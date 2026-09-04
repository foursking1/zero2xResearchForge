"""Reader for Monash `.tsf` time-series files plus frozen-data validation.

The format is:

    # comment lines
    @relation ...
    @attribute series_name string
    @attribute start_timestamp date
    @frequency monthly|quarterly|yearly
    @horizon N
    @missing false
    @equallength false
    @data
    <series_name>:<start_timestamp>:<v1>,<v2>,...   (one line per series)

All series are used in *full*; the last ``@horizon`` observations of every
series are the test segment.  Train/validation never touch those observations.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass

import numpy as np

import config

FILES = {
    "M3": {
        "monthly": "m3_monthly_dataset.tsf",
        "quarterly": "m3_quarterly_dataset.tsf",
        "yearly": "m3_yearly_dataset.tsf",
    },
    "Tourism": {
        "monthly": "tourism_monthly_dataset.tsf",
        "quarterly": "tourism_quarterly_dataset.tsf",
        "yearly": "tourism_yearly_dataset.tsf",
    },
}


@dataclass
class Series:
    name: str
    dataset: str
    frequency: str
    horizon: int
    values: np.ndarray


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def locate_tsf_dir() -> str:
    for cand in config.TSF_DIR_CANDIDATES:
        if cand and os.path.isdir(cand):
            present = {f
                       for f in os.listdir(cand)
                       if f.endswith(".tsf")}
            expected = set(sum([list(v.values()) for v in FILES.values()], []))
            if present >= expected:
                return cand
    raise FileNotFoundError(
        "Frozen data directory not found among " + ", ".join(config.TSF_DIR_CANDIDATES)
    )


def parse_tsf(path: str) -> tuple[dict, dict]:
    """Return (metadata, {series_name: [values]})."""
    freq, horizon = None, None
    series = {}
    in_data = False
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("@data"):
                in_data = True
                continue
            if line.startswith("@"):
                key, _, value = line[1:].partition(" ")
                if key == "frequency":
                    freq = value.strip()
                elif key == "horizon":
                    horizon = int(value.strip())
                continue
            if not in_data or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            name, rest = line.split(":", 1)
            _, _, vals = rest.partition(":")
            values = np.array([float(v) for v in vals.split(",") if v.strip()])
            series[name] = values
    meta = {"frequency": freq, "horizon": horizon}
    return meta, series


def load_data(check_manifest: bool = True) -> tuple[list[Series], dict]:
    """Load all 6 frozen files and validate the basic data facts.

    Returns
    -------
    series_list : list[Series]
    metadata : dict  (per dataset/frequency: frequency, horizon, n_series)
    """
    tsf_dir = locate_tsf_dir()
    series_list = []
    metadata = {}

    if check_manifest and os.path.exists(config.MANIFEST_FILE):
        with open(config.MANIFEST_FILE) as fh:
            manifest = json.load(fh)
        for fobj in manifest["files"]:
            p = os.path.join(tsf_dir, os.path.basename(fobj["file"]))
            actual = _sha256(p)
            if actual != fobj["sha256"]:
                raise RuntimeError(
                    f"sha256 mismatch for {fobj['file']}: {actual} != {fobj['sha256']}"
                )
        print(f"[data] manifest sha256 OK for all {len(manifest['files'])} files")

    for dataset in config.DATASETS:
        for freq in config.FREQUENCIES:
            fname = FILES[dataset][freq]
            path = os.path.join(tsf_dir, fname)
            meta, series = parse_tsf(path)
            if meta["frequency"] != freq:
                raise RuntimeError(f"frequency mismatch in {fname}")
            if meta["horizon"] is None:
                raise RuntimeError(f"missing @horizon in {fname}")
            for name, values in series.items():
                series_list.append(Series(
                    name=name, dataset=dataset, frequency=freq,
                    horizon=int(meta["horizon"]), values=values,
                ))
            metadata[(dataset, freq)] = dict(
                frequency=freq, horizon=int(meta["horizon"]),
                n=len(series), min_len=int(min(len(v) for v in series.values())),
            )
    return series_list, metadata


def validate_protocol(series_list: list[Series]) -> dict:
    """Validate A1 data facts: per-file counts, every series length >= horizon."""
    report = {}
    for ds in config.DATASETS:
        for fr in config.FREQUENCIES:
            sub = [s for s in series_list if s.dataset == ds and s.frequency == fr]
            short = [s.name for s in sub if len(s.values) < s.horizon]
            report[(ds, fr)] = {
                "n_series": len(sub),
                "horizon": sub[0].horizon if sub else None,
                "n_short_series": len(short),
                "short_series": short[:5],
            }
    return report


def split_train_test(s: Series):
    """Test = last `s.horizon` observations; the rest is training data."""
    return s.values[: -s.horizon], s.values[-s.horizon :]


if __name__ == "__main__":
    ss, meta = load_data()
    rep = validate_protocol(ss)
    print(f"total series: {len(ss)}")
    for k in sorted(rep, key=str):
        v = rep[k]
        print(f"  {k[0]:8s} {k[1]:10s} n={v['n_series']:5d} H={v['horizon']} "
              f"short={v['n_short_series']}")
    print("\nper-file metadata:")
    for k, v in sorted(meta.items(), key=str):
        print(f"  {k} -> {v}")