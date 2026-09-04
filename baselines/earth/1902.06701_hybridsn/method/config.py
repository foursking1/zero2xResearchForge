"""Shared configuration for the 1902.06701 HybridSN reproduction."""
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
SPLIT_DIR = os.path.join(RESULTS_DIR, 'splits')

# Paper protocol (Roy et al. 2020): 30% training / 70% testing on labeled pixels.
TRAIN_RATIO = 0.3
SEEDS = [0, 1, 2]

# Data preprocessing
N_PCA_BANDS = 30          # spectral bands kept after PCA (paper uses 30)
WINDOW = 25               # spatial patch size 25x25 (paper: Table IV 25->99.75)

# Training
BATCH_SIZE = 16
LR = 5e-4
WEIGHT_DECAY = 1e-5
EPOCHS = 100
DROPOUT = 0.5
SEED = 0

DEVICE = os.environ.get('DEVICE', 'cpu')  # 'cpu' preferred; 'cuda' if free memory confirmed