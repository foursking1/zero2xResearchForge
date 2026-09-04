"""Classical, local (per-series) forecasting methods.

Implements the six classical baselines used in the evaluation, each modelling
every series independently (local methods): SNaive, Theta, SES, ETS, RWD, ARIMA.

All methods follow the *same* protocol: train on ``values[:-H]`` (never on the
test segment) and produce a length-``H`` forecast vector, where ``H`` is the
series-specific horizon from the frozen ``@horizon`` header.
"""

from __future__ import annotations

import warnings

import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing
from statsmodels.tsa.arima.model import ARIMA

import config
from config import SEASONAL_PERIODS

_SEASONAL = SEASONAL_PERIODS
warnings.filterwarnings("ignore")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def seasonal_indices_mul(y_like_values, s, n_seasons=6):
    """Multiplicative seasonal indices from a sample of recent seasons."""
    if s <= 1:
        return np.ones(1)
    vals = np.asarray(y_like_values, dtype=float)
    nseas = min(n_seasons, len(vals) // s)
    if nseas < 2:
        # not enough data for seasonal indices -> flat
        return np.ones(s)
    y = vals[-nseas * s:]
    seasonal = np.zeros(s)
    for k in range(s):
        idx = np.arange(k, len(y), s)
        seasonal[k] = np.mean(y[idx])
    grand = np.mean(y)
    if grand == 0:
        return np.ones(s)
    return (seasonal / grand).clip(min=1e-3)


def _olser_slope(x):
    n = len(x)
    t = np.arange(1, n + 1, dtype=float)
    t = t - t.mean()
    xm = x - x.mean()
    denom = (t * t).sum()
    if denom == 0:
        return 0.0
    return float((t * xm).sum() / denom)


# ---------------------------------------------------------------------------
# methods (each returns the H-step forecast vector)
# ---------------------------------------------------------------------------
def forecast_snaive(values, H, s):
    """Seasonal naive: repeat the value s steps back (recursively)."""
    train = np.asarray(values[:-H], dtype=float)
    n = len(train)
    fc = np.empty(H)
    for h in range(1, H + 1):
        if h <= s:
            src = n - s + h - 1
            fc[h - 1] = train[src] if 0 <= src else train[0]
        else:
            fc[h - 1] = fc[h - 1 - s]
    return fc


def forecast_ses(values, H, s=1):
    train = np.asarray(values[:-H], dtype=float)
    model = SimpleExpSmoothing(train)
    try:
        fitted = model.fit(optimized=True, remove_bias=False)
    except Exception:
        fitted = model.fit(smoothing_level=0.5)
    return np.full(H, float(fitted.forecast(1)[0]))


def forecast_rwd(values, H, s=1):
    """Random walk with drift."""
    train = np.asarray(values[:-H], dtype=float)
    n = len(train)
    last = train[-1]
    drift = (train[-1] - train[0]) / (n - 1) if n > 1 else 0.0
    return last + drift * np.arange(1, H + 1)


def forecast_ets(values, H, s):
    """ETS (exponential smoothing) with simple model selection by AIC.

    Candidates: [SES (no trend, no season)] and, when applicable,
    Holt (additive trend + optional additive seasonality for s>1).
    """
    train = np.asarray(values[:-H], dtype=float)
    nr = len(train)
    aic = {}
    fits = {}
    try:
        m_ses = SimpleExpSmoothing(train)
        f_ses = m_ses.fit(optimized=True)
        aic["E(S)N"] = f_ses.aic
        fits["E(S)N"] = f_ses
    except Exception:
        pass

    seasonal_ok = s > 1 and nr > 2 * s
    if nr > 3:
        spec_trend = ["add", None][0]
        try:
            m_holt = ExponentialSmoothing(train, trend="add", damped_trend=False)
            f_holt = m_holt.fit(optimized=True)
            aic["A(A)N"] = f_holt.aic
            fits["A(A)N"] = f_holt
        except Exception:
            pass
        if seasonal_ok:
            try:
                m_ets = ExponentialSmoothing(
                    train, trend="add", seasonal="add", seasonal_periods=s, damped_trend=False
                )
                f_ets = m_ets.fit(optimized=True)
                aic["A(A)A"] = f_ets.aic
                fits["A(A)A"] = f_ets
            except Exception:
                pass

    if aic:
        best_key = min(aic, key=aic.get)
        fc = fits[best_key].forecast(H)
        return np.asarray(fc, dtype=float)
    return forecast_ses(values, H, s)


def forecast_theta(values, H, s):
    """Theta method (Assimakopoulos & Nikolopoulos 2000).

    Standard "SES-with-drift" formulation (Hyndman & Billah 2003): the theta
    forecast equals an optimised simple exponential smoothing of (a seasonally
    adjusted) series plus half the linear-trend drift per horizon step.
    Seasonal series are handled multiplicatively.
    """
    train = np.asarray(values[:-H], dtype=float)
    n = len(train)
    if n < 3:
        return forecast_ses(values, H, s)

    if s > 1 and n > 2 * s + H:
        si = seasonal_indices_mul(train, s)
        des = train / np.tile(si, int(np.ceil(n / s)) + 1)[:n]
    else:
        si = np.ones(1)
        des = train

    # drift (OLS slope of the deseasonalised series)
    slope = _olser_slope(des)

    # SES on deseasonalised series (optimised alpha)
    try:
        model = SimpleExpSmoothing(des)
        fit = model.fit(optimized=True)
        level = float(fit.forecast(1)[0])
    except Exception:
        level = float(des[-1])

    # Theta forecast on deseasonalised scale, then reseasonalise
    fc_des = level + 0.5 * slope * np.arange(1, H + 1)
    fc = fc_des.copy()
    if len(si) > 1:
        for h in range(H):
            fc[h] *= si[(n + h) % s]
    return fc


def forecast_arima(values, H, grid=None, max_obs=600):
    """ARIMA with light model selection over a small order grid (by AIC)."""
    grid = grid or list(config.ARIMA_GRID)
    train = np.asarray(values[:-H], dtype=float)
    if len(train) > max_obs:
        train = train[-max_obs:]

    last_best = None
    best_aic = np.inf
    best_model = None
    exog_last = None
    exog_future = None
    n = len(train)
    t = np.arange(1, n + 1, dtype=np.float64)
    for order in grid:
        try:
            if order[1] >= 1:
                # allow a drift term for integrated models via a linear exog
                m = ARIMA(train, order=order, trend="n", exog=t)
            else:
                m = ARIMA(train, order=order, trend="c")
            res = m.fit(method_kwargs={"maxiter": 200})
            if (res.aic or np.inf) < best_aic:
                best_aic = res.aic
                best_model = res
                last_best = order
                exog_last = order[1] >= 1
        except Exception:
            continue
    if best_model is None:
        # fallback: random-walk (naive)
        return forecast_snaive(values, H, 1)
    try:
        if exog_last:
            exog_future = np.arange(n + 1, n + H + 1, dtype=np.float64)
            fc = best_model.forecast(H, exog=exog_future)
        else:
            fc = best_model.forecast(H)
        return np.asarray(fc, dtype=float)
    except Exception:
        return forecast_snaive(values, H, 1)


# ---------------------------------------------------------------------------
# dispatcher
# ---------------------------------------------------------------------------
METHOD_FNS = {
    "SNaive": forecast_snaive,
    "Theta": forecast_theta,
    "SES": forecast_ses,
    "ETS": forecast_ets,
    "RWD": forecast_rwd,
    "ARIMA": forecast_arima,
}


def forecast_series(series, method, arima_grid=None):
    """Forecast a single Series object for its own horizon.

    Returns np.ndarray of length series.horizon (or None on hard failure).
    """
    s_period = _SEASONAL[series.frequency]
    values = np.asarray(series.values, dtype=float)
    H = series.horizon
    try:
        if method == "SNaive":
            return forecast_snaive(values, H, s_period)
        if method == "Theta":
            return forecast_theta(values, H, s_period)
        if method == "SES":
            return forecast_ses(values, H, s_period)
        if method == "ETS":
            return forecast_ets(values, H, s_period)
        if method == "RWD":
            return forecast_rwd(values, H, s_period)
        if method == "ARIMA":
            return forecast_arima(values, H, grid=arima_grid,
                                  max_obs=config.ARIMA_MAX_OBS)
    except Exception:
        return None
    raise ValueError(f"unknown method {method}")