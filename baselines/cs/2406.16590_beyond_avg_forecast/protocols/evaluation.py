"""Multi-view evaluation protocol (SMAPE) per Cerqueira et al. (2024).

Views computed for every method on the *same* test segments:
  * overall       — pooled SMAPE over all test points (100%/n * Σ 2|ŷ-y|/(|ŷ|+|y|))
  * horizon       — SMAPE of the first (one-step-ahead) and last (multi-step) step
  * frequency     — SMAPE within monthly / quarterly / yearly
  * conditional   — difficult series (SNaive per-series SMAPE > 95% quantile)
                    and anomaly points (obs outside SNaive 99% prediction
                    interval), plus expected shortfall (mean of the largest
                    errors / worst tail)
  * win/loss      — per-series SMAPE comparison of every method against SNaive
                    (and each other) at the sequence level
"""

from __future__ import annotations

import numpy as np

from config import COND_DIFFICULT_QUANTILE, COND_ANOMALY_CI, SEASONAL_PERIODS

Z_ANOMALY = {0.99: 2.576}


def smape_point(a, b):
    """Pointwise symmetric MAPE in %; 0/0 -> 0 (declared convention)."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    num = np.abs(a - b)
    den = (np.abs(a) + np.abs(b)) / 2.0
    out = np.where(den > 0, 100.0 * num / den, 0.0)
    return out


def smape_pooled(a, b):
    p = smape_point(a, b)
    return float(p.mean())


class ForecastStore:
    """Ordered, aligned forecasts for all methods."""

    def __init__(self, series_list):
        self.series = series_list
        # global index -> position helper lists
        self.by_key = {}   # (dataset, freq) -> list of (global_idx, series)
        for i, s in enumerate(series_list):
            self.by_key.setdefault((s.dataset, s.frequency), []).append(i)
        self.fc = {}       # method -> dict (dataset,freq) -> (idx_array, fc_matrix)

    def add_forecasts(self, method, data_by_key):
        """data_by_key: {(dataset, freq): (idx_global_array, fc_matrix)}."""
        self.fc[method] = {k: (np.asarray(v[0]), np.asarray(v[1])) for k, v in data_by_key.items()}

    def methods(self):
        return list(self.fc.keys())

    def get(self, method, scope=None):
        """Return (global_idx, actual, forecast) arrays for the scope.
        scope: None (all) or (dataset, frequency)."""
        keys = list(self.fc[method].keys()) if scope is None else [scope]
        idx_all, act_all, fc_all = [], [], []
        for k in keys:
            idx, fcm = self.fc[method][k]
            for gi, row in zip(idx, fcm):
                s = self.series[int(gi)]
                h = s.horizon
                y = np.asarray(s.values[-h:], dtype=float)
                f = np.asarray(row[:h], dtype=float)
                if np.isnan(f).any():
                    continue
                idx_all.append(gi)
                act_all.append(y)
                fc_all.append(f)
        return np.array(idx_all), np.concatenate(act_all), np.concatenate(fc_all)

    def scope_series(self, scope=None):
        """Global indices of series in scope (all or (dataset,freq))."""
        if scope is None:
            return list(range(len(self.series)))
        return list(self.by_key.get(scope, []))

    def series_smape(self, method, gi):
        s = self.series[gi]
        (d, fr) = (s.dataset, s.frequency)
        idx, fcm = self.fc[method][(d, fr)]
        pos = np.where(idx == gi)[0][0]
        row = fcm[pos]
        f = np.asarray(row[: s.horizon], dtype=float)
        y = np.asarray(s.values[-s.horizon :], dtype=float)
        return float(smape_pooled(y, f))


# ---------------------------------------------------------------------------
# SNaive-derived condition definitions
# ---------------------------------------------------------------------------
def snaive_test_pi(series):
    """Return (snaive_forecast, sigma, z) for a series' test segment.

    sigma = std of one-step seasonal-naive residuals over the training part.
    """
    s = series
    H = s.horizon
    m = SEASONAL_PERIODS[s.frequency]
    train = np.asarray(s.values[:-H], dtype=float)
    n = len(train)
    if m == 1:
        res = np.diff(train)                                  # naive (s=1)
    else:
        res = train[m:] - train[:-m]
    sigma = float(np.std(res)) if res.size else 0.0
    fc = np.empty(H)
    for h in range(1, H + 1):
        if h <= m:
            src = n - m + h - 1
            fc[h - 1] = train[src] if 0 <= src else train[0]
        else:
            fc[h - 1] = fc[h - 1 - m]
    return fc, sigma, Z_ANOMALY[COND_ANOMALY_CI]


def anomaly_mask(series_list, scope=None):
    """Boolean mask over all test points: is the observation outside the SNaive
    99% prediction interval?  (Condition is method-independent — SNaive only.)"""
    m = []
    for s in series_list:
        if scope is not None and (s.dataset, s.frequency) != scope:
            m.append(np.zeros(s.horizon, dtype=bool))
            continue
        fc, sigma, z = snaive_test_pi(s)
        y = np.asarray(s.values[-s.horizon :], dtype=float)
        m.append(np.abs(y - fc) > z * sigma)
    return np.concatenate(m)


def difficult_series_mask(series_list, store, quantile=COND_DIFFICULT_QUANTILE):
    """Series where SNaive per-series SMAPE exceeds its 95% quantile."""
    smapes = np.array([store.series_smape("SNaive", gi)
                       for gi in range(len(series_list))])
    thr = np.quantile(smapes, quantile)
    return smapes, thr, smapes > thr


# ---------------------------------------------------------------------------
# view computations
# ---------------------------------------------------------------------------
def view_overall(store, scope=None, scope_label="all"):
    rows = []
    for method in store.methods():
        gi, y, f = store.get(method, scope)
        n = len(y)
        smape = smape_pooled(y, f) if n else np.nan
        rows.append(dict(dataset=scope_label, view="overall", condition="all",
                         method=method, smape=smape, n=n))
    return rows


def view_horizon(store, scope=None, scope_label="all"):
    rows = []
    # first step (h=0 index) and last step (h=H-1)
    parts = []
    for method in store.methods():
        for gi, s in enumerate(store.series):
            if scope is not None and (s.dataset, s.frequency) != scope:
                continue
            try:
                h = s.horizon
                idx, fcm = store.fc[method][(s.dataset, s.frequency)]
                pos = np.where(idx == gi)[0]
                if pos.size == 0:
                    continue
                f = np.asarray(fcm[pos[0]][:h], dtype=float)
                y = np.asarray(s.values[-h:], dtype=float)
                n_ = min(h, 2)
                parts.append((method, gi, y[:1], f[:1], y[-1:], f[-1:]))
            except KeyError:
                continue
    for method in store.methods():
        sub = [p for p in parts if p[0] == method]
        if not sub:
            continue
        y1 = np.concatenate([p[2] for p in sub]); f1 = np.concatenate([p[3] for p in sub])
        yl = np.concatenate([p[4] for p in sub]); fl = np.concatenate([p[5] for p in sub])
        rows.append(dict(dataset=scope_label, view="horizon", condition="first_step",
                         method=method, smape=smape_pooled(y1, f1), n=len(y1)))
        rows.append(dict(dataset=scope_label, view="horizon", condition="last_step",
                         method=method, smape=smape_pooled(yl, fl), n=len(yl)))
    return rows


def view_frequency(store):
    rows = []
    for freq in ["monthly", "quarterly", "yearly"]:
        mask_series = []
        ki = []
        scope = None
        # gather all test points of that frequency
        keys = [(d, freq) for d in ["M3", "Tourism"]]
        for k in keys:
            if k not in store.by_key:
                continue
            for gi in store.by_key[k]:
                s = store.series[gi]
                ki.append(gi)
        for method in store.methods():
            y_all, f_all = [], []
            for gi in ki:
                s = store.series[gi]
                try:
                    idx, fcm = store.fc[method][(s.dataset, s.frequency)]
                    pos = np.where(idx == gi)[0]
                    if pos.size == 0:
                        continue
                    f = np.asarray(fcm[pos[0]][:s.horizon], dtype=float)
                    y = np.asarray(s.values[-s.horizon:], dtype=float)
                    y_all.append(y); f_all.append(f)
                except KeyError:
                    continue
            if y_all:
                ya = np.concatenate(y_all); fa = np.concatenate(f_all)
                rows.append(dict(dataset="All", view="frequency", condition=freq,
                                 method=method, smape=smape_pooled(ya, fa), n=len(ya)))
    return rows


def view_conditional(store, series_list):
    rows = []
    # --- difficult series -------------------------------------------------
    smapes, thr, mask = difficult_series_mask(series_list, store)
    for method in store.methods():
        y_all, f_all = [], []
        for gi in np.where(mask)[0]:
            s = series_list[int(gi)]
            try:
                idx, fcm = store.fc[method][(s.dataset, s.frequency)]
                pos = np.where(idx == gi)[0]
                if pos.size == 0:
                    continue
                f = np.asarray(fcm[pos[0]][: s.horizon], dtype=float)
                y = np.asarray(s.values[-s.horizon:], dtype=float)
                y_all.append(y); f_all.append(f)
            except KeyError:
                continue
        if y_all:
            ya = np.concatenate(y_all); fa = np.concatenate(f_all)
            rows.append(dict(dataset="All", view="difficult", condition="snaive_95q",
                             method=method, smape=smape_pooled(ya, fa),
                             n=len(ya), thr_meta=float(thr)))
    # --- anomaly points -----------------------------------------------------
    am = anomaly_mask(series_list)
    pos_master = _master_point_positions(series_list)
    for method in store.methods():
        y_all, f_all = [], []
        for gi, s in enumerate(series_list):
            lo, hi = pos_master[gi]
            sub = am[lo:hi]
            if not sub.any():
                continue
            try:
                idx, fcm = store.fc[method][(s.dataset, s.frequency)]
                pos = np.where(idx == gi)[0]
                if pos.size == 0:
                    continue
                f = np.asarray(fcm[pos[0]][: s.horizon], dtype=float)[sub]
                y = np.asarray(s.values[-s.horizon:], dtype=float)[sub]
                y_all.append(y); f_all.append(f)
            except KeyError:
                continue
        if y_all:
            ya = np.concatenate(y_all); fa = np.concatenate(f_all)
            rows.append(dict(dataset="All", view="anomaly", condition="snaive_99pi",
                             method=method, smape=smape_pooled(ya, fa),
                             n=len(ya)))
    # --- expected shortfall (worst-5% point errors per method within anomalies)
    for method in store.methods():
        y_all, p_all = [], []
        for gi, s in enumerate(series_list):
            lo, hi = pos_master[gi]
            sub = am[lo:hi]
            if not sub.any():
                continue
            try:
                idx, fcm = store.fc[method][(s.dataset, s.frequency)]
                pos = np.where(idx == gi)[0]
                if pos.size == 0:
                    continue
                f = np.asarray(fcm[pos[0]][: s.horizon], dtype=float)[sub]
                y = np.asarray(s.values[-s.horizon:], dtype=float)[sub]
                p = smape_point(y, f)
                y_all.append(y); p_all.append(p)
            except KeyError:
                continue
        if p_all:
            p = np.concatenate(p_all)
            tail = np.sort(p)[-max(1, int(0.05 * len(p))):]
            rows.append(dict(dataset="All", view="expected_shortfall",
                             condition="anomaly_tail5", method=method,
                             smape=float(tail.mean()), n=len(tail)))
    return rows


def _master_point_positions(series_list):
    """Global index ranges of each series in the concatenated test-point stream."""
    pos = []
    acc = 0
    for s in series_list:
        pos.append((acc, acc + s.horizon))
        acc += s.horizon
    return pos


def view_winloss(store, series_list, opponents=("SNaive", "Theta", "ETS", "SES", "RWD", "ARIMA")):
    """Per-series win/loss of each method vs each opponent (SMAPE smaller wins)."""
    rows = []
    methods = [m for m in store.methods() if m != "SNaive"]
    for method in methods:
        for opp in opponents:
            if method == opp:
                continue
            wins = losses = ties = 0
            w_frac = []
            for gi in range(len(series_list)):
                try:
                    a = store.series_smape(method, gi)
                    b = store.series_smape(opp, gi)
                except (KeyError, IndexError):
                    continue
                eps = 1e-9
                if a < b - eps:
                    wins += 1
                elif a > b + eps:
                    losses += 1
                else:
                    ties += 1
            total = wins + losses + ties
            rows.append(dict(view="winloss", condition=f"vs_{opp}", method=method,
                             wins=wins, losses=losses, ties=ties, n_total=total,
                             win_rate=(wins / total if total else np.nan)))
    return rows


def build_evidence_table(store, series_list):
    """Assemble rows for results/evidence_table.csv."""
    rows = []
    scopes = [None, ("M3", "monthly"), ("M3", "quarterly"), ("M3", "yearly"),
              ("Tourism", "monthly"), ("Tourism", "quarterly"), ("Tourism", "yearly")]
    for scope in scopes:
        label = "All" if scope is None else f"{scope[0]}:{scope[1]}"
        rows += view_overall(store, scope, label)
    rows += view_frequency(store)
    rows += view_horizon(store, None, "All")
    rows += view_conditional(store, series_list)
    return rows


def winloss_table(store, series_list):
    return view_winloss(store, series_list)