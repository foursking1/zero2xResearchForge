"""Global configuration for the multi-view forecasting evaluation.

Task: 2406.16590_beyond_avg_forecast
Paper anchor: Cerqueira et al. (2024) "Forecasting with Deep Learning: Beyond
Average of Average of Average Performance" (arXiv:2406.16590).

All horizons are read from the frozen `.tsf` file headers (``@horizon``), as
mandated by TASK.md ("H 见各文件 @horizon").
"""

import os

# ---------------------------------------------------------------------------
# Data locations (frozen package). The loader tries these in order so the code
# is runnable both inside the task folder and from the frozen-dataset location.
# ---------------------------------------------------------------------------
TSF_DIR_CANDIDATES = [
    "/mnt/f/dataset/cs/2406.16590_beyond_avg_forecast/tsf",  # frozen location
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "tsf"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tsf"),
]

# Keep the frozen manifest's sha256 for a self-check.
MANIFEST_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data", "source_manifest.json"
)

# ---------------------------------------------------------------------------
# Datasets / frequencies
# ---------------------------------------------------------------------------
DATASETS = ["M3", "Tourism"]
FREQUENCIES = ["monthly", "quarterly", "yearly"]

SEASONAL_PERIODS = {"monthly": 12, "quarterly": 4, "yearly": 1}

# ---------------------------------------------------------------------------
# Evaluation protocol
# ---------------------------------------------------------------------------
NAMESPACE = "NS"              # group by dataset for attribution in smape agg
# Definition of condition thresholds (fixed, declared openly, leak-free).
COND_DIFFICULT_QUANTILE = 0.95   # difficult series: SNaive per-series SMAPE > 95% quantile
COND_ANOMALY_CI = 0.99           # anomaly points: |obs - SNaive forecast| outside 99% CI

# ---------------------------------------------------------------------------
# Deep model (global, one model per sampling frequency)
# ---------------------------------------------------------------------------
NHITS_CFG = {
    "monthly": dict(input_window=32, output_horizon=24, n_stacks=2, n_blocks_per_stack=2,
                    width=64, n_pool_kernel_size=2),
    "quarterly": dict(input_window=12, output_horizon=8, n_stacks=2, n_blocks_per_stack=2,
                      width=64, n_pool_kernel_size=2),
    "yearly": dict(input_window=8, output_horizon=6, n_stacks=2, n_blocks_per_stack=2,
                   width=64, n_pool_kernel_size=2),
}
NHITS_TRAIN_CFG = dict(
    batch_size=256,
    epochs=50,
    lr=1e-3,
    weight_decay=1e-4,
    val_fraction=0.1,
    max_windows_per_series=200,   # cap the number of windows per series
    patience=8,
    seed=42,
)

# ---------------------------------------------------------------------------
# Classical forecasters
# ---------------------------------------------------------------------------
CLASSICAL_METHODS = ["SNaive", "Theta", "SES", "ETS", "RWD", "ARIMA"]

ARIMA_GRID = [(0, 1, 1), (1, 1, 1)]   # concise drift-enabled grid (light, robust)
ARIMA_MAX_OBS = 300      # speed: fit on the most recent observations
ARIMA_WORKERS = 8

# ---------------------------------------------------------------------------
# Randomness
# ---------------------------------------------------------------------------
SEED = 42