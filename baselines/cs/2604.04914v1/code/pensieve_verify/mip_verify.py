"""MIP verification backend (HiGHS via scipy.optimize.milp).

Encodes the comparative ReLU network and the query's argmax constraints as a
mixed-integer linear feasibility problem.  Feasible  ->  unsafe (certified
counterexample);  infeasible  ->  safe (certified for the box);  solver timeout
or numerical failure  ->  unknown.
"""

from __future__ import annotations

import time

import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy import sparse

from .verify import CompNet, ibp_bounds, reduce_net_for_box
from .queries import Query


def verify_mip(net: CompNet, query: Query, timeout_s: float = 120.0) -> dict:
    """Run MIP feasibility for a query.  Returns status / detail dict."""
    t0 = time.perf_counter()
    rnet, rlo, rhi = reduce_net_for_box(net, query.lower, query.upper)
    n_in = rnet.n_in
    pre = ibp_bounds(rnet, rlo, rhi)  # pre[k+1] = pre-activation bounds of layer k

    # ---- variable layout ----
    layers = []   # per-layer bookkeeping
    cur = n_in
    n_bin = 0
    for k in range(len(rnet.Ws)):
        m = rnet.Ws[k].shape[0]
        is_relu = rnet.relu[k]
        mask = rnet.masks[k]
        zlo, zhi = pre[k + 1]
        if is_relu:
            if mask is None:
                unstable = (zlo < 0) & (zhi > 0)
            else:
                unstable = mask & (zlo < 0) & (zhi > 0)
            n_unstable = int(unstable.sum())
            z_base, h_base, bin_base = cur, cur + m, cur + 2 * m
            layers.append({
                "k": k, "z": z_base, "h": h_base, "bin": bin_base,
                "n_bin": n_unstable, "unstable": unstable, "m": m,
                "bin_of_row": None, "mask": mask,
            })
            # binary index per neuron row
            row_bin = np.full(m, -1, dtype=np.int64)
            b = 0
            for i in range(m):
                if unstable[i]:
                    row_bin[i] = b
                    b += 1
            layers[-1]["bin_of_row"] = row_bin
            cur = bin_base + n_unstable
            n_bin += n_unstable
        else:
            layers.append({"k": k, "z": cur, "h": None, "bin": None,
                           "n_bin": 0, "unstable": None, "m": m, "bin_of_row": None})
            cur += m
    n_var = cur

    # Constraint matrix is built sparse: the z-affine rows have ~n_in..m_prev
    # nonzeros and the ReLU rows have 2-3, so a dense (n_rows x n_var) array
    # would blow up memory for the mid/big models (14468 x 10656 -> 1.15 GB).
    rows = []      # list of (indices, values) sparse rows
    lo_vec = []
    hi_vec = []

    def add(coeff_dict, lo, hi):
        nz = np.nonzero(coeff_dict)[0]
        rows.append((nz, coeff_dict[nz]))
        lo_vec.append(lo)
        hi_vec.append(hi)

    def add_eq(coeff_dict, rhs):
        add(coeff_dict, rhs, rhs)

    # input bounds
    input_lb = np.full(n_var, -np.inf)
    input_ub = np.full(n_var, np.inf)
    input_lb[:n_in] = rlo
    input_ub[:n_in] = rhi
    for L in layers:
        if L["bin"] is not None and L["n_bin"] > 0:
            input_lb[L["bin"]: L["bin"] + L["n_bin"]] = 0.0
            input_ub[L["bin"]: L["bin"] + L["n_bin"]] = 1.0

    for L in layers:
        k = L["k"]
        W = rnet.Ws[k]
        b = rnet.bs[k]
        m = L["m"]
        zlo, zhi = pre[k + 1]
        if k == 0:
            h_prev = np.arange(n_in)
        else:
            pL = layers[k - 1]
            h_prev = np.arange(pL["h"], pL["h"] + pL["m"])

        # z_k = W h_prev + b
        for i in range(m):
            c_arr = np.zeros(n_var)
            c_arr[L["z"] + i] = 1.0
            c_arr[h_prev] -= W[i]
            add_eq(c_arr, b[i])
        # n.b.: for the masked first layer, rows with mask=False have h = z, which
        # the ReLU branch below encodes as 'stable' via IBP (they never get binaries).

        if L["h"] is None:
            continue

        # ReLU constraints
        row_bin = L["bin_of_row"]
        for i in range(m):
            li, ui = zlo[i], zhi[i]
            if L["mask"] is not None and not L["mask"][i]:
                # identity row (no ReLU applied)
                c = np.zeros(n_var)
                c[L["h"] + i] = 1.0
                c[L["z"] + i] = -1.0
                add_eq(c, 0.0)
            elif L["unstable"][i]:
                bi = L["bin"] + row_bin[i]
                c = np.zeros(n_var)
                c[L["h"] + i] = 1.0
                c[L["z"] + i] = -1.0
                add(c, 0.0, np.inf)           # h >= z
                c = np.zeros(n_var)
                c[L["h"] + i] = 1.0
                add(c, 0.0, np.inf)           # h >= 0
                c = np.zeros(n_var)
                c[L["h"] + i] = 1.0
                c[bi] = -ui
                add(c, -np.inf, 0.0)          # h <= u*d
                c = np.zeros(n_var)
                c[L["h"] + i] = 1.0
                c[L["z"] + i] = -1.0
                c[bi] = -li
                add(c, -np.inf, -li)          # h - z - l*d <= -l  (== h <= z - l(1-d))
            elif li >= 0.0:
                c = np.zeros(n_var)
                c[L["h"] + i] = 1.0
                c[L["z"] + i] = -1.0
                add_eq(c, 0.0)                # h = z
            else:  # u <= 0
                c = np.zeros(n_var)
                c[L["h"] + i] = 1.0
                add_eq(c, 0.0)                # h = 0

    # query output constraints: y[lhs] - y[rhs] <= 0
    out_layer = layers[-1]
    y_base = out_layer["z"]
    for lhs, rhs in query.pairs:
        c = np.zeros(n_var)
        c[y_base + lhs] = 1.0
        c[y_base + rhs] = -1.0
        add(c, -np.inf, 0.0)

    lb = np.array(lo_vec)
    ub = np.array(hi_vec)
    if rows:
        data, col, row_idx = [], [], []
        for r, (idx, val) in enumerate(rows):
            row_idx.extend([r] * idx.size)
            col.extend(idx.tolist())
            data.extend(val.tolist())
        A = sparse.csr_matrix((data, (row_idx, col)), shape=(len(rows), n_var))
    else:
        A = sparse.csr_matrix((0, n_var))

    integrality = np.zeros(n_var, dtype=np.uint8)
    for L in layers:
        if L["bin"] is not None and L["n_bin"] > 0:
            integrality[L["bin"]: L["bin"] + L["n_bin"]] = 1

    t_start = time.perf_counter()
    try:
        res = milp(
            c=np.zeros(n_var),
            integrality=integrality,
            bounds=Bounds(lb=input_lb, ub=input_ub),
            constraints=LinearConstraint(A, lb, ub),
            options={"time_limit": timeout_s, "disp": False},
        )
    except Exception as exc:  # solver failure -> unknown
        return {
            "backend": "mip", "status": "unknown", "time_s": time.perf_counter() - t_start,
            "n_var": n_var, "n_bin": n_bin, "solver_msg": f"exception: {exc}", "witness": None,
            "input_dim_red": n_in,
        }
    elapsed = time.perf_counter() - t_start

    witness = None
    if res.success:
        status = "unsafe"
        witness = res.x[:n_in].tolist()
    elif res.status == 2:
        status = "safe"
    else:
        status = "unknown"

    return {
        "backend": "mip",
        "status": status,
        "time_s": elapsed,
        "n_var": int(n_var),
        "n_bin": int(n_bin),
        "solver_msg": getattr(res, "message", ""),
        "witness": witness,
        "input_dim_red": n_in,
    }
