"""Configuration and constants for the XRD classification reproduction.

Task: 1811.08425_small_xrd_classification
Paper: Oviedo et al., npj Comput. Mater. 5, 60 (2019); arXiv:1811.08425
"""

import os

# ---------------------------------------------------------------------------
# Data locations (frozen data).  Resolution order:
#   1. env var XRD_DATA_DIR
#   2. F: dataset location (physical location of the frozen data, see
#      data/DATA_LOCATION.md in the task directory)
#   3. local ../data
# ---------------------------------------------------------------------------
_F_DRIVE = "/mnt/f/dataset/materials/1811.08425_small_xrd_classification"
_LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def _find_data_dir():
    env = os.environ.get("XRD_DATA_DIR")
    if env and os.path.exists(os.path.join(env, "exp.csv")):
        return env
    for cand in (_F_DRIVE, _LOCAL):
        if os.path.exists(os.path.join(cand, "exp.csv")):
            return cand
    raise FileNotFoundError(
        "Could not locate frozen data/exp.csv. Set XRD_DATA_DIR."
    )


DATA_DIR = _find_data_dir()
EXPERIMENTAL_DIR = os.path.join(DATA_DIR, "Experimental")

# File names
EXP_CSV = os.path.join(DATA_DIR, "exp.csv")
LABEL_EXP_CSV = os.path.join(DATA_DIR, "label_exp.csv")
ENCODING_CSV = os.path.join(DATA_DIR, "encoding.csv")
THEOR_CSV = os.path.join(DATA_DIR, "theor.csv")
LABEL_THEO_CSV = os.path.join(DATA_DIR, "label_theo.csv")

# Space-group encoding: 0..6 -> space group name
SG_ENCODING = ["Fm-3m", "I41mcm", "P21a", "P3m1", "P61mmc", "Pc", "Pm-3m"]
NUM_CLASSES = len(SG_ENCODING)

# ---------------------------------------------------------------------------
# Physical grid
# ---------------------------------------------------------------------------
# Experimental grid (exp.csv): 2theta 10.04 .. 69.96 step 0.04 (1499 points)
EXP_TW_MIN, EXP_TW_MAX, EXP_STEP = 10.04, 69.96, 0.04
# Theoretical grid (theor.csv): 2theta 5.04 .. 89.96 step 0.04 (2125 points)
THEO_TW_MIN, THEO_TW_MAX = 5.04, 89.96

# ---------------------------------------------------------------------------
# Random seeds (fixed, following the paper's shuffle-with-fixed-seed protocol)
# ---------------------------------------------------------------------------
SEED = 42            # master seed
CV_SEED = 20240813   # seed for the 5-fold split (fixed)
AUG_SEED = 7         # seed for augmentation

# ---------------------------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------------------------
SMOOTH_WINDOW = 15   # Savitzky-Golay window length
SMOOTH_ORDER = 3     # Savitzky-Golay polynomial order
BG_FILTER = 401      # moving-minimum window (odd) for background estimation

# ---------------------------------------------------------------------------
# a-CNN (paper Sec III, "All Convolutional Neural Network")
#   3 x Conv1D(32 filters) + ReLU + Global Average Pooling + Dense/Softmax
# ---------------------------------------------------------------------------
CONV_FILTERS = 32
KERNELS = [8, 5, 3]      # kernel sizes of the 3 conv layers
STRIDES = [8, 5, 3]      # strides (all-convolutional downsampling)
ACTIVATION = "relu"
POOL = "gap"             # global average pooling
LOSS = "bce"             # binary cross-entropy per output (paper)
OPTIMIZER = "adam"
BATCH_SIZE = 128
EPOCHS_MAX = 120
EARLY_STOP_PATIENCE = 15
LR = 1e-3

# ---------------------------------------------------------------------------
# Data augmentation (paper Eqs. 1-3)
# ---------------------------------------------------------------------------
AUG_N_SIM = 2000     # augmented spectra generated from the simulated set
AUG_N_EXP = 2000     # augmented spectra generated from the experimental set

# Peak scaling (Eq. 1)
SCALE_C_LO, SCALE_C_HI = 0.5, 1.5   # peak intensity scaling factor range
SCALE_PERIOD = 4                   # periodic subset: every n-th peak
SCALE_FRAC = 0.5                   # max fraction of selected peaks

# Peak removal (Eq. 2)
REMOVE_PERIOD = 4
REMOVE_FRAC = 0.3

# Pattern shift (Eq. 3)
SHIFT_MAX_DEG = 0.1                # max shift along 2theta (deg)

# Fraction of transformed spectra (rest are copies of originals)
AUG_MIX_RATIO = 0.75

# ---------------------------------------------------------------------------
# Output locations
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
FIGURES_DIR = os.path.join(BASE_DIR, "figures")
EVIDENCE_DIR = os.path.join(BASE_DIR, "evidence")

for _d in (RESULTS_DIR, FIGURES_DIR, EVIDENCE_DIR):
    os.makedirs(_d, exist_ok=True)
