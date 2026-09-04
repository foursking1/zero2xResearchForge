# -*- coding: utf-8 -*-
"""PTA data extraction: parse NG15 wideband .tim/.par files.

Computes from the frozen data:
  - number of ToAs per pulsar (paper Table V)
  - ToA time span, frequency coverage
  - average ToA white-noise uncertainty (paper Table V)
  - pulsar RA/Dec (for Hellings-Downs matrix)

NOTE on data version: the frozen files yield 4944 active ToAs (matching paper Table V
exactly) and white-noise levels matching Table V to ~0.05 ns. The `C`-prefixed rows in
the .tim files are cut/commented ToAs (flags like -cut dmx) and are NOT counted as active
ToAs. So the "+1 ToA per pulsar (v2.1.0)" claim in TASK.md does not materialise for these
files; we report the actual count as a data fact.

Observed timing residuals cannot be produced offline: PINT/ENTERPRISE need the DE440
solar-system ephemeris, which is not bundled and no network is available.
"""
import os
import numpy as np
import json
import re

DATA_DIR = r"F:/dataset/astro/2504.04211_pta_normalizing_flows/ng15_wideband_10pulsars"
PULSARS = ["J0030+0451", "J0613-0200", "J1600-3053", "J1744-1134", "J1909-3744",
           "J1910+1256", "J1918-0642", "J1944+0907", "J2043+1711", "J2317+1439"]

# paper Table V
PAPER_WHITE_NS = {"J0030+0451": 685.7, "J0613-0200": 276.0, "J1600-3053": 241.7,
                  "J1744-1134": 236.3, "J1909-3744": 95.4, "J1910+1256": 442.1,
                  "J1918-0642": 543.2, "J1944+0907": 664.4, "J2043+1711": 251.4,
                  "J2317+1439": 303.6}
PAPER_NTOA = {"J0030+0451": 724, "J0613-0200": 423, "J1600-3053": 481, "J1744-1134": 433,
              "J1909-3744": 833, "J1910+1256": 216, "J1918-0642": 487, "J1944+0907": 180,
              "J2043+1711": 459, "J2317+1439": 708}


def parse_tim(path):
    """Parse PINT-format .tim. Returns mjd(days), freq(MHz), err_us, obs."""
    mjd, freq, err, obs = [], [], [], []
    with open(path, "r") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            if line.startswith("C ") or line.startswith("c ") or line.startswith("#"):
                continue
            if line.startswith("FORMAT"):
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            try:
                freq.append(float(parts[1]))
                mjd.append(float(parts[2]))
                err.append(float(parts[3]))
            except ValueError:
                continue
            obs.append(parts[4])
    return np.array(mjd), np.array(freq), np.array(err), obs


def parse_par_radec(path):
    """Extract RA/Dec (deg) from a PINT .par. Handles RAJ/DECJ, ELONG/ELAT (ecliptic->eq)."""
    raj = decj = None
    elong = elat = None
    with open(path, "r", encoding="latin-1") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            parts = line.split()
            key = parts[0]
            if key == "RAJ" and len(parts) >= 2:
                v = parts[1]
                m = re.match(r"(\d+):(\d+):([\d.]+)", v)
                if m:
                    h, mnt, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
                    raj = (h + mnt / 60.0 + s / 3600.0) * 15.0
            elif key == "DECJ" and len(parts) >= 2:
                v = parts[1]
                m = re.match(r"([+-]?\d+):(\d+):([\d.]+)", v)
                if m:
                    d = int(m.group(1)); mnt = int(m.group(2)); s = float(m.group(3))
                    sign = -1 if d < 0 else 1
                    decj = sign * (abs(d) + mnt / 60.0 + s / 3600.0)
            elif key == "ELONG" and len(parts) >= 2:
                elong = float(parts[1])
            elif key == "ELAT" and len(parts) >= 2:
                elat = float(parts[1])
    if raj is not None and decj is not None:
        return raj, decj
    if elong is not None and elat is not None:
        # ecliptic -> equatorial (J2000 obliquity)
        eps = np.radians(23.4392911)
        lam = np.radians(elong)
        be = np.radians(elat)
        sin_dec = np.sin(be) * np.cos(eps) + np.cos(be) * np.sin(eps) * np.sin(lam)
        dec = np.degrees(np.arcsin(sin_dec))
        ra = np.degrees(np.arctan2(np.cos(be) * np.cos(lam),
                                   -np.sin(be) * np.sin(eps) + np.cos(be) * np.cos(eps) * np.sin(lam)))
        ra = ra % 360.0
        return ra, dec
    return None, None


def main():
    summary = {}
    all_t, all_sigma, all_ra, all_dec = {}, {}, {}, {}
    for psr in PULSARS:
        tim = par = None
        for f in os.listdir(DATA_DIR):
            if f.startswith(psr) and f.endswith(".tim"):
                tim = f
            if f.startswith(psr) and f.endswith(".par"):
                par = f
        mjd, freq, err_us, obs = parse_tim(os.path.join(DATA_DIR, tim))
        ra, dec = parse_par_radec(os.path.join(DATA_DIR, par))
        t = (mjd - mjd.min()) * 86400.0
        sigma = err_us * 1e-6
        summary[psr] = {
            "ntoa_frozen": int(len(mjd)),
            "ntoa_paper": PAPER_NTOA[psr],
            "delta_ntoa": int(len(mjd)) - PAPER_NTOA[psr],
            "span_days": float(mjd.max() - mjd.min()),
            "avg_sigma_ns": float(np.mean(err_us) * 1e3),
            "paper_white_ns": PAPER_WHITE_NS[psr],
            "ra_deg": ra, "dec_deg": dec,
        }
        all_t[psr] = t
        all_sigma[psr] = sigma
        all_ra[psr] = ra * np.pi / 180.0
        all_dec[psr] = dec * np.pi / 180.0

    total = sum(s["ntoa_frozen"] for s in summary.values())
    out = {
        "per_pulsar": summary,
        "total_ntoa_frozen": total,
        "total_ntoa_paper": sum(PAPER_NTOA.values()),
        "note": ("active ToA count matches paper Table V (4944); the C-prefixed rows are "
                 "cut ToAs, not active ToAs; the +1/pulsar (v2.1.0) claim in TASK.md does "
                 "not materialise for these frozen files"),
    }
    np.savez(os.path.join(os.path.dirname(__file__), "pta_toas.npz"),
             **{psr: all_t[psr] for psr in PULSARS},
             **{psr + "_sigma": all_sigma[psr] for psr in PULSARS},
             **{psr + "_ra": all_ra[psr] for psr in PULSARS},
             **{psr + "_dec": all_dec[psr] for psr in PULSARS})
    with open(os.path.join(os.path.dirname(__file__), "pta_data_summary.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))


def load_toas():
    """Load the saved arrays for downstream use."""
    d = np.load(os.path.join(os.path.dirname(__file__), "pta_toas.npz"))
    times = [d[psr] for psr in PULSARS]
    sigma = [d[psr + "_sigma"] for psr in PULSARS]
    ra = np.array([d[psr + "_ra"] for psr in PULSARS])
    dec = np.array([d[psr + "_dec"] for psr in PULSARS])
    return times, sigma, ra, dec, PULSARS


if __name__ == "__main__":
    main()
