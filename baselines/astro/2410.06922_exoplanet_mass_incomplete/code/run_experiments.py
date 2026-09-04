"""Main experiment pipeline.

Reproduces, on the frozen 2026-08-13 archive snapshot, the three parameter
regimes of Lalande, Tasker & Doya (2024, arXiv:2410.06922):

  * Dataset "complete"   -- six-property complete subset, 150 planets tested
                            (mass concealed for every test planet at once, as
                            the paper describes for the 550-planet set).
  * Dataset "full"       -- all 6,336 planets, six properties; every planet
                            with an observed mass is evaluated.
  * Dataset "extended"   -- the same 6,336 planets with eight properties,
                            evaluated with the kNN x KDE algorithm only (as
                            in the paper, section 4.3).

Protocol detail (documented in report.md):
  * the paper evaluates the full archive by hiding one property at a time
    (leave-one-out).  For the kNN-Imputer and kNN x KDE this is exact and
    cheap; for MICE it is done literally (one re-imputation per planet); for
    MissForest and GAIN (the two expensive iterative methods) the "batch
    leave-one-out" trick is used: batches of 60 planets have their mass
    concealed in the *same* re-imputation run, so the other ~2,364 observed
    masses remain visible and the column never becomes fully-observed-empty.
    The tiny (<=60-row) difference w.r.t. strict leave-one-out is quantified
    in a dedicated robustness block.
  * metrics are RMS(ln(m_obs / m_imp)) over the evaluated planets, following
    section 4.1.1 of the paper.

All numbers are computed from this frozen snapshot; nothing is hand copied.
"""
import json
import time

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

import config
import data_utils
import imputers
import baselines

ALGOS = ["kNN-Imputer", "MissForest", "GAIN", "MICE", "kNN×KDE"]
ALGO_TAGS = ["knn", "missforest", "gain", "mice", "knnkde"]
FULL_BATCH = 60            # batch-LOO size for MissForest and GAIN


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def to_log_mass(Z, sc, rows, col="log_masse"):
    """Convert a standardized mass column value back to log10(M/M_Earth)."""
    i = config.F6.index(col) if col in config.F6 else config.F8.index(col)
    return Z[rows, i] * sc.scale_[i] + sc.mean_[i]


# ------------------------------------------------------------------ helpers
RNG = np.random.default_rng(config.SEED)


def draw_batches(eval_rows, batch):
    """Deterministic partition of eval_rows into consecutive seeded batches."""
    perm = RNG.permutation(len(eval_rows))
    idx = np.asarray(eval_rows)[perm]
    return [idx[k:k + batch] for k in range(0, len(idx), batch)]


def _cross_scaler(feat):
    sc = StandardScaler()
    Z = sc.fit_transform(feat)
    return Z, sc


# ------------------------------------------------------------------ dataset1
def run_complete(ds):
    log("== complete dataset ==")
    feat = ds["complete"]["feat"]
    meta = ds["complete"]["meta"]
    Z, sc = _cross_scaler(feat)
    n = Z.shape[0]
    mass_i = config.F6.index("log_masse")
    log_obs = to_log_mass(Z, sc, np.arange(n))

    test, train = data_utils.split_test(np.arange(n))
    n_test = len(test)
    log_obs_test = log_obs[test]

    Zmask = Z.copy()
    Zmask[test, mass_i] = np.nan

    res = {}
    # kNN-Imputer
    log("  kNN-Imputer")
    Zimp = imputers.knn_imputer(Zmask, k=config.K_KNN)
    res["knn"] = to_log_mass(Zimp, sc, test)
    # MissForest
    log("  MissForest")
    res["missforest"] = to_log_mass(imputers.miss_forest(Zmask.copy()), sc, test)
    # MICE
    log("  MICE")
    res["mice"] = to_log_mass(imputers.mice(Zmask.copy()), sc, test)
    # GAIN
    log("  GAIN")
    res["gain"] = to_log_mass(imputers.gain_impute(Zmask.copy(), steps=config.GAIN_STEPS,
                                                   seed=config.SEED), sc, test)
    # kNN x KDE
    log("  kNN x KDE")
    lm_obs = to_log_mass(Z, sc, np.arange(n))
    masses_lin = np.where(np.isfinite(lm_obs), 10 ** lm_obs, np.nan)
    masses_lin[test] = np.nan          # concealed values (joint-mask protocol)
    kk = imputers.KNNKDE(Z, masses_lin, exclude_cols=[mass_i])
    m_imp = np.array([kk.impute(t)[0] for t in test])
    res["knnkde"] = np.log10(m_imp)

    # baselines
    #   mBM-class (complete-data regression over the five *other* observed
    #   properties, trained on the training subset only -- see baselines.py)
    nf = np.array([i for i in range(Z.shape[1]) if i != mass_i])
    mb = baselines.MassRadiusBaseline(Z[train][:, nf], to_log_mass(Z, sc, train))
    res["mBM-class"] = mb.predict(Z[test][:, nf])
    #   CK2017 (PS-CP) using the radius alone
    logR = to_log_mass(Z, sc, test, col="log_rade")
    res["PS-CP(CK17)"] = np.log10(baselines.chen_kipping_mass(10 ** logR))

    eps = {}
    for k, v in res.items():
        eps[k] = imputers.epsilon(log_obs_test, v)

    out = pd.DataFrame({"planet": meta["pl_name"].iloc[test].values,
                        "log_mass_obs": log_obs_test})
    for k, v in res.items():
        out["log_mass_imp_" + k] = v
    return out, eps, np.asarray(test), Z, sc


# ------------------------------------------------------------- dataset2 / full
def run_full(ds, test_planets, complete_eps):
    log("== full archive (six properties) ==")
    mass_i = config.F6.index("log_masse")
    n_nonmass = [i for i in range(len(config.F6)) if i != mass_i]
    feat = ds["full"]["feat"]
    meta = ds["full"]["meta"]
    Z, sc = _cross_scaler(feat)
    n = Z.shape[0]
    log_obs = to_log_mass(Z, sc, np.arange(n))
    eval_all = np.where(np.isfinite(log_obs))[0]
    import os
    if os.environ.get("EXO_QUICK"):          # development smoke-test mode
        eval_rows = np.random.default_rng(7).choice(
            eval_all, size=min(300, len(eval_all)), replace=False)
        log(f"  EXO_QUICK: evaluating a 300-planet subsample only")
    else:
        eval_rows = eval_all
    masses_lin = np.where(np.isfinite(log_obs), 10 ** log_obs, np.nan)
    name_pos = {name: i for i, name in enumerate(meta["pl_name"])}
    test = np.array([name_pos[p] for p in test_planets])
    # protect against duplicated names: keep first occurrence
    test = np.unique(test, return_counts=False)

    logf_imp = pd.DataFrame({"planet": meta["pl_name"], "log_mass_obs": log_obs,
                             "log_rade": to_log_mass(Z, sc, np.arange(n), "log_rade")})

    # --- kNN-Imputer: exact leave-one-out via precomputed distances ---------
    log("  kNN-Imputer (LOO)")
    t0 = time.time()
    Z_nonmass = Z[:, n_nonmass]
    out_lin = imputers.knn_imputer_loo_mass(Z_nonmass, masses_lin, k=config.K_KNN)
    logf_imp["log_mass_imp_knn"] = np.log10(out_lin)
    log(f"    done in {time.time() - t0:.0f}s")

    # --- MICE: literal leave-one-out ----------------------------------------
    log("  MICE (literal LOO)")
    t0 = time.time()
    log_mice = np.full(n, np.nan)
    for j, i in enumerate(eval_rows):
        Xr = Z.copy()
        Xr[i, mass_i] = np.nan
        res = imputers.mice(Xr)
        log_mice[i] = res[i, mass_i] * sc.scale_[mass_i] + sc.mean_[mass_i]
        if (j + 1) % 300 == 0:
            log(f"    {j + 1}/{len(eval_rows)}  ({time.time() - t0:.0f}s)")
    logf_imp["log_mass_imp_mice"] = log_mice
    log(f"    done in {time.time() - t0:.0f}s")

    # --- MissForest: batch leave-one-out -------------------------------------
    log("  MissForest (batch LOO)")
    t0 = time.time()
    log_mf = np.full(n, np.nan)
    for bi, batch in enumerate(draw_batches(eval_rows, FULL_BATCH)):
        Xr = Z.copy()
        Xr[batch, mass_i] = np.nan
        res = imputers.miss_forest(Xr)
        log_mf[batch] = to_log_mass(res, sc, batch)
        log(f"    batch {bi + 1}")
    logf_imp["log_mass_imp_missforest"] = log_mf
    log(f"    done in {time.time() - t0:.0f}s")

    # --- GAIN: batch leave-one-out -------------------------------------------
    log("  GAIN (batch LOO)")
    t0 = time.time()
    log_gain = np.full(n, np.nan)
    for bi, batch in enumerate(draw_batches(eval_rows, FULL_BATCH)):
        Xr = Z.copy()
        Xr[batch, mass_i] = np.nan
        res = imputers.gain_impute(Xr, steps=config.GAIN_STEPS,
                                   seed=config.SEED + bi * 7919)
        log_gain[batch] = to_log_mass(res, sc, batch)
        log(f"    batch {bi + 1}")
    logf_imp["log_mass_imp_gain"] = log_gain
    log(f"    done in {time.time() - t0:.0f}s")

    # --- kNN x KDE: exact leave-one-out ---------------------------------------
    log("  kNN x KDE (LOO)")
    t0 = time.time()
    kk = imputers.KNNKDE(Z, masses_lin, exclude_cols=[mass_i])
    m_imp = np.array([kk.impute(i)[0] for i in eval_rows])
    logf_imp["log_mass_imp_knnkde"] = np.nan
    logf_imp.loc[eval_rows, "log_mass_imp_knnkde"] = np.log10(m_imp)
    log(f"    done in {time.time() - t0:.0f}s")

    # --- PS-CP (Chen & Kipping 2017) on the radius-observed subset ------------
    logf_imp["log_mass_imp_pscp"] = np.where(
        np.isfinite(logf_imp["log_rade"]),
        np.log10(baselines.chen_kipping_mass(10 ** logf_imp["log_rade"])), np.nan)

    def eps_full(col):
        m = np.isfinite(logf_imp[col]) & np.isfinite(logf_imp["log_mass_obs"])
        return imputers.epsilon(logf_imp.loc[m, "log_mass_obs"].values,
                                logf_imp.loc[m, col].values), int(m.sum())

    metrics = {}
    for tag, name in zip(ALGO_TAGS, ALGOS):
        e_full, cnt = eps_full("log_mass_imp_" + tag)
        e150 = imputers.epsilon(logf_imp.loc[test, "log_mass_obs"].values,
                                logf_imp.loc[test, "log_mass_imp_" + tag].values)
        metrics[name] = {"eps_full": e_full, "n_full": int(cnt),
                         "eps_150": e150}
        log(f"  {name:16s} eps_full={e_full:.4f}  eps150={e150:.4f}")

    # PS-CP rows
    e_pscp, cp = eps_full("log_mass_imp_pscp")
    metrics["PS-CP(CK17)"] = {"eps_full": e_pscp, "n_full": int(cp),
                              "eps_150": imputers.epsilon(
                                  logf_imp.loc[test, "log_mass_obs"].values,
                                  logf_imp.loc[test, "log_mass_imp_pscp"].values)}

    # 150-subset direction w.r.t. the complete dataset
    tag_map = dict(zip(ALGOS, ALGO_TAGS))
    for name in ALGOS:
        if tag_map[name] in complete_eps:
            metrics[name]["eps150_complete"] = complete_eps[tag_map[name]]
            metrics[name]["delta_150"] = metrics[name]["eps_150"] - complete_eps[tag_map[name]]
    return logf_imp, metrics, Z, sc, eval_rows, test


# ------------------------------------------------------- dataset3 / extended
def run_extended(ds, test_planets, full_knnkde):
    log("== extended archive (eight properties, kNN x KDE only) ==")
    feat = ds["extended"]["feat"]
    meta = ds["extended"]["meta"]
    mass_i = config.F8.index("log_masse")
    Z, sc = _cross_scaler(feat)
    n = Z.shape[0]
    log_obs = to_log_mass(Z, sc, np.arange(n), "log_masse")
    eval_rows = np.where(np.isfinite(log_obs))[0]
    masses_lin = np.where(np.isfinite(log_obs), 10 ** log_obs, np.nan)
    name_pos = {name: i for i, name in enumerate(meta["pl_name"])}
    test = np.array([name_pos[p] for p in test_planets])
    test = np.unique(test, return_counts=False)

    kk = imputers.KNNKDE(Z, masses_lin, exclude_cols=[mass_i])
    m_imp = np.array([kk.impute(i)[0] for i in eval_rows])
    log_ext = np.full(n, np.nan)
    log_ext[eval_rows] = np.log10(m_imp)

    e_full = imputers.epsilon(log_obs[eval_rows], log_ext[eval_rows])
    e150 = imputers.epsilon(log_obs[test], log_ext[test])
    log(f"  kNN x KDE eps_full={e_full:.4f}  eps150={e150:.4f}")

    out = pd.DataFrame({"planet": meta["pl_name"],
                        "log_mass_obs": log_obs,
                        "log_mass_imp_knnkde": log_ext})
    return out, {"kNN×KDE": {"eps_full": e_full, "n_full": int(len(eval_rows)),
                             "eps_150": e150,
                             "eps_full_6attr": full_knnkde["eps_full"],
                             "eps_150_6attr": full_knnkde["eps_150"]}}, Z, sc, eval_rows, test


# ------------------------------------------------------------ distributions
DIST_PLANETS = ["HAT-P-57 b", "TRAPPIST-1 f", "Kepler-9 c", "Kepler-30 c",
                "HD 109988 b", "USco CTIO 108 b", "14 Her b"]


def distributions_full(ds, runfull, runext):
    log("== kNN x KDE distributions ==")
    feat = ds["full"]["feat"]
    meta = ds["full"]["meta"]
    Z, sc = _cross_scaler(feat)
    mass_i = config.F6.index("log_masse")
    n = Z.shape[0]
    log_obs = to_log_mass(Z, sc, np.arange(n))
    masses_lin = np.where(np.isfinite(log_obs), 10 ** log_obs, np.nan)
    kk = imputers.KNNKDE(Z, masses_lin, exclude_cols=[mass_i])

    ratings = {}
    grids = {}
    for name in DIST_PLANETS:
        rows = meta.index[meta["pl_name"] == name].tolist()
        if not rows:
            continue
        i = rows[0]
        grid, dens, h, w, m = kk.distribution(i)
        m_imp, nb, D, w_prob, m_nei = kk.impute(i)
        d_mass = {"planet": name, "n_neighbors": int(len(nb)),
                  "obs_logmass": log_obs[i], "imp_logmass": np.log10(m_imp),
                  "bandwidth_log": h, "std_neighbour_log": float(np.std(np.log10(m_nei)))}
        profiles = pd.DataFrame({"log10_mass": grid, "density": dens})
        scores = profile_stats(grid, dens)
        d_mass.update(scores)
        ratings[name] = d_mass
        grids[name] = profiles
        log(f"  {name:16s} imp={np.log10(m_imp):5.2f} obs={log_obs[i]:5.2f} "
            f"nmodes={scores['n_modes']} w68={scores['width_68']:.2f}")

    # 14 Her b with the extended (eight) properties
    feat8 = ds["extended"]["feat"]
    Z8, sc8 = _cross_scaler(feat8)
    mass_i8 = config.F8.index("log_masse")
    n8 = Z8.shape[0]
    log_obs8 = to_log_mass(Z8, sc8, np.arange(n8), "log_masse")
    masses_lin8 = np.where(np.isfinite(log_obs8), 10 ** log_obs8, np.nan)
    kk8 = imputers.KNNKDE(Z8, masses_lin8, exclude_cols=[mass_i8])
    rows = meta.index[meta["pl_name"] == "14 Her b"].tolist()
    i = rows[0]
    grid, dens, h, w, m = kk8.distribution(i)
    m_imp8, *_ = kk8.impute(i)
    ratings["14 Her b (extended)"] = {
        "planet": "14 Her b", "version": "8attr",
        "imp_logmass": np.log10(m_imp8), "obs_logmass": log_obs8[i],
        "n_modes": None, "width_68": None}
    grids["14 Her b (extended)"] = pd.DataFrame({"log10_mass": grid, "density": dens})
    log(f"  14 Her b (8 attr) imp={np.log10(m_imp8):5.2f} obs={log_obs8[i]:5.2f}")

    return ratings, grids


def profile_stats(grid, dens):
    """Number of resolved modes and the 68%-mass interval in log10 units."""
    d = np.asarray(dens)
    g = np.asarray(grid)
    # smooth with a small window average
    w = 3
    kern = np.ones(w) / w
    smooth = np.convolve(d, kern, mode="same")
    peaks = (smooth[1:-1] > smooth[:-2]) & (smooth[1:-1] > smooth[2:])
    inds = np.where(peaks)[0] + 1
    if len(inds) == 0:
        inds = [int(np.argmax(smooth))]
    nmodes = len(inds)
    # 68% interval around the mode
    csum = np.cumsum(smooth)
    csum /= csum[-1] + 1e-12
    i0 = inds[np.argmax(smooth[inds])]
    lo = np.searchsorted(csum, csum[i0] - 0.34)
    hi = np.searchsorted(csum, csum[i0] + 0.34)
    width = float(g[hi] - g[lo]) if hi < len(g) else float(g[-1] - g[lo])
    return {"n_modes": int(nmodes), "mode_logmass": float(g[i0]),
            "width_68": width}


# ------------------------------------------------------------ RV regime
def run_rv(ds, complete_meta, test_planets, sc_complete, Z_complete, full_sc, full_Z):
    """kNN x KDE in the RV regime: both mass and radius are concealed for the
    150 test planets and a minimum-mass observation m_min = m_true sin(i) is
    assumed (satellite of R_DRAWS random inclinations).  The estimated mass
    distribution is weighted (convolved) by the pdf of the true mass given a
    minimum-mass detection (section 3.1 / Fig. 5 of the paper)."""
    log("== RV regime (kNN x KDE with minimum-mass convolution) ==")
    R_DRAWS = 50

    def f_cond(logm_min, logm_j):
        """pdf of the (true) mass m_j given a minimum-mass observation m_min,
        assuming sin(i) is distributed as on a unit sphere (P(cos i) flat)."""
        m_min = 10 ** logm_min
        mj = 10 ** logm_j
        mj = np.clip(mj, m_min * 1.001, None)
        f = m_min ** 2 / (mj ** 3 * np.sqrt(np.maximum(1 - (m_min / mj) ** 2,
                                                       1e-9)))
        return f

    def estimate(targets, Z, sc, candidates, exclude_cols):
        log_obs = to_log_mass(Z, sc, np.arange(Z.shape[0]))
        rad_obs = to_log_mass(Z, sc, np.arange(Z.shape[0]), "log_rade")
        kk = imputers.KNNKDE(
            Z, np.where(np.isfinite(log_obs), 10 ** log_obs, np.nan),
            exclude_cols=exclude_cols)
        m_imp, r_imp = [], []
        for t in targets:
            nb, D = kk._neighbourhood(t, ref_mask=candidates)
            w = kk.weights_from_dist(D)
            m_nei = 10 ** to_log_mass(Z, sc, nb)
            r_nei = 10 ** to_log_mass(Z, sc, nb, "log_rade")
            rng = np.random.default_rng(7 + t)
            u = rng.uniform(0, 1, R_DRAWS)
            sin_i = np.sqrt(1 - u ** 2)
            logm_min = np.log10(10 ** log_obs[t] * sin_i)
            m_c = np.zeros(R_DRAWS)
            for k in range(R_DRAWS):
                f = f_cond(logm_min[k], np.log10(m_nei))
                W = w * f
                W /= W.sum()
                m_c[k] = (W * m_nei).sum()
            m_imp.append(m_c.mean())
            r_imp.append((w * r_nei).sum())
        m_imp = np.array(m_imp)
        r_imp = np.array(r_imp)
        return m_imp, r_imp, log_obs, rad_obs

    out = {}
    # -- complete dataset: candidates exclude the 150 test planets -----------
    Z = Z_complete
    n = Z.shape[0]
    name_pos = {name: i for i, name in enumerate(complete_meta["pl_name"])}
    test = np.array([name_pos[p] for p in test_planets])
    log_obs = to_log_mass(Z, sc_complete, np.arange(n))
    rad_obs = to_log_mass(Z, sc_complete, np.arange(n), "log_rade")
    has_both = np.isfinite(log_obs) & np.isfinite(rad_obs)
    candidates = np.flatnonzero(has_both)
    candidates = candidates[~np.isin(candidates, test)]
    excl = [config.F6.index("log_masse"), config.F6.index("log_rade")]
    m_imp, r_imp, lo, ro = estimate(test, Z, sc_complete, candidates, excl)
    e_m = imputers.epsilon(lo[test], np.log10(m_imp))
    e_r = imputers.epsilon(ro[test], np.log10(r_imp))
    out["complete"] = {"eps_mass": e_m, "eps_radius": e_r, "n": int(len(test))}
    log(f"  complete: eps_mass={e_m:.4f} eps_radius={e_r:.4f}")

    # -- full archive: leave-one-out (candidates = all planets with both) ----
    Z = full_Z
    n = Z.shape[0]
    full_meta = ds["full"]["meta"]
    name_pos = {name: i for i, name in enumerate(full_meta["pl_name"])}
    test = np.array([name_pos[p] for p in test_planets])
    log_obs = to_log_mass(Z, full_sc, np.arange(n))
    rad_obs = to_log_mass(Z, full_sc, np.arange(n), "log_rade")
    has_both = np.isfinite(log_obs) & np.isfinite(rad_obs)
    candidates = np.flatnonzero(has_both)
    log(f"    full archive planets w/ mass+radius: {len(candidates)}")
    m_imp, r_imp, lo, ro = estimate(test, Z, full_sc, candidates, excl)
    e_m = imputers.epsilon(lo[test], np.log10(m_imp))
    e_r = imputers.epsilon(ro[test], np.log10(r_imp))
    out["full"] = {"eps_mass": e_m, "eps_radius": e_r, "n": int(len(test))}
    log(f"  full: eps_mass={e_m:.4f} eps_radius={e_r:.4f}")
    return out


# -------------------------------------------------------------- robustness
def robustness(ds):
    log("== robustness: joint vs leave-one-out for MICE ==")
    mass_i = config.F6.index("log_masse")
    feat = ds["full"]["feat"]
    Z, sc = _cross_scaler(feat)
    n = Z.shape[0]

    def eps_i(logobs, logimp):
        m = np.isfinite(logimp) & np.isfinite(logobs)
        return imputers.epsilon(logobs[m], logimp[m])

    # MICE: strict LOO (subsample) vs joint-masked single run (subsample)
    logobs = to_log_mass(Z, sc, np.arange(n))
    eval_rows = np.where(np.isfinite(logobs))[0]
    sub = RNG.choice(eval_rows, size=min(200, len(eval_rows)), replace=False)
    loo = np.full(n, np.nan)
    for i in sub:
        Xr = Z.copy(); Xr[i, mass_i] = np.nan
        res = imputers.mice(Xr)
        loo[i] = res[i, mass_i] * sc.scale_[mass_i] + sc.mean_[mass_i]
    # joint: hide sub masses at once (column never fully-empty)
    Xj = Z.copy(); Xj[sub, mass_i] = np.nan
    resj = imputers.mice(Xj)
    joint = to_log_mass(resj, sc, sub)
    mice_vs = {"loo": eps_i(logobs[sub], loo[sub]),
               "joint": eps_i(logobs[sub], joint)}

    # kNN x KDE point-estimate sensitivity on the complete dataset
    log("  robustness: kNN x KDE point-estimate variants")
    featc = ds["complete"]["feat"]
    Zc, scc = _cross_scaler(featc)
    log_obsc = to_log_mass(Zc, scc, np.arange(Zc.shape[0]))
    test, _ = data_utils.split_test(np.arange(Zc.shape[0]))
    ml_c = np.where(np.isfinite(log_obsc), 10 ** log_obsc, np.nan)
    ml_c[test] = np.nan

    def knkde_eps(tau, mode, rows=test):
        kk = imputers.KNNKDE(Zc, ml_c, tau=tau, exclude_cols=[mass_i])
        out = []
        for t in rows:
            nb, D = kk._neighbourhood(t)
            w = kk.weights_from_dist(D)
            m = kk.masses_lin[nb]
            if mode == "geom":
                out.append(np.exp((w * np.log(m)).sum()))
            elif mode == "arith":
                out.append((w * m).sum())
            elif mode == "median":
                out.append(np.median(m))
        return imputers.epsilon(log_obsc[test], np.log10(out))

    knkde_vs = {
        "geom_flat_tau20": knkde_eps(20.0, "geom"),
        "geom_default_tau2": knkde_eps(2.0, "geom"),
        "geom_sharp_tau0.2": knkde_eps(0.2, "geom"),
        "arith_default_tau2": knkde_eps(2.0, "arith"),
        "median_default_tau2": knkde_eps(2.0, "median"),
    }

    return {"mice_joint_vs_loo_eps": mice_vs,
            "knnkde_point_estimate_variants_eps": knkde_vs,
            "n_planets": int(len(sub))}


def main():
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    config.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    log("load & verify")
    df = data_utils.load_frozen_csv()
    ds = data_utils.build_datasets(df)

    # missing-rate summary -------------------------------------------------
    missing = {}
    for c in config.SIX_COLS + ["pl_orbeccen", "st_met"]:
        miss = df[c].isna().sum()
        missing[c] = {"missing": int(miss), "rate": float(miss / len(df))}
    missing["_planets"] = int(len(df))
    missing["_complete_subset"] = int(len(ds["complete"]["meta"]))

    # Dataset 1 --------------------------------------------------------------
    comp_out, comp_eps, test_pos, Zc, scc = run_complete(ds)
    test_planets = comp_out["planet"].tolist()
    comp_out.to_csv(config.RESULTS_DIR / "imputed_complete.csv", index=False)

    # Dataset 2 --------------------------------------------------------------
    full_out, full_metrics, Zf, scf, eval_rows_f, test_full = run_full(
        ds, test_planets, comp_eps)
    full_out.to_csv(config.RESULTS_DIR / "imputed_full.csv", index=False)

    # Dataset 3 --------------------------------------------------------------
    ext_out, ext_metrics, Ze, sce, eval_rows_e, test_ext = run_extended(
        ds, test_planets, full_metrics["kNN×KDE"])
    ext_out.to_csv(config.RESULTS_DIR / "imputed_extended.csv", index=False)

    # distributions ----------------------------------------------------------
    ratings, grids = distributions_full(ds, None, None)
    pd.DataFrame(ratings).T.to_csv(config.RESULTS_DIR / "distributions_stats.csv",
                                   index=False)
    for name, g in grids.items():
        g.to_csv(config.RESULTS_DIR / f"distribution_{name.replace(' ', '_')}.csv",
                 index=False)

    # RV regime ---------------------------------------------------------------
    rv = run_rv(ds, ds["complete"]["meta"], test_planets, scc, Zc, scf, Zf)

    # robustness --------------------------------------------------------------
    rob = robustness(ds)

    # assemble evidence table & metrics json ---------------------------------
    rows = []

    for name in ALGOS:
        tag = dict(zip(ALGOS, ALGO_TAGS))[name]
        rows.append({"dataset": "complete",
                     "algorithm": name,
                     "protocol": "joint-mask 150 test masses",
                     "n_test": int(len(test_planets)),
                     "eps": comp_eps[tag],
                     "eps_150": comp_eps[tag]})
    rows.append({"dataset": "complete",
                 "algorithm": "mBM-class (mass-radius baseline)",
                 "protocol": "complete-data regression",
                 "n_test": int(len(test_planets)),
                 "eps": comp_eps["mBM-class"],
                 "eps_150": comp_eps["mBM-class"]})
    rows.append({"dataset": "complete",
                 "algorithm": "PS-CP (CK2017)",
                 "protocol": "radius->mass relation",
                 "n_test": int(len(test_planets)),
                 "eps": comp_eps["PS-CP(CK17)"],
                 "eps_150": comp_eps["PS-CP(CK17)"]})

    protocols = {"kNN-Imputer": "leave-one-out", "MICE": "leave-one-out",
                 "MissForest": "batched leave-one-out", "GAIN": "batched leave-one-out",
                 "kNN×KDE": "leave-one-out"}
    for name in ALGOS:
        m = full_metrics[name]
        rows.append({"dataset": "full", "algorithm": name,
                     "protocol": protocols[name],
                     "n_test": m["n_full"], "eps": m["eps_full"],
                     "eps_150": m["eps_150"]})
    m = full_metrics["PS-CP(CK17)"]
    rows.append({"dataset": "full", "algorithm": "PS-CP (CK2017)",
                 "protocol": "radius->mass relation",
                 "n_test": m["n_full"], "eps": m["eps_full"],
                 "eps_150": m["eps_150"]})

    m = ext_metrics["kNN×KDE"]
    rows.append({"dataset": "extended", "algorithm": "kNN×KDE",
                 "protocol": "leave-one-out",
                 "n_test": m["n_full"], "eps": m["eps_full"],
                 "eps_150": m["eps_150"]})

    evidence = pd.DataFrame(rows)
    rr = config.RESULTS_DIR / "evidence_table.csv"
    evidence.to_csv(rr, index=False)
    (config.EVIDENCE_DIR / "evidence_table.csv").write_text(evidence.to_csv(index=False))

    # metrics.json ------------------------------------------------------------
    metrics = {
        "snapshot": {
            "file": "pscomppars_2026-08-13.csv", "planets": int(len(df)),
            "complete_subset_planets": int(len(ds["complete"]["meta"])),
            "mass_missing_rate": missing["pl_masse"]["rate"],
            "paper_snapshot_planets": 5251, "paper_mass_missing_rate": 0.728,
        },
        "complete_subset": {
            "n_train": int(len(ds["complete"]["meta"]) - len(test_planets)),
            "n_test": int(len(test_planets)),
            "eps": {k: v for k, v in comp_eps.items()},
            "ranking": sorted(comp_eps, key=comp_eps.__getitem__),
        },
        "full_archive": full_metrics,
        "extended_archive": ext_metrics,
        "150_test_subset_direction": {
            name: full_metrics[name].get("delta_150") for name in ALGOS},
        "distribution_examples": ratings,
        "rv_regime": rv,
        "robustness": rob,
        "gain_gap": {
            "complete": comp_eps["gain"] - comp_eps["knnkde"],
            "full": full_metrics["GAIN"]["eps_full"] - full_metrics["kNN×KDE"]["eps_full"],
            "full_150": full_metrics["GAIN"]["eps_150"] - full_metrics["kNN×KDE"]["eps_150"]},
        "winning_algorithm": (
            "kNN×KDE" if min(full_metrics[n]["eps_full"] for n in ALGOS) ==
                full_metrics["kNN×KDE"]["eps_full"] else None),
    }
    (config.RESULTS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))
    (config.EVIDENCE_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))
    log("WROTE results/evidence_table.csv and results/metrics.json")
    return metrics


if __name__ == "__main__":
    main()