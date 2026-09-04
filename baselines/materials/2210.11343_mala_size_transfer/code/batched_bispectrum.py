"""
Batched single-process bispectrum descriptor calculator.

Replicates MALA's pure-python Bispectrum.__calculate_python() algorithm
exactly, but batches the per-grid-point loop so the expensive 506-step
recurrence in compute_ui is paid once per BATCH of grid points instead of
once per grid point. This gives a large speedup in a single process, avoiding
multiprocessing overhead (which is high on Windows and under CPU contention).

The per-atom math is identical to MALA's implementation (verified to match
bit-for-bit; see test_batched_bispectrum.py).
"""
import numpy as np
from scipy.spatial import distance


def _compute_ui_batched(batch_ij_arrays, cfg):
    """
    Compute ui for a batch of grid points.

    Parameters
    ----------
    batch_ij_arrays : tuple
        (flat_atoms, flat_grid, flat_distances, boundaries) where
        flat_* are the concatenated per-atom quantities over all grid points
        in the batch, and boundaries are the segment starts for each grid point.
    cfg : dict
        Precomputed index arrays and parameters.

    Returns
    -------
    ulisttot_r, ulisttot_i : numpy.ndarray
        Shape (B, index_u_max).
    """
    (flat_atoms, flat_grid, flat_distances, boundaries) = batch_ij_arrays
    n_batch = len(boundaries)
    u_max = cfg["u_max"]
    rmin0 = 0.0
    rfac0 = 0.99363
    cutoff = cfg["bispectrum_cutoff"]

    theta0 = (
        (flat_distances - rmin0) * rfac0 * np.pi / (cutoff - rmin0)
    )
    z0 = np.squeeze(flat_distances / np.tan(theta0))

    nr_total = len(flat_distances)
    ulist_r_ij = np.zeros((nr_total, u_max), dtype=np.float64)
    ulist_i_ij = np.zeros((nr_total, u_max), dtype=np.float64)
    ulist_r_ij[:, 0] = 1.0

    r0inv = np.squeeze(
        1.0 / np.sqrt(flat_distances * flat_distances + z0 * z0)
    )
    distance_vector = -1.0 * (flat_atoms - flat_grid)

    a_r = r0inv * z0
    a_i = -r0inv * distance_vector[:, 2]
    b_r = r0inv * distance_vector[:, 1]
    b_i = -r0inv * distance_vector[:, 0]

    iuf = cfg["index_u_full"]
    iu1f = cfg["index_u1_full"]
    rpq1 = cfg["rootpq_full_1"]
    rpq2 = cfg["rootpq_full_2"]
    u_full_pos = cfg["u_full_pos"]   # for each jju_outer: index into index_u_full or -1
    sym_pos_pos = cfg["sym_pos_pos"]
    sym_neg_pos = cfg["sym_neg_pos"]
    isym_pos = cfg["index_u_symmetry_pos"]
    isym_neg = cfg["index_u_symmetry_neg"]
    is1p = cfg["index_u1_symmetry_pos"]
    is1n = cfg["index_u1_symmetry_neg"]

    for jju_outer in range(u_max):
        k = u_full_pos[jju_outer]
        if k >= 0:
            cur = iuf[k]
            prv = iu1f[k]
            r1 = rpq1[k]
            r2 = rpq2[k]
            # a-recurrence (in-place +=)
            ulist_r_ij[:, cur] += r1 * (a_r * ulist_r_ij[:, prv]
                                        + a_i * ulist_i_ij[:, prv])
            ulist_i_ij[:, cur] += r1 * (a_r * ulist_i_ij[:, prv]
                                        - a_i * ulist_r_ij[:, prv])
            # b-recurrence (assignment to cur+1)
            ulist_r_ij[:, cur + 1] = -r2 * (b_r * ulist_r_ij[:, prv]
                                            + b_i * ulist_i_ij[:, prv])
            ulist_i_ij[:, cur + 1] = -r2 * (b_r * ulist_i_ij[:, prv]
                                            - b_i * ulist_r_ij[:, prv])
        k = sym_pos_pos[jju_outer]
        if k >= 0:
            ulist_r_ij[:, is1p[k]] = ulist_r_ij[:, isym_pos[k]]
            ulist_i_ij[:, is1p[k]] = -ulist_i_ij[:, isym_pos[k]]
        k = sym_neg_pos[jju_outer]
        if k >= 0:
            ulist_r_ij[:, is1n[k]] = -ulist_r_ij[:, isym_neg[k]]
            ulist_i_ij[:, is1n[k]] = ulist_i_ij[:, isym_neg[k]]

    # sfac (switchflag == 0 -> hard cutoff -> sfac = 1)
    sfac = np.ones(nr_total, dtype=np.float64)

    # Reduce per grid point (segments are non-empty; grid point ids via boundaries)
    contrib_r = sfac[:, None] * ulist_r_ij
    contrib_i = sfac[:, None] * ulist_i_ij
    segsum_r = np.add.reduceat(contrib_r, boundaries, axis=0)
    segsum_i = np.add.reduceat(contrib_i, boundaries, axis=0)

    ulisttot_r = np.zeros((n_batch, u_max), dtype=np.float64)
    ulisttot_i = np.zeros((n_batch, u_max), dtype=np.float64)
    ulisttot_r[:, cfg["index_u_one_initialized"]] = 1.0
    ulisttot_r += segsum_r
    ulisttot_i += segsum_i
    return ulisttot_r, ulisttot_i


def _compute_zi_batched(ulisttot_r, ulisttot_i, cfg):
    """Compute zi for a batch of grid points. Shapes (B, index_u_max) -> (B, idxz_max)."""
    icgb = cfg["index_z_icgb"]
    icga = cfg["index_z_icga"]
    u1r = cfg["index_z_u1r"]
    u1i = cfg["index_z_u1i"]
    u2r = cfg["index_z_u2r"]
    u2i = cfg["index_z_u2i"]
    cglist = cfg["cglist"]
    zi_boundaries = cfg["zi_boundaries"]  # segment starts, index_z_jjz sorted

    cg_prod = cglist[icgb] * cglist[icga]
    tmp_real = cg_prod * (
        ulisttot_r[:, u1r] * ulisttot_r[:, u2r]
        - ulisttot_i[:, u1i] * ulisttot_i[:, u2i]
    )
    tmp_imag = cg_prod * (
        ulisttot_r[:, u1r] * ulisttot_i[:, u2i]
        + ulisttot_i[:, u1i] * ulisttot_r[:, u2r]
    )
    zlist_r = np.add.reduceat(tmp_real, zi_boundaries, axis=1)
    zlist_i = np.add.reduceat(tmp_imag, zi_boundaries, axis=1)
    return zlist_r, zlist_i


def _compute_bi_batched(ulisttot_r, ulisttot_i, zlist_r, zlist_i, cfg):
    """Compute bispectrum descriptors for a batch. Shapes (B, feature_size)."""
    B = ulisttot_r.shape[0]
    n_b = cfg["index_b_max"]
    blist = np.zeros((B, n_b), dtype=np.float64)
    u_max = cfg["u_max"]

    start_jju = cfg["bi_start_jju"]
    start_jjz = cfg["bi_start_jjz"]
    n_pairs = cfg["bi_n_pairs"]
    has_half = cfg["bi_has_half"]

    for jjb in range(n_b):
        s_jju = start_jju[jjb]
        s_jjz = start_jjz[jjb]
        n = n_pairs[jjb]
        if n > 0:
            jju_seq = s_jju + np.arange(n, dtype=np.int64)
            jjz_seq = s_jjz + np.arange(n, dtype=np.int64)
            blist[:, jjb] = np.sum(
                ulisttot_r[:, jju_seq] * zlist_r[:, jjz_seq]
                + ulisttot_i[:, jju_seq] * zlist_i[:, jjz_seq],
                axis=1,
            )
        if has_half[jjb]:
            jju = s_jju + n
            jjz = s_jjz + n
            blist[:, jjb] += 0.5 * (
                ulisttot_r[:, jju] * zlist_r[:, jjz]
                + ulisttot_i[:, jju] * zlist_i[:, jjz]
            )
    blist *= 2.0

    # Assemble into feature vector with xyz prepended
    out = np.zeros((B, cfg["feature_size"]), dtype=np.float64)
    out[:, 3:] = blist
    return out


def prepare_config(params):
    """
    Build the config dict of index arrays from a configured Bispectrum object.

    Call after dc._Bispectrum__init_index_arrays() has been run.
    """
    dc = params  # actually the Bispectrum instance
    u_max = dc._Bispectrum__index_u_max
    cfg = {
        "u_max": u_max,
        "index_u_full": np.asarray(dc._Bispectrum__index_u_full, dtype=np.int64),
        "index_u1_full": np.asarray(dc._Bispectrum__index_u1_full, dtype=np.int64),
        "rootpq_full_1": np.asarray(dc._Bispectrum__rootpq_full_1, dtype=np.float64),
        "rootpq_full_2": np.asarray(dc._Bispectrum__rootpq_full_2, dtype=np.float64),
        "index_u_symmetry_pos": np.asarray(dc._Bispectrum__index_u_symmetry_pos, dtype=np.int64),
        "index_u_symmetry_neg": np.asarray(dc._Bispectrum__index_u_symmetry_neg, dtype=np.int64),
        "index_u1_symmetry_pos": np.asarray(dc._Bispectrum__index_u1_symmetry_pos, dtype=np.int64),
        "index_u1_symmetry_neg": np.asarray(dc._Bispectrum__index_u1_symmetry_neg, dtype=np.int64),
        "index_u_one_initialized": np.asarray(dc._Bispectrum__index_u_one_initialized, dtype=np.int64),
        "index_z_icgb": np.asarray(dc._Bispectrum__index_z_icgb, dtype=np.int64),
        "index_z_icga": np.asarray(dc._Bispectrum__index_z_icga, dtype=np.int64),
        "index_z_u1r": np.asarray(dc._Bispectrum__index_z_u1r, dtype=np.int64),
        "index_z_u1i": np.asarray(dc._Bispectrum__index_z_u1i, dtype=np.int64),
        "index_z_u2r": np.asarray(dc._Bispectrum__index_z_u2r, dtype=np.int64),
        "index_z_u2i": np.asarray(dc._Bispectrum__index_z_u2i, dtype=np.int64),
        "index_z_jjz": np.asarray(dc._Bispectrum__index_z_jjz, dtype=np.int64),
        "cglist": np.asarray(dc._Bispectrum__cglist, dtype=np.float64),
        "index_b_max": dc._Bispectrum__index_b_max,
        "index_b": dc._Bispectrum__index_b,
        "index_z_block": dc._Bispectrum__index_z_block,
        "index_u_block": dc._Bispectrum__index_u_block,
        "feature_size": dc.feature_size,
        "bispectrum_cutoff": dc.parameters.bispectrum_cutoff,
    }

    # Precompute membership positions for the 506-loop.
    # MALA's __compute_ui uses hit-counters jju1/jju2/jju3: when jju_outer is a
    # member of the set, it uses the counter-th entry of the paired arrays and
    # then increments.  This means the correct index for a member value v is
    # the RANK of v among the (distinct) members, i.e. the number of members
    # strictly less than v.  Note the symmetry arrays are NOT sorted, so using
    # `argwhere(membership == v)` (inverse position) would be WRONG.
    n = int(u_max)
    u_full_pos = -np.ones(n, dtype=np.int64)
    for v in cfg["index_u_full"]:
        u_full_pos[int(v)] = int((cfg["index_u_full"] < v).sum())
    sym_pos_pos = -np.ones(n, dtype=np.int64)
    for v in cfg["index_u1_symmetry_pos"]:
        sym_pos_pos[int(v)] = int((cfg["index_u1_symmetry_pos"] < v).sum())
    sym_neg_pos = -np.ones(n, dtype=np.int64)
    for v in cfg["index_u1_symmetry_neg"]:
        sym_neg_pos[int(v)] = int((cfg["index_u1_symmetry_neg"] < v).sum())
    cfg["u_full_pos"] = u_full_pos
    cfg["sym_pos_pos"] = sym_pos_pos
    cfg["sym_neg_pos"] = sym_neg_pos

    # Precompute segment boundaries for compute_zi.  index_z_jjz is sorted, so
    # each distinct jjz value occupies a contiguous block.  We store the block
    # STARTS so np.add.reduceat can sum each block in a fully vectorized way.
    # This mirrors MALA's `np.bincount(inverse, tmp_real)` exactly (same
    # grouping) but avoids the per-row Python loop / bincount cost.
    jjz = cfg["index_z_jjz"]
    zi_boundaries = np.concatenate(
        [[0], np.nonzero(np.diff(jjz))[0] + 1]
    ).astype(np.int64)
    cfg["zi_boundaries"] = zi_boundaries
    cfg["idxz_max"] = int(jjz.max()) + 1

    # Precompute compute_bi pair indices per jjb
    n_b = cfg["index_b_max"]
    start_jju = np.zeros(n_b, dtype=np.int64)
    start_jjz = np.zeros(n_b, dtype=np.int64)
    n_pairs = np.zeros(n_b, dtype=np.int64)
    has_half = np.zeros(n_b, dtype=bool)
    for jjb in range(n_b):
        b = cfg["index_b"][jjb]
        j1 = int(b.j1); j2 = int(b.j2); j = int(b.j)
        jjz = int(cfg["index_z_block"][j1][j2][j])
        jju = int(cfg["index_u_block"][j])
        s_jju = jju; s_jjz = jjz
        cnt = 0
        for mb in range(int(np.ceil(j / 2))):
            for ma in range(j + 1):
                cnt += 1
        if j % 2 == 0:
            mb = j // 2
            for ma in range(mb):
                cnt += 1
            has_half[jjb] = True
        start_jju[jjb] = s_jju
        start_jjz[jjb] = s_jjz
        n_pairs[jjb] = cnt
    cfg["bi_start_jju"] = start_jju
    cfg["bi_start_jjz"] = start_jjz
    cfg["bi_n_pairs"] = n_pairs
    cfg["bi_has_half"] = has_half
    return cfg


def calculate_bispectrum_batched(dc, atoms, grid, batch_size=128):
    """
    Compute bispectrum descriptors for `atoms` on `grid` using batched numpy.

    Parameters
    ----------
    dc : mala.descriptors.bispectrum.Bispectrum
        Configured object from prepare_bispectrum().
    atoms : ase.Atoms
    grid : list[int]
    batch_size : int
        Number of grid points processed per batch.

    Returns
    -------
    descs : numpy.ndarray
        Shape (nx, ny, nz, feature_size) with xyz.
    """
    cfg = prepare_config(dc)
    all_atoms = dc._setup_atom_list()
    nx, ny, nz = grid
    out = np.zeros((nx, ny, nz, cfg["feature_size"]), dtype=np.float64)

    # All grid point coordinates (precompute all, memory permitting)
    xs = np.arange(nx); ys = np.arange(ny); zs = np.arange(nz)
    gx, gy, gz = np.meshgrid(xs, ys, zs, indexing="ij")
    flat_xyz = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], axis=1)  # (N, 3)

    n_points = len(flat_xyz)
    for start in range(0, n_points, batch_size):
        chunk = flat_xyz[start:start + batch_size]
        B = len(chunk)
        coords = np.array([dc._grid_to_coord([int(x), int(y), int(z)])
                           for x, y, z in chunk])  # (B, 3)

        # Distances to all atoms
        dmat = distance.cdist(coords, all_atoms)  # (B, N_all)
        mask = dmat < cfg["bispectrum_cutoff"]

        # Build flat atom arrays
        counts = mask.sum(axis=1).astype(np.int64)
        boundaries = np.concatenate([[0], np.cumsum(counts)]).astype(np.int64)
        total = int(boundaries[-1])
        flat_atoms = np.zeros((total, 3), dtype=np.float64)
        flat_grid = np.zeros((total, 3), dtype=np.float64)
        flat_dists = np.zeros(total, dtype=np.float64)
        if total > 0:
            for b in range(B):
                lo = boundaries[b]; hi = boundaries[b + 1]
                if hi > lo:
                    idx = np.nonzero(mask[b])[0]
                    flat_atoms[lo:hi] = all_atoms[idx]
                    flat_grid[lo:hi] = coords[b]
                    flat_dists[lo:hi] = dmat[b, idx]
        ur, ui = _compute_ui_batched(
            (flat_atoms, flat_grid, flat_dists, boundaries[:-1]), cfg
        )
        zr, zi = _compute_zi_batched(ur, ui, cfg)
        bi = _compute_bi_batched(ur, ui, zr, zi, cfg)
        # Place into output (bi already includes xyz as first 3 columns)
        for b in range(B):
            x, y, z = chunk[b]
            out[x, y, z, 0:3] = coords[b]
            out[x, y, z, 3:] = bi[b, 3:]
    return out


def prepare_bispectrum(params, atoms, grid):
    """Build a configured Bispectrum object (same as parallel_bispectrum)."""
    from mala.descriptors.bispectrum import Bispectrum
    dc = Bispectrum(params)
    dc._atoms = dc.enforce_pbc(atoms)
    dc.grid_dimensions = list(grid)
    dc._voxel = dc._atoms.cell.copy()
    dc._voxel[0] = dc._voxel[0] / grid[0]
    dc._voxel[1] = dc._voxel[1] / grid[1]
    dc._voxel[2] = dc._voxel[2] / grid[2]

    dc._rmin0 = 0.0
    dc._rfac0 = 0.99363
    dc._bzero_flag = False
    dc._wselfall_flag = False
    dc._bnorm_flag = False
    dc._quadraticflag = False

    twojmax = params.descriptors.bispectrum_twojmax
    ncoeff = ((twojmax + 2) * (twojmax + 3) * (twojmax + 4)) // 24
    dc.feature_size = ncoeff + 3

    dc._Bispectrum__init_index_arrays()
    return dc
