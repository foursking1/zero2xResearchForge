"""
Numba-JIT bispectrum descriptor calculator.

Replicates MALA's pure-python Bispectrum.__calculate_python() algorithm exactly,
but JIT-compiles the expensive per-atom 506-step recurrence in __compute_ui with
numba. The recurrence for each atom is independent (only depends on that atom's
a_r/a_i/b_r/b_i), so processing atoms serially in a compiled loop is bit-identical
to MALA's vectorized-over-atoms loop (same per-atom floating point order).

The compute_zi and compute_bi steps are also JIT-compiled / vectorized.
"""
import numpy as np
from numba import njit, prange


@njit(cache=True, parallel=True)
def _ui_rows(flat_atoms, flat_grid, flat_distances, cutoff,
             u_full_pos, index_u_full, index_u1_full, rootpq_full_1, rootpq_full_2,
             sym_pos_pos, index_u1_symmetry_pos, index_u_symmetry_pos,
             sym_neg_pos, index_u1_symmetry_neg, index_u_symmetry_neg,
             u_max):
    """
    Compute per-atom ulist real/imag arrays.

    Parameters
    ----------
    flat_* : (nr_total, 3) / (nr_total,) arrays of concatenated neighbor atoms,
        grid points and distances for a batch.
    Returns
    -------
    ulist_r, ulist_i : (nr_total, u_max) float64 arrays
    """
    nr = flat_atoms.shape[0]
    rmin0 = 0.0
    rfac0 = 0.99363

    theta0 = (flat_distances - rmin0) * rfac0 * np.pi / (cutoff - rmin0)
    z0 = flat_distances / np.tan(theta0)
    r0inv = 1.0 / np.sqrt(flat_distances * flat_distances + z0 * z0)
    dv = -1.0 * (flat_atoms - flat_grid)
    a_r = r0inv * z0
    a_i = -r0inv * dv[:, 2]
    b_r = r0inv * dv[:, 1]
    b_i = -r0inv * dv[:, 0]

    ulist_r = np.zeros((nr, u_max), dtype=np.float64)
    ulist_i = np.zeros((nr, u_max), dtype=np.float64)
    ulist_r[:, 0] = 1.0

    for i in prange(nr):
        ar = a_r[i]; ai = a_i[i]; br = b_r[i]; bi = b_i[i]
        ur = ulist_r[i]
        ui = ulist_i[i]
        for jju_outer in range(u_max):
            k = u_full_pos[jju_outer]
            if k >= 0:
                cur = index_u_full[k]
                prv = index_u1_full[k]
                r1 = rootpq_full_1[k]
                r2 = rootpq_full_2[k]
                # a-recurrence (in-place +=)
                ur[cur] += r1 * (ar * ur[prv] + ai * ui[prv])
                ui[cur] += r1 * (ar * ui[prv] - ai * ur[prv])
                # b-recurrence (assignment to cur+1)
                ur[cur + 1] = -r2 * (br * ur[prv] + bi * ui[prv])
                ui[cur + 1] = -r2 * (br * ui[prv] - bi * ur[prv])
            k = sym_pos_pos[jju_outer]
            if k >= 0:
                ur[index_u1_symmetry_pos[k]] = ur[index_u_symmetry_pos[k]]
                ui[index_u1_symmetry_pos[k]] = -ui[index_u_symmetry_pos[k]]
            k = sym_neg_pos[jju_outer]
            if k >= 0:
                ur[index_u1_symmetry_neg[k]] = -ur[index_u_symmetry_neg[k]]
                ui[index_u1_symmetry_neg[k]] = ui[index_u_symmetry_neg[k]]
    return ulist_r, ulist_i


@njit(cache=True, parallel=True)
def _zi_rows(ulisttot_r, ulisttot_i, icgb, icga, u1r, u1i, u2r, u2i, cglist,
             idx_z_jjz, n_z):
    """Compute zi for a batch of grid points. (B, u_max) -> (B, n_z)."""
    B = ulisttot_r.shape[0]
    L = len(idx_z_jjz)
    zlist_r = np.zeros((B, n_z), dtype=np.float64)
    zlist_i = np.zeros((B, n_z), dtype=np.float64)
    for b in prange(B):
        ur = ulisttot_r[b]
        ui = ulisttot_i[b]
        zr_row = zlist_r[b]
        zi_row = zlist_i[b]
        for k in range(L):
            cg = cglist[icgb[k]] * cglist[icga[k]]
            r1 = ur[u1r[k]]
            i1 = ui[u1i[k]]
            r2 = ur[u2r[k]]
            i2 = ui[u2i[k]]
            zr_row[idx_z_jjz[k]] += cg * (r1 * r2 - i1 * i2)
            zi_row[idx_z_jjz[k]] += cg * (r1 * i2 + i1 * r2)
    return zlist_r, zlist_i


@njit(cache=True)
def _bi_rows(ulisttot_r, ulisttot_i, zlist_r, zlist_i,
             bi_start_jju, bi_start_jjz, bi_n_pairs, bi_has_half, n_b):
    """Compute bispectrum blist for a batch. (B, feature_size-3)."""
    B = ulisttot_r.shape[0]
    blist = np.zeros((B, n_b), dtype=np.float64)
    for jjb in range(n_b):
        s_jju = bi_start_jju[jjb]
        s_jjz = bi_start_jjz[jjb]
        n = bi_n_pairs[jjb]
        for b in range(B):
            ur = ulisttot_r[b]
            ui = ulisttot_i[b]
            zr = zlist_r[b]
            zi = zlist_i[b]
            s = 0.0
            for p in range(n):
                s += ur[s_jju + p] * zr[s_jjz + p] + ui[s_jju + p] * zi[s_jjz + p]
            if bi_has_half[jjb]:
                s += 0.5 * (ur[s_jju + n] * zr[s_jjz + n]
                            + ui[s_jju + n] * zi[s_jjz + n])
            blist[b, jjb] = 2.0 * s
    return blist


def prepare_bispectrum(params, atoms, grid):
    """Build a configured Bispectrum object (see batched_bispectrum.prepare_bispectrum)."""
    from batched_bispectrum import prepare_bispectrum as _pb
    return _pb(params, atoms, grid)


def calculate_bispectrum_numba(dc, atoms, grid, batch_size=256):
    """
    Compute bispectrum descriptors for `atoms` on `grid` using numba-JIT cores.

    Neighbor search uses a scipy cKDTree (built once per atom set) instead of a
    full O(B * N_all) cdist, and the flat per-neighbor arrays are assembled
    with vectorized numpy (np.repeat / np.lexsort) instead of per-point Python
    loops.  The 506-step ulist recurrence is still the numba-JIT core, so the
    output is bit-identical to the previous cdist path (same neighbor set and
    per-point ascending atom-index ordering) up to ~1e-16 floating point.

    Returns array of shape (nx, ny, nz, feature_size) with xyz prepended.
    """
    from batched_bispectrum import prepare_config
    from scipy.spatial import cKDTree
    cfg = prepare_config(dc)
    all_atoms = dc._setup_atom_list()
    nx, ny, nz = grid
    out = np.zeros((nx, ny, nz, cfg["feature_size"]), dtype=np.float64)

    xs = np.arange(nx); ys = np.arange(ny); zs = np.arange(nz)
    gx, gy, gz = np.meshgrid(xs, ys, zs, indexing="ij")
    flat_xyz = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], axis=1)

    # Vectorized grid-index -> real-coordinate conversion (triclinic + orthorhombic)
    cell = dc._atoms.cell
    gd = np.array(grid, dtype=np.float64)
    npts_all = len(flat_xyz)
    if cell.orthorhombic:
        all_coords = flat_xyz.astype(np.float64) * np.diag(dc._voxel)
    else:
        i = flat_xyz[:, 0].astype(np.float64)
        j = flat_xyz[:, 1].astype(np.float64)
        k = flat_xyz[:, 2].astype(np.float64)
        all_coords = np.zeros((npts_all, 3), dtype=np.float64)
        all_coords[:, 0] = i/gd[0]*cell[0, 0] + j/gd[1]*cell[1, 0] + k/gd[2]*cell[2, 0]
        all_coords[:, 1] = j/gd[1]*cell[1, 1] + k/gd[2]*cell[1, 2]
        all_coords[:, 2] = k/gd[2]*cell[2, 2]

    tree = cKDTree(all_atoms)
    cutoff = cfg["bispectrum_cutoff"]

    for start in range(0, npts_all, batch_size):
        chunk = flat_xyz[start:start + batch_size]
        coords = all_coords[start:start + batch_size]
        B = len(chunk)

        idx_list = tree.query_ball_point(coords, r=cutoff, workers=1)
        counts = np.array([len(v) for v in idx_list], dtype=np.int64)
        boundaries = np.concatenate([[0], np.cumsum(counts)]).astype(np.int64)
        total = int(boundaries[-1])
        flat_atoms = np.zeros((total, 3), dtype=np.float64)
        flat_grid = np.zeros((total, 3), dtype=np.float64)
        flat_dists = np.zeros(total, dtype=np.float64)
        if total > 0:
            flat_idx = np.concatenate(idx_list)
            # Sort within each grid point's segment to preserve ascending
            # atom-index order (deterministic, matches the cdist path ordering).
            pt_ids = np.repeat(np.arange(B), counts)
            order = np.lexsort((flat_idx, pt_ids))
            flat_idx = flat_idx[order]
            flat_atoms[:] = all_atoms[flat_idx]
            flat_grid[:] = np.repeat(coords, counts, axis=0)
            dv = flat_atoms - flat_grid
            flat_dists[:] = np.sqrt((dv*dv).sum(axis=1))

        ur, ui = _ui_rows(
            flat_atoms, flat_grid, flat_dists, cfg["bispectrum_cutoff"],
            cfg["u_full_pos"], cfg["index_u_full"], cfg["index_u1_full"],
            cfg["rootpq_full_1"], cfg["rootpq_full_2"],
            cfg["sym_pos_pos"], cfg["index_u1_symmetry_pos"], cfg["index_u_symmetry_pos"],
            cfg["sym_neg_pos"], cfg["index_u1_symmetry_neg"], cfg["index_u_symmetry_neg"],
            cfg["u_max"],
        )
        # Reduce per grid point
        ulisttot_r = np.zeros((B, cfg["u_max"]), dtype=np.float64)
        ulisttot_i = np.zeros((B, cfg["u_max"]), dtype=np.float64)
        if total > 0:
            segsum_r = np.add.reduceat(ur, boundaries[:-1], axis=0)
            segsum_i = np.add.reduceat(ui, boundaries[:-1], axis=0)
            ulisttot_r += segsum_r
            ulisttot_i += segsum_i
        ulisttot_r[:, cfg["index_u_one_initialized"]] += 1.0

        zr, zi = _zi_rows(ulisttot_r, ulisttot_i, cfg["index_z_icgb"],
                          cfg["index_z_icga"], cfg["index_z_u1r"], cfg["index_z_u1i"],
                          cfg["index_z_u2r"], cfg["index_z_u2i"], cfg["cglist"],
                          cfg["index_z_jjz"], cfg["idxz_max"])
        blist = _bi_rows(ulisttot_r, ulisttot_i, zr, zi,
                         cfg["bi_start_jju"], cfg["bi_start_jjz"], cfg["bi_n_pairs"],
                         cfg["bi_has_half"], cfg["index_b_max"])
        xx = chunk[:, 0]; yy = chunk[:, 1]; zz = chunk[:, 2]
        out[xx, yy, zz, 0:3] = coords
        out[xx, yy, zz, 3:] = blist
    return out
