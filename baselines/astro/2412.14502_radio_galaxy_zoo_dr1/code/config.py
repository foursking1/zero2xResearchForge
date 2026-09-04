"""Shared configuration for the RGZ DR1 verification scripts.

Resolves the location of the frozen official RGZ DR1 csv files so that the
judge / reviewer can point the scripts at any mirror of the frozen data
without editing the code.

Resolution order:
  1. positional --data-dir argument (when parsed by the caller)
  2. environment variable RGZ_DATA_DIR
  3. known defaults (Linux / WSL and Windows paths)
"""

import os
from pathlib import Path

FILES = {
    "FIRST_class": "DR1_FIRST_radio_classifications.csv",
    "FIRST_host": "DR1_FIRST_host_properties.csv",
    "ATLAS_class": "DR1_ATLAS_radio_classifications.csv",
    "ATLAS_host": "DR1_ATLAS_host_properties.csv",
}

DEFAULT_CANDIDATES = [
    "/mnt/f/dataset/astro/2412.14502_radio_galaxy_zoo_dr1",
    "F:\\dataset\\astro\\2412.14502_radio_galaxy_zoo_dr1",
]


def resolve_data_dir(explicit=None):
    if explicit:
        return Path(explicit)
    env = os.environ.get("RGZ_DATA_DIR")
    if env:
        return Path(env)
    for cand in DEFAULT_CANDIDATES:
        p = Path(cand)
        if p.is_dir() and all((p / f).is_file() for f in FILES.values()):
            return p
    raise FileNotFoundError(
        "Could not locate the frozen RGZ DR1 data directory. Set RGZ_DATA_DIR "
        "or pass --data-dir pointing to the directory containing the 4 CSV files."
    )


def resolve_files(data_dir):
    d = Path(data_dir)
    return {key: d / name for key, name in FILES.items()}