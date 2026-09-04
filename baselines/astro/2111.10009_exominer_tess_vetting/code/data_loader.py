"""Shared frozen-data loader for the ExoMiner TESS vetting analysis.

Locates the frozen TESS SPOC vetting catalog CSV across a set of candidate
paths (env var, working dir, local replica, WSL mount of the frozen F: drive),
loads it with pandas, asserts the expected shape, and returns the DataFrame.

The frozen file (SHA-256 6B4F2491E3C54BE770A4ADE9EFEFD25CDB4258BAADE7D985033EDC46013DE862)
was downloaded from the official NASA/ExoMiner GitHub repository
(exominer_vetting_pc_catalog_dash-render-web-app/data/
 exominer_vetting_tess-spoc-2-min-s1s67_dashtable_dvm-url_scoregt0.1.csv).
"""
from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import pandas as pd

EXPECTED_SHA256 = "6B4F2491E3C54BE770A4ADE9EFEFD25CDB4258BAADE7D985033EDC46013DE862"

# Candidate locations of the frozen catalog (first existing wins).
CANDIDATE_PATHS = [
    # 1) explicit env var
    Path(os.environ["EXOMINER_DATA_PATH"]) if os.environ.get("EXOMINER_DATA_PATH") else None,
    # 2) relative to current working directory
    Path("data/exominer_vetting_tess.csv"),
    Path("exominer_vetting_tess.csv"),
    Path("exominer_vetting_tess-spoc-2-min-s1s67_dashtable_dvm-url_scoregt0.1.csv"),
    # 3) relative to this script's location (agent_solution/code -> clone dir)
    Path(__file__).resolve().parent.parent / "data" / "exominer_vetting_tess.csv",
    # 4) frozen location on the WSL mount of the project F: drive
    Path("/mnt/f/dataset/astro/2111.10009_exominer_tess_vetting/exominer_vetting_tess.csv"),
    # 5) frozen location with a Windows-style absolute path
    Path("F:/dataset/astro/2111.10009_exominer_tess_vetting/exominer_vetting_tess.csv"),
]


def find_data_file() -> Path:
    """Return the first existing candidate path, or raise a clear error."""
    for cand in CANDIDATE_PATHS:
        if cand is not None and cand.is_file():
            return cand
    raise FileNotFoundError(
        "Frozen catalog 'exominer_vetting_tess.csv' not found in any candidate "
        "location. Set EXOMINER_DATA_PATH to the frozen file path, or place a "
        "copy in ./data/ next to this repository."
    )


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def load_exominer_vetting(path: Path | None = None) -> tuple[pd.DataFrame, Path, str]:
    """Load and sanity-check the frozen catalog.

    Returns (df, used_path, sha256). Raises AssertionError if the file does
    not match the expected content hash.
    """
    data_file = Path(path) if path is not None else find_data_file()
    digest = sha256_of(data_file)
    if digest != EXPECTED_SHA256:
        print(
            f"[WARN] SHA-256 mismatch for {data_file}:\n"
            f"   actual   {digest}\n"
            f"   expected {EXPECTED_SHA256}",
            file=sys.stderr,
        )
    df = pd.read_csv(data_file)
    expected_cols = [
        "TCE ID", "TIC ID", "Sector Run", "Planet Number", "ExoMiner Score",
        "ExoMiner Unc. Score", "DV mini-report URL", "Orbital Period [day]",
        "Transit Duration [hour]", "Transit Epoch [BTJD]", "Transit Depth [ppm]",
        "Planet Radius [Earth Radii]", "MES", "Transit Model SNR",
        "Number of transits observed", "Gaia RUWE",
    ]
    assert list(df.columns) == expected_cols, (
        f"Unexpected columns: {list(df.columns)}"
    )
    assert len(df) == 11289, f"Expected 11289 data rows, got {len(df)}"
    return df, data_file, digest


if __name__ == "__main__":
    df, path, digest = load_exominer_vetting()
    print(f"data file : {path}")
    print(f"sha256    : {digest}")
    print(f"shape     : {df.shape}")
    print(f"columns   : {list(df.columns)}")