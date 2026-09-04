"""Neighbor lists with periodic boundary conditions (minimum-image over image
shifts in [-2, 2]^3) and Behler-Parrinello style descriptors with *analytic*
derivatives w.r.t. atomic positions. Single-element (pure) systems only.

Descriptor layout (D features per atom):
  0..5     G2     : sum_j fc(r_ij)*exp(-eta_m r_ij^2)               (6 widths)
  6..12    shell  : sum_j fc(r_ij)*exp(-((r_ij - s_m)/sig)^2)       (7 shells)
  13..14   angular: sum_{j<k} w_a(r_ij) w_a(r_ik) cos(theta_jik)    (2 widths)

The gradient machinery exposes, for any energy model whose per-atom energy is
w_i . g_i with per-atom weight vectors w_i (N,D), the exact force F = -dE/dr.
"""
import numpy as np

RC = 5.0                        # cutoff (Angstrom)
G2_ETA = np.array([0.2, 0.5, 1.0, 2.0, 4.0, 8.0], dtype=float)
SHELL_S = np.array([1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5], dtype=float)
SHELL_SIG = 0.35
ANG_RS = np.array([0.0, 2.4], dtype=float)     # gaussian window center (0 -> plain fc)
ANG_SIG = 0.5
K_ANG = 12                       # (kept for API compatibility; unused)

NR = len(G2_ETA) + len(SHELL_S)   # number of radial features
NA = len(ANG_RS)
D = NR + NA


def cosine_cutoff(r, rc=RC):
    r = np.asarray(r, dtype=float)
    return np.where(r < rc, 0.5 * (np.cos(np.pi * r / rc) + 1.0), 0.0)


def dcosine_cutoff(r, rc=RC):
    r = np.asarray(r, dtype=float)
    return np.where(r < rc, -0.5 * (np.pi / rc) * np.sin(np.pi * r / rc), 0.0)


def neighbor_pairs(lat, cart):
    """Return (i, j, u, d): directed neighbour pairs over *all* periodic
    images within RC (not just the nearest image). Each image of every pair
    (i,j) contributes one (i,j) directed entry and one mirror (j,i) entry,
    so that in small (super)cells all neighbours inside the cutoff are
    represented (min-image would wrongly merge distinct images)."""
    cart = np.asarray(cart, dtype=float)
    N = len(cart)
    lat = np.asarray(lat, dtype=float)
    Linv = np.linalg.inv(lat)
    frac = cart @ Linv
    # how many integer repeats per axis are needed to cover RC
    row_norms = np.linalg.norm(lat, axis=1)
    S = int(np.ceil(RC / max(row_norms.min(), 1e-9))) + 1
    shifts = []
    for ix in range(-S, S + 1):
        for iy in range(-S, S + 1):
            for iz in range(-S, S + 1):
                shifts.append((ix, iy, iz))
    shifts = np.asarray(shifts, dtype=float)
    iu = np.triu_indices(N, k=1)
    iA, jA = iu
    dfrac = frac[jA] - frac[iA]
    # total: (n_pairs_unordered * n_shifts)
    dcart = dfrac[:, None, :] + shifts[None, :, :]
    dcart = dcart @ lat                          # (P, S3, 3)
    dist = np.sqrt(np.einsum("pse,pse->ps", dcart, dcart))
    sel = dist < RC
    repeat_i = np.repeat(iA, len(shifts))
    repeat_j = np.repeat(jA, len(shifts))
    flat_dcart = dcart.reshape(-1, 3)
    flat_dist = dist.ravel()
    i_pairs = repeat_i[sel.ravel()]
    j_pairs = repeat_j[sel.ravel()]
    d = flat_dist[sel.ravel()]
    best = flat_dcart[sel.ravel()]
    u = best / d[:, None]
    # add mirror entries (j,i)
    i_all = np.concatenate([i_pairs, j_pairs])
    j_all = np.concatenate([j_pairs, i_pairs])
    u_all = np.vstack([u, -u])
    d_all = np.concatenate([d, d])
    return i_all, j_all, u_all, d_all


def angular_triples_full(i_arr, j_arr, u, d, N):
    """Enumerate ALL triplet terms of the angular descriptor.

    The angular feature of atom i is the sum over *every* ordered pair of
    neighbour images (j,u_j),(k,u_k) within the cutoff of
        w(r_ij) w(r_ik) cos(triangle at i)
    (never a nearest-image/K selection, so the feature is an analytic, smooth
    function of the atomic coordinates). Every periodic image is its own term.

    Returns (i, j, k, rj, rk, co, uj, uk) where j, k are atom indices and
    uj, uk the (image-specific) unit vectors."""
    order = np.lexsort((d, i_arr))
    i_s, j_s, u_s, d_s = i_arr[order], j_arr[order], u[order], d[order]
    ui, starts = np.unique(i_s, return_index=True)
    ends = np.append(starts[1:], len(i_s))
    outs = [[] for _ in range(8)]
    for ai, (s0, e0) in enumerate(zip(starts, ends)):
        seg_j, seg_u, seg_d = j_s[s0:e0], u_s[s0:e0], d_s[s0:e0]
        nn = len(seg_j)
        if nn < 2:
            continue
        # unordered entry pairs
        p, q = np.triu_indices(nn, k=1)
        jg = seg_j[p]
        kg = seg_j[q]
        u1g, u2g = seg_u[p], seg_u[q]
        r1g, r2g = seg_d[p], seg_d[q]
        co = np.einsum("ij,ij->i", u1g, u2g)
        iid = ui[ai]
        outs[0].append(np.full(len(jg), iid))
        outs[1].append(jg)
        outs[2].append(kg)
        outs[3].append(r1g)
        outs[4].append(r2g)
        outs[5].append(co)
        outs[6].append(u1g)
        outs[7].append(u2g)
    if not outs[0]:
        return None
    return tuple(np.concatenate(o) for o in outs)


def compute_pair_features(pairs_info):
    """Return (R, dR) arrays for all radial features over the pair list."""
    i_arr, j_arr, u, d = pairs_info
    fc = cosine_cutoff(d)
    dfc = dcosine_cutoff(d)
    g2 = np.exp(-d[:, None] ** 2 * G2_ETA[None, :])
    dg2 = (-2 * d[:, None] * G2_ETA[None, :]) * g2
    sh = np.exp(-((d[:, None] - SHELL_S[None, :]) / SHELL_SIG) ** 2)
    dsh = (-2 * (d[:, None] - SHELL_S[None, :]) / SHELL_SIG ** 2) * sh
    R = np.hstack([fc[:, None] * g2, fc[:, None] * sh])
    dR = np.hstack([dfc[:, None] * g2 + fc[:, None] * dg2,
                    dfc[:, None] * sh + fc[:, None] * dsh])
    return R, dR


def compute_descriptors(cart, lat):
    """Compute descriptor matrix G (N,D) and pair/triple info for a config."""
    i_arr, j_arr, u, d = neighbor_pairs(lat, cart)
    N = len(cart)
    R, _ = compute_pair_features((i_arr, j_arr, u, d))
    G = np.zeros((N, D))
    np.add.at(G[:, :R.shape[1]], i_arr, R)
    t = angular_triples_full(i_arr, j_arr, u, d, N)
    if t is not None:
        ti, tj, tk, rj, rk, co, uj, uk = t
        for a, rs in enumerate(ANG_RS):
            wja = angular_w(rj, rs)
            wka = angular_w(rk, rs)
            contrib = wja * wka * co
            np.add.at(G[:, NR + a], ti, contrib)
    return G, (i_arr, j_arr, u, d), t


def angular_w(r, rs, sig=ANG_SIG):
    fc = cosine_cutoff(r)
    if rs > 0:
        return fc * np.exp(-((r - rs) / sig) ** 2)
    return fc


def dw_angular(r, rs, sig=ANG_SIG):
    fc = cosine_cutoff(r)
    dfc = dcosine_cutoff(r)
    if rs > 0:
        g = np.exp(-((r - rs) / sig) ** 2)
        return dfc * g + fc * g * (-2 * (r - rs) / sig ** 2)
    return dfc


def dE_dr_radial(pairs_info, coeffs):
    """Gradient of sum_i coeffs[i].g_i w.r.t. positions (radial part).

    E = sum_directed (i->j) coeffs[i].R(r_ij). The derivative of each
    directed pair term is handled independently with its own image vector:
      dE/dr_i += -coeffs[i] R'(r) u_ij ;  dE/dr_j += +coeffs[i] R'(r) u_ij
    (mirror entries (j,i) reappear in the list with their own vector and
    their own coefficient, so nothing is double counted or assumed)."""
    R, dR = compute_pair_features(pairs_info)
    i_arr, j_arr, u, d = pairs_info
    N = coeffs.shape[0]
    wsrc = coeffs[i_arr, :NR]
    s = np.einsum("nd,nd->n", wsrc, dR)
    G = np.zeros((N, 3))
    np.add.at(G, i_arr, -s[:, None] * u)
    np.add.at(G, j_arr, +s[:, None] * u)
    return G, R


def energy_radial(pairs_info, coeffs, R=None):
    if R is None:
        R, _ = compute_pair_features(pairs_info)
    i_arr = pairs_info[0]
    gsum = np.zeros((coeffs.shape[0], R.shape[1]))
    np.add.at(gsum, i_arr, R)
    return float(np.einsum("nd,nd->", coeffs[:, :R.shape[1]], gsum))


def dE_dr_angular(triples_data, coeffs):
    if triples_data is None:
        return np.zeros((coeffs.shape[0], 3)), 0.0
    i_arr, j_arr, k_arr, rj, rk, co, uj, uk = triples_data
    N = coeffs.shape[0]
    G = np.zeros((N, 3))
    E = 0.0
    for a, rs in enumerate(ANG_RS):
        wj = angular_w(rj, rs)
        wk = angular_w(rk, rs)
        dwj = dw_angular(rj, rs)
        dwk = dw_angular(rk, rs)
        wc = coeffs[i_arr, NR + a]
        E += float(np.sum(wc * wj * wk * co))
        M1 = (uk - uj * co[:, None]) / rj[:, None]
        M2 = (uj - uk * co[:, None]) / rk[:, None]
        gi = (-dwj * wk * co)[:, None] * uj - (wj * dwk * co)[:, None] * uk - (wj * wk)[:, None] * (M1 + M2)
        gj = (dwj * wk * co)[:, None] * uj + (wj * wk)[:, None] * M1
        gk = (wj * dwk * co)[:, None] * uk + (wj * wk)[:, None] * M2
        np.add.at(G, i_arr, wc[:, None] * gi)
        np.add.at(G, j_arr, wc[:, None] * gj)
        np.add.at(G, k_arr, wc[:, None] * gk)
    return G, E


def energy_and_force_from_weights(pairs_info, triples_data, coeffs):
    """coeffs: (N,D) per-atom descriptor weights (w_i . g_i per atom).
    Returns (E, F) with F = -dE/dr (energy-conserving)."""
    G, _ = dE_dr_radial(pairs_info, coeffs)
    E = energy_radial(pairs_info, coeffs)
    if triples_data is not None:
        Ga, Ea = dE_dr_angular(triples_data, coeffs)
        E += Ea
        G = G + Ga
    return E, -G