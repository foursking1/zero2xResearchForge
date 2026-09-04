"""Load and preprocess the frozen XRD data for task 1811.08425.

- exp.csv      : 88 experimental spectra (1499 pts, 2theta 10.04..69.96, 0.04 deg)
- label_exp.csv: class index (0..6) per experimental spectrum
- encoding.csv : class index -> space group name
- theor.csv    : 164 simulated spectra (2125 pts, 2theta 5.04..89.96, 0.04 deg)
- label_theo.csv: per-column space-group labels (2 per spectrum)

Preprocessing (following the paper: background removal + Savitzky-Golay
smoothing + normalization) is applied per spectrum on the common
2theta grid [10.04, 69.96].
"""

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from scipy.ndimage import minimum_filter

import config


def _read_exp():
    """Return (tw_theta [N,], X [N_spec, N_pts], y [N_spec,])."""
    exp = pd.read_csv(config.EXP_CSV, header=None, skiprows=1)
    tw = exp[1].to_numpy(dtype=np.float64)
    n_spec = (exp.shape[1] - 1) // 2
    X = np.empty((n_spec, len(tw)), dtype=np.float64)
    for i in range(n_spec):
        X[i] = exp[1 + 2 * i + 1].to_numpy(dtype=np.float64)
    le = pd.read_csv(config.LABEL_EXP_CSV, header=None, skiprows=1)
    y = le[1].to_numpy(dtype=np.int64)
    assert len(y) == n_spec, (len(y), n_spec)
    return tw, X, y


def _read_theor():
    """Return (tw [N,], X [N_spec, N_pts], sg_names [N_spec,])."""
    theo = pd.read_csv(config.THEOR_CSV, header=None, skiprows=2)
    n_spec = (theo.shape[1] - 1) // 2
    tw = theo[1].to_numpy(dtype=np.float64)
    X = np.empty((n_spec, len(tw)), dtype=np.float64)
    for i in range(n_spec):
        X[i] = theo[1 + 2 * i + 1].to_numpy(dtype=np.float64)
    lt = pd.read_csv(config.LABEL_THEO_CSV, header=None)
    names = [lt[1].iloc[2 * i] for i in range(n_spec)]
    return tw, X, names


def _trim_to_grid(X, src_tw, dst_tw, tol=1e-4):
    """Resample spectra to the dst grid by index matching (float-safe)."""
    idx = []
    for t in dst_tw:
        d = np.abs(src_tw - t)
        j = int(np.argmin(d))
        if abs(src_tw[j] - t) > tol:
            raise ValueError(f"no grid match within {tol} for {t}")
        idx.append(j)
    return X[:, np.array(idx)]


def _bg_remove(spec, win=config.BG_FILTER):
    """Background estimate = moving minimum, smoothed; subtract & clip >= 0."""
    k = win if win % 2 == 1 else win + 1
    bg = minimum_filter(spec, size=k, mode="nearest")
    bg = savgol_filter(bg, window_length=min(101, len(spec) - (len(spec) % 2) - 1),
                       polyorder=3, mode="nearest")
    return np.clip(spec - bg, 0.0, None)


def _smooth(spec):
    w = config.SMOOTH_WINDOW
    if len(spec) < w:
        return spec
    return savgol_filter(spec, window_length=w, polyorder=config.SMOOTH_ORDER,
                         mode="nearest")


def _normalize(spec, eps=1e-8):
    s = spec.astype(np.float64)
    lo, hi = s.min(), s.max()
    if hi - lo < eps:
        return np.zeros_like(s)
    return (s - lo) / (hi - lo)


def preprocess(X):
    """Full preprocessing pipeline: bg removal -> SG smoothing -> [0,1]."""
    out = np.empty_like(X, dtype=np.float64)
    for i in range(X.shape[0]):
        s = _bg_remove(X[i])
        s = _smooth(s)
        out[i] = _normalize(s)
    return out


def load_data(preprocessed=True):
    """Return dict with exp/theo data on the common 10.04..69.96 grid.

    Returns
    -------
    dict with keys:
      tw            : 2theta grid (1499,)
      X_exp, y_exp  : experimental (88, 1499) + labels (88,)
      X_theo, y_theo: simulated (164, 1499) + labels (164,)
      sg_names      : list of 7 space group names in class order
    """
    tw_e, X_e, y_e = _read_exp()
    tw_t, X_t, names = _read_theor()

    # common grid: use the experimental grid [10.04, 69.96]
    tw = tw_e
    X_t = _trim_to_grid(X_t, tw_t, tw)

    # map simulated space-group names -> class indices
    name2idx = {name: i for i, name in enumerate(config.SG_ENCODING)}
    y_t = np.array([name2idx[n] for n in names], dtype=np.int64)

    if preprocessed:
        X_e = preprocess(X_e)
        X_t = preprocess(X_t)

    return dict(tw=tw, X_exp=X_e, y_exp=y_e,
                X_theo=X_t, y_theo=y_t,
                sg_names=config.SG_ENCODING)


def class_distribution(y):
    return np.bincount(y, minlength=config.NUM_CLASSES)


if __name__ == "__main__":
    d = load_data()
    print("data dir      :", config.DATA_DIR)
    print("2theta grid   :", d["tw"][0], "..", d["tw"][-1],
          "n =", len(d["tw"]))
    print("exp           :", d["X_exp"].shape, "labels",
          class_distribution(d["y_exp"]))
    print("theo          :", d["X_theo"].shape, "labels",
          class_distribution(d["y_theo"]))
    print("sg_names      :", d["sg_names"])
    print("exp range     :", d["X_exp"].min(), d["X_exp"].max())
    print("theo range    :", d["X_theo"].min(), d["X_theo"].max())
