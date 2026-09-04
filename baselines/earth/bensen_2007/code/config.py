# -*- coding: utf-8 -*-
"""
Shared configuration and data paths for the bensen_2007 reproduction.

All data is read IN PLACE from the frozen dataset (no copying).
"""
import os

# ---------------------------------------------------------------- data paths
DATA_ROOT = r"E:\scisolvebench-data\asset-data\datasets-v1\v1\bensen_2007"
BUNDLE = os.path.join(DATA_ROOT, "real_data_candidates", "seismic_waveform_subset_v1")

FILES_DIR = os.path.join(BUNDLE, "files")
XCORR_MSEED = os.path.join(FILES_DIR, "12mo_2004_sym.mseed")
IRIS_MANIFEST = os.path.join(FILES_DIR, "iris_manifest.csv")
STATIONS_XML = os.path.join(FILES_DIR, "stations_priority12.xml")

EARTHQUAKE_DIR = os.path.join(BUNDLE, "directories", "earthquake_records")
EARTHQUAKE_FILES = {
    "BK.CMB":  {"BHZ": os.path.join(EARTHQUAKE_DIR, "BK.CMB.BHZ.mseed"),
                "LHZ": os.path.join(EARTHQUAKE_DIR, "BK.CMB.LHZ.mseed")},
    "CI.TIN":  {"BHZ": os.path.join(EARTHQUAKE_DIR, "CI.TIN.BHZ.mseed"),
                "LHZ": os.path.join(EARTHQUAKE_DIR, "CI.TIN.LHZ.mseed")},
    "CN.LLLB": {"BHZ": os.path.join(EARTHQUAKE_DIR, "CN.LLLB.BHZ.mseed")},
    "IU.HKT":  {"BHZ": os.path.join(EARTHQUAKE_DIR, "IU.HKT.BHZ.mseed"),
                "LHZ": os.path.join(EARTHQUAKE_DIR, "IU.HKT.LHZ.mseed")},
    "NM.UALR": {"BHZ": os.path.join(EARTHQUAKE_DIR, "NM.UALR.BHZ.mseed"),
                "LHZ": os.path.join(EARTHQUAKE_DIR, "NM.UALR.LHZ.mseed")},
}

# ---------------------------------------------------------------- outputs
AGENT_SOLUTION = r"D:\project\paper-bench\tasks_legacy\bensen_2007\agent_solution"
RESULTS_DIR = os.path.join(AGENT_SOLUTION, "results")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")
CODE_DIR = os.path.join(AGENT_SOLUTION, "code")

for d in (RESULTS_DIR, FIGURES_DIR, CODE_DIR):
    os.makedirs(d, exist_ok=True)

# ---------------------------------------------------------------- science constants
# Great-circle distance HRV-PFO (computed from station coordinates below)
# IU.HRV = (42.5064, -71.5583)  ; II.PFO = (33.6092, -116.4553)
STATION_COORDS = {
    "IU.ANMO": (34.94591, -106.4572),
    "IU.HRV":  (42.5064, -71.5583),
    "II.PFO":  (33.6092, -116.4553),
    "IU.CCM":  (38.0557, -91.2446),
    "IU.SSPA": (40.6358, -77.8876),
}

# Six passbands used in the paper (Bensen et al. 2007, fig. 4)
PASSBANDS = {
    "7-150s":  (7.0, 150.0),
    "7-25s":   (7.0, 25.0),
    "20-50s":  (20.0, 50.0),
    "33-67s":  (33.0, 67.0),
    "50-100s": (50.0, 100.0),
    "70-150s": (70.0, 150.0),
}

# Paper reference values (CITE as paper values, not computed)
PAPER_REF = {
    "powerlaw_n_10s": 2.55,
    "powerlaw_n_25s": 2.88,
    "powerlaw_n_50s": 3.40,
    "powerlaw_n_100s": 2.66,
}
