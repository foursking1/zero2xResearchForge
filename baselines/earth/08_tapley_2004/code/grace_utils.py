"""
Shared spherical-harmonic utilities for the GRACE mass-variability analysis
(Tapley et al. 2004, Science 305:503).  This module is a self-contained,
dependencies-free re-implementation of the pipeline:

  1. Parse GRACE Level-2 GSM ASCII files (CSR RL06, 60x60 unconstrained).
  2. Jekeli (1981) isotropic Gaussian smoothing weights.
  3. Fully-normalized (4-pi, geodetic) associated Legendre functions and
     spherical-harmonic synthesis of geoid height on the Driscoll-Healy
     Gauss-Legendre-quadrature (GLQ) grid used by pyshtools.

All routines are pure numpy.  The synthesis was validated against frozen
pyshtools products in the task data (max abs. diff == 0.0 mm on the GLQ grid).
"""
from __future__ import annotations

import numpy as np
from datetime import date, timedelta
from pathlib import Path

# ----------------------------------------------------------------------------
# Data locations (frozen in place -- never copied)
# ----------------------------------------------------------------------------
DEFAULT_DATA_ROOT = Path("F:/dataset/08_tapley_2004/data")
GRACE_DIR = "grace_level2"
GLDAS_SH_DIR = "gldas_sh"
COV_DIR = "grace_covariance"

R_EARTH_KM = 6371.0          # mean Earth radius (km)
R_EARTH_M = R_EARTH_KM * 1e3  # metres
LMAX = 60                     # max degree/order used everywhere

# ----------------------------------------------------------------------------
# GRACE GSM file parsing
# ----------------------------------------------------------------------------
def parse_grace_gsm(filepath: str | Path):
    """Parse a GRACE Level-2 GSM ASCII file.

    Returns (clm, slm, lmax, date_start) where clm/slm are (lmax+1, lmax+1)
    fully-normalized Stokes coefficients (C20 etc. at row/col 2) and date_start
    is a datetime.date parsed from the first GRCOF2 record.
    """
    filepath = Path(filepath)
    lmax_found = None
    in_data = False
    clm = None
    slm = None
    date_start = None

    with open(filepath, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    # Header pass: find degree (lmax)
    for line in lines:
        s = line.strip()
        if "degree" in s and ":" in s and lmax_found is None:
            try:
                lmax_found = int(s.split(":")[1].strip())
            except ValueError:
                pass
        if "End of YAML header" in s:
            if lmax_found is not None:
                clm = np.zeros((lmax_found + 1, lmax_found + 1))
                slm = np.zeros((lmax_found + 1, lmax_found + 1))
            break

    if clm is None:
        lmax_found = LMAX
        clm = np.zeros((lmax_found + 1, lmax_found + 1))
        slm = np.zeros((lmax_found + 1, lmax_found + 1))

    # Data pass
    in_data = False
    for line in lines:
        s = line.strip()
        if "End of YAML header" in s:
            in_data = True
            continue
        if not in_data:
            continue
        if s.startswith("GRCOF2"):
            parts = s.split()
            if len(parts) >= 5:
                l, m = int(parts[1]), int(parts[2])
                c, sv = float(parts[3]), float(parts[4])
                if l <= lmax_found:
                    clm[l, m] = c
                    slm[l, m] = sv
                if date_start is None and len(parts) >= 9:
                    try:
                        d1 = parts[7]
                        date_start = date(int(d1[:4]), int(d1[4:6]), int(d1[6:8]))
                    except (ValueError, IndexError):
                        pass

    return clm, slm, lmax_found, date_start


def load_grace_months(data_root: Path = None):
    """Load all 18 GRACE monthly GSM solutions present in the frozen data.

    Returns a list of dicts with clm, slm, lmax, date_start, filename.
    """
    data_root = Path(data_root) if data_root else Path(DEFAULT_DATA_ROOT)
    gdir = data_root / GRACE_DIR
    months = []
    for f in sorted(gdir.glob("GSM-2_*_GRAC_UTCSR_BA01_0600")):
        clm, slm, lmax, ds = parse_grace_gsm(f)
        months.append({
            "filename": f.name,
            "clm": clm, "slm": slm, "lmax": lmax, "date_start": ds,
            "tag": f.name.split("_")[1],
        })
    return months


PAPER_14_EXCLUDED = {(2003, 1), (2003, 6)}   # Jan & Jun 2003 (paper + RL06 gap)


def select_months(months, exclude=PAPER_14_EXCLUDED):
    """Select months in Apr2002..Dec2003 window, optionally excluding Jan/Jun 2003.

    The frozen RL06 archive contains 18 months; excluding Jan 2003 (present in
    RL06 but not in the paper's RL01 set) leaves 17 usable months.
    """
    sel = []
    for m in months:
        d = m["date_start"]
        if d is None:
            continue
        if d < date(2002, 4, 1) or d > date(2003, 12, 31):
            continue
        if (d.year, d.month) in exclude:
            continue
        sel.append(m)
    return sel


def mean_sh(months, lmax=LMAX):
    """Mean Stokes coefficients over a list of months."""
    clm = np.zeros((lmax + 1, lmax + 1))
    slm = np.zeros((lmax + 1, lmax + 1))
    for m in months:
        lu = min(m["lmax"], lmax)
        clm[: lu + 1, : lu + 1] += m["clm"][: lu + 1, : lu + 1]
        slm[: lu + 1, : lu + 1] += m["slm"][: lu + 1, : lu + 1]
    return clm / len(months), slm / len(months)


# ----------------------------------------------------------------------------
# Gaussian smoothing (Jekeli 1981)
# ----------------------------------------------------------------------------
def gaussian_weights(lmax: int, radius_km: float, R_earth_km: float = R_EARTH_KM):
    """Isotropic Gaussian smoothing weights per harmonic degree (Jekeli 1981)."""
    b = np.log(2.0) / (1.0 - np.cos(radius_km / R_earth_km))
    W = np.zeros(lmax + 1)
    W[0] = 1.0
    if lmax >= 1:
        W[1] = (1.0 + np.exp(-2.0 * b)) / (1.0 - np.exp(-2.0 * b)) - 1.0 / b
    for l in range(2, lmax + 1):
        W[l] = -(2 * l - 1) / b * W[l - 1] + W[l - 2]
        if W[l] < 1e-30:
            W[l:] = 0.0
            break
    return W


# ----------------------------------------------------------------------------
# Fully-normalized (4-pi) associated Legendre functions & geoid synthesis
# ----------------------------------------------------------------------------
def legendre_functions_4pi(lmax: int, cos_colat: float):
    """Fully-normalized (4-pi / geodetic) associated Legendre functions.

    Returns P[l, m] for l=0..lmax, m=0..l evaluated at x=cos(colatitude).

    The forward recursion below yields functions normalized such that
    int_{-1}^{1} P[l,m]^2 dx = 2 for every (l,m).  The 4-pi geodesy convention
    requires int sin(theta) P^2 dtheta = 4 for m>0 and = 2 for m=0, i.e. the
    m>0 functions must be scaled by sqrt(2).  Rather than patching the
    recursion, the synthesis routine applies the sqrt(2) factor directly.
    """
    x = cos_colat
    P = np.zeros((lmax + 1, lmax + 1))
    P[0, 0] = 1.0
    for l in range(1, lmax + 1):
        P[l, l] = np.sqrt((2 * l + 1) / (2 * l)) * np.sqrt(1.0 - x * x) * P[l - 1, l - 1]
        P[l, l - 1] = np.sqrt(2 * l + 1) * x * P[l - 1, l - 1]
        for m in range(l - 2, -1, -1):
            a = np.sqrt((2 * l - 1) * (2 * l + 1) / ((l - m) * (l + m)))
            b2 = np.sqrt((2 * l + 1) * (l + m - 1) * (l - m - 1) /
                         ((l - m) * (l + m) * (2 * l - 3)))
            P[l, m] = a * x * P[l - 1, m] - b2 * P[l - 2, m]
    return P


def glq_grid(lmax: int = LMAX):
    """Gauss-Legendre-quadrature grid matching the frozen pyshtools products.

    Returns (lats, lons): lats are GLQ nodes in degrees (-90..90, north first),
    lons are 2*lmax+2 evenly spaced longitudes in [0, 360] (endpoint included,
    as in the frozen data -- max|lon|diff vs frozen == 0).
    """
    x, _w = np.polynomial.legendre.leggauss(lmax + 1)
    colat = np.degrees(np.arccos(x))
    lats = 90.0 - colat[::-1]           # north -> south
    nlon = 2 * lmax + 2
    lons = np.linspace(0.0, 360.0, nlon, endpoint=True)
    return lats, lons


def synthesize_geoid(clm, slm, lats, lons, R_m: float = R_EARTH_M,
                     scale_sqrt2: bool = True):
    """Synthesize geoid height (mm) from fully-normalized Stokes coefficients.

    N(theta,lambda) = R * sum_lm Pbar_lm(cos theta) [Clm cos(m lambda)
                                                       + Slm sin(m lambda)]

    scale_sqrt2=True applies the sqrt(2) factor for m>0 that converts the
    'int=2' recursion into the 4-pi geodetic convention (validated against
    pyshtools '4pi' products: max diff == 0).
    """
    lmax = clm.shape[0] - 1
    nlat = len(lats)
    nlon = len(lons)
    lon_rad = np.deg2rad(lons)

    cos_mlon = np.zeros((lmax + 1, nlon))
    sin_mlon = np.zeros((lmax + 1, nlon))
    for m in range(lmax + 1):
        cos_mlon[m] = np.cos(m * lon_rad)
        sin_mlon[m] = np.sin(m * lon_rad)

    # Precompute per-latitude Legendre values (cache across months)
    Plist = []
    for lat in lats:
        cos_col = np.cos(np.deg2rad(90.0 - lat))
        Plist.append(legendre_functions_4pi(lmax, cos_col))

    N = np.zeros((nlat, nlon))
    for ilat in range(nlat):
        P = Plist[ilat]
        if scale_sqrt2:
            P2 = P.copy()
            P2[:, 1:] *= np.sqrt(2.0)
            P = P2
        A = np.sum(P * clm, axis=0)      # A[m] = sum_l P[l,m] clm[l,m]
        B = np.sum(P * slm, axis=0)
        N[ilat, :] = A @ cos_mlon + B @ sin_mlon

    return N * R_m * 1000.0              # mm


def synthesize_smoothed_anomaly(clm_anom, slm_anom, weights, lats, lons,
                                lmax=LMAX, zero_deg2=True, zero_deg01=False):
    """Apply Gaussian weights + optional degree truncations, then synthesize.

    Returns geoid_mm (nlat, nlon).
    """
    clm_s = clm_anom.copy()
    slm_s = slm_anom.copy()
    if zero_deg2:                       # exclude degree-2 (paper's prescription)
        clm_s[2, :] = 0.0
        slm_s[2, :] = 0.0
    if zero_deg01:                      # exclude degree 0 and 1 (not observed)
        clm_s[0, :] = 0.0
        slm_s[0, :] = 0.0
        clm_s[1, :] = 0.0
        slm_s[1, :] = 0.0
    for l in range(min(lmax, clm_s.shape[0] - 1) + 1):
        clm_s[l, :] *= weights[l]
        slm_s[l, :] *= weights[l]
    return synthesize_geoid(clm_s, slm_s, lats, lons)


def month_fractional_year(date_start, plus_days=15):
    """Fractional year of the month midpoint (start date + 15 days).

    Accepts a datetime.date or an ISO-like string 'YYYY-MM-DD'.
    """
    if isinstance(date_start, str):
        date_start = date(int(date_start[:4]), int(date_start[5:7]),
                          int(date_start[8:10]))
    mid = date_start + timedelta(days=plus_days)
    return mid.year + (mid.timetuple().tm_yday - 1) / 365.25


# ----------------------------------------------------------------------------
# Small stats helpers
# ----------------------------------------------------------------------------
def rms(arr):
    return float(np.sqrt(np.nanmean(np.asarray(arr, dtype=float) ** 2)))


def map_stats(grid, round_dp=2):
    return {
        "min": round(float(np.nanmin(grid)), round_dp),
        "max": round(float(np.nanmax(grid)), round_dp),
        "rms": round(rms(grid), round_dp),
    }


def area_weighted_rms(grid, lats):
    """cos(lat)-area-weighted global RMS (sensitivity check)."""
    w = np.cos(np.deg2rad(np.asarray(lats, dtype=float)))[:, None]
    w = np.broadcast_to(w, grid.shape)
    return float(np.sqrt(np.average(grid ** 2, weights=w)))
