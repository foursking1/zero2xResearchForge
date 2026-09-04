"""C03: Model-data variance ratios and correlations (paper Table 1, Fig. 2).

Reproduces the paper's "Multi-decadal GMST and Data-model agreement" method:

  - 30-200 yr bandpass Butterworth filter (R signal::butter, fs=2, end.m="pad",
    cut.end=F) applied to all data.
  - Reconstruction ensemble members are filtered over the full 1-2000 CE series
    (Figs_gmst.R line 62).
  - Model simulations are windowed to 850-1995 CE *before* filtering
    (Figs_gmst.R line 162), then the 1300-1995 window is used.
  - The data-model comparison is over the period 1300-2000 CE per the paper;
    with the model series ending in 1995 the common window is 1300-1995.
  - Variance ratio: per-pair median of model variance / member variance
    ("median model/data variance ratio across all reconstruction and model
    ensemble members is 1.01").
  - Correlation: Pearson correlation between each member and each model.
  - Significance: red-noise (AR(1)) surrogates with the same AR(1) coefficient
    as the corresponding (unfiltered) reconstruction/model data, bandpass-
    filtered, correlated with each other; the percentage of member-model
    correlations exceeding the 95th percentile of the noise correlation
    distribution is reported (paper reports 98.9-99.8 %).
"""
import os
import numpy as np
from scipy.signal import butter, filtfilt

from load_data import load_recon_ensembles, load_models_fullforced

METHODS = ["CPS", "PCR", "M08", "PAI", "OIE", "BHM", "DA"]
W_START, W_END = 1300, 1995   # common window (models end at 1995)
MOD_WIN = (850, 1995)         # model filtering window (Figs_gmst.R line 162)
N_MEMBERS = 1000
N_MODELS = 23


def bandpass30_200(y):
    """30-200 yr bandpass Butterworth; mirrors R bandpass.tsc.na(y, 30, 200,
    cut.end=F, end.m='pad').  NaN edges trimmed before filtering."""
    idx = np.where(~np.isnan(y))[0]
    if len(idx) == 0:
        return np.full(len(y), np.nan, dtype=float)
    sy, ey = idx.min(), idx.max()
    x = y[sy:ey + 1].astype(float)
    nx = 200 * 2
    nx2 = 30
    xp = np.concatenate([np.full(nx, np.mean(x[:nx2])),
                         x,
                         np.full(nx, np.mean(x[-nx2:]))])
    b, a = butter(2, [1.0 / 200, 1.0 / 30], btype='pass', fs=2)
    b1 = filtfilt(b, a, xp)
    b1 = b1[nx:len(b1) - nx]
    z = np.full(len(y), np.nan, dtype=float)
    z[sy:ey + 1] = b1
    return z


def ar1_fit(x):
    """Lag-1 autocorrelation of a series (after removing its mean)."""
    ok = ~np.isnan(x)
    xx = x[ok]
    if len(xx) < 10:
        return np.nan
    a, b = xx[:-1], xx[1:]
    va = np.var(a)
    if va == 0:
        return 0.0
    return np.mean((a - np.mean(a)) * (b - np.mean(b))) / va


def ar1_sim(n, phi, var):
    """Simulate an AR(1) series of length n with coefficient phi and variance var."""
    eps_std = np.sqrt(max(var * (1.0 - phi ** 2), 1e-12))
    eps = np.random.normal(0, eps_std, n)
    x = np.zeros(n)
    for t in range(1, n):
        x[t] = phi * x[t - 1] + eps[t]
    return x


def main():
    np.random.seed(42)

    # --- Reconstructions: bandpass over full 1-2000, then window ---
    recons = load_recon_ensembles()
    years = recons["CPS"][0]
    sel = (years >= W_START) & (years <= W_END)
    years_sel = years[sel]
    bp_members = {}
    for m in METHODS:
        y, d = recons[m]
        bp = np.full_like(d, np.nan)
        for i in range(d.shape[1]):
            bp[:, i] = bandpass30_200(d[:, i])
        bp_members[m] = bp[sel]                 # (696, 1000)

    # --- Models: window 850-1995, bandpass, then window 1300-1995 ---
    myears, mdata, mnames = load_models_fullforced()
    mwin = (myears >= MOD_WIN[0]) & (myears <= MOD_WIN[1])
    mod_win = mdata[mwin]                       # (1146, 23)
    bp_models = np.full_like(mod_win, np.nan)
    for j in range(N_MODELS):
        bp_models[:, j] = bandpass30_200(mod_win[:, j])
    myears_w = myears[mwin]
    msel = (myears_w >= W_START) & (myears_w <= W_END)
    bp_models = bp_models[msel]                 # (696, 23)
    print("common window:", W_START, "-", W_END, "n =", len(years_sel))
    assert len(years_sel) == bp_models.shape[0]

    # --- Variance ratio: per-pair model variance / member variance ---
    model_vars = np.nanvar(bp_models, axis=0)   # per model
    var_ratio_pairs = {}                        # method -> (1000, 23)
    print("\n=== Model/data variance ratio, 1300-1995 (bandpass 30-200) ===")
    for m in METHODS:
        mv = np.var(bp_members[m], axis=0)      # per member
        var_ratio_pairs[m] = model_vars[None, :] / mv[:, None]
        med = np.nanmedian(var_ratio_pairs[m])
        q = np.nanpercentile(var_ratio_pairs[m], [2.5, 97.5])
        print(f"{m}: median = {med:.3f}  [2.5-97.5: {q[0]:.3f}-{q[1]:.3f}]")
    overall = np.median(np.concatenate([var_ratio_pairs[m].ravel() for m in METHODS]))
    print(f"overall median (all pairs): {overall:.3f}   (paper: 1.01)")

    # --- Per-pair correlations (member x model) ---
    print("\n=== Model-data correlations, 1300-1995 (bandpass 30-200) ===")
    corr_all = {}
    for m in METHODS:
        sub = bp_members[m]
        corr = np.full((N_MEMBERS, N_MODELS), np.nan)
        for j in range(N_MODELS):
            b = bp_models[:, j]
            ok = ~np.isnan(b)
            A = sub[ok]
            Bc = b[ok] - np.mean(b[ok])
            Ac = A - np.mean(A, axis=0)
            num = (Ac * Bc[:, None]).sum(axis=0)
            den = np.sqrt((Ac ** 2).sum(axis=0)) * np.sqrt((Bc ** 2).sum())
            corr[:, j] = num / den
        corr_all[m] = corr
        med = np.nanmedian(corr)
        q = np.nanpercentile(corr, [2.5, 97.5])
        print(f"{m}: corr median = {med:.3f}  [2.5-97.5: {q[0]:.3f}-{q[1]:.3f}]")

    # --- Red-noise significance test ---
    # AR(1) fitted to the *unfiltered* anomalised data over the window
    # (fitting to bandpass-filtered data gives phi ~ 1 and a degenerate null).
    print("\n=== Significance via red-noise (AR(1)) surrogates ===")
    raw_model = mdata[mwin][msel]
    phi_model = np.array([ar1_fit(raw_model[:, j]) for j in range(N_MODELS)])
    var_model = np.array([np.var(raw_model[:, j]) for j in range(N_MODELS)])

    noise_mod = np.zeros((len(years_sel), N_MODELS))
    for j in range(N_MODELS):
        noise_mod[:, j] = ar1_sim(len(years_sel), phi_model[j], var_model[j])
    bp_noise_mod = np.full_like(noise_mod, np.nan)
    for j in range(N_MODELS):
        bp_noise_mod[:, j] = bandpass30_200(noise_mod[:, j])

    frac_signif = {}
    null_thr = {}
    for m in METHODS:
        raw = recons[m][1][sel]
        ph_m = np.array([ar1_fit(raw[:, i]) for i in range(N_MEMBERS)])
        va_m = np.array([np.var(raw[:, i]) for i in range(N_MEMBERS)])
        noise_m = np.zeros((len(years_sel), N_MEMBERS))
        for i in range(N_MEMBERS):
            noise_m[:, i] = ar1_sim(len(years_sel), ph_m[i], va_m[i])
        bp_noise_m = np.full_like(noise_m, np.nan)
        for i in range(N_MEMBERS):
            bp_noise_m[:, i] = bandpass30_200(noise_m[:, i])
        # null correlations: corr(bp(noise_member_i), bp(noise_model_j))
        null = np.full((N_MEMBERS, N_MODELS), np.nan)
        for j in range(N_MODELS):
            B = bp_noise_mod[:, j]
            Bc = B - np.mean(B)
            A = bp_noise_m
            Ac = A - np.mean(A, axis=0)
            num = (Ac * Bc[:, None]).sum(axis=0)
            den = np.sqrt((Ac ** 2).sum(axis=0)) * np.sqrt((Bc ** 2).sum())
            null[:, j] = num / den
        thr = np.nanpercentile(null, 95)
        null_thr[m] = thr
        frac = np.nanmean(corr_all[m] > thr)
        frac_signif[m] = frac
        print(f"{m}: noise 95th pct = {thr:.3f}   fraction significant = {frac*100:.1f}%")
    print(f"\nAll methods > 95% significant? {all(v > 0.95 for v in frac_signif.values())}")

    # --- Save compact summary (JSON, no large arrays) ---
    os.makedirs("results", exist_ok=True)
    out = {
        "methods": METHODS,
        "window": [W_START, W_END],
        "n_window": int(len(years_sel)),
        "variance_ratio_median": {m: float(np.nanmedian(var_ratio_pairs[m]))
                                  for m in METHODS},
        "variance_ratio_q025": {m: float(np.nanpercentile(var_ratio_pairs[m], 2.5))
                                for m in METHODS},
        "variance_ratio_q975": {m: float(np.nanpercentile(var_ratio_pairs[m], 97.5))
                                for m in METHODS},
        "overall_variance_ratio": float(overall),
        "corr_median": {m: float(np.nanmedian(corr_all[m])) for m in METHODS},
        "corr_q025": {m: float(np.nanpercentile(corr_all[m], 2.5)) for m in METHODS},
        "corr_q975": {m: float(np.nanpercentile(corr_all[m], 97.5)) for m in METHODS},
        "frac_significant": {m: float(frac_signif[m]) for m in METHODS},
        "noise_threshold_95": {m: float(null_thr[m]) for m in METHODS},
    }
    import json
    with open("results/c03_metrics.json", "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    print("saved results/c03_metrics.json")


if __name__ == "__main__":
    main()
