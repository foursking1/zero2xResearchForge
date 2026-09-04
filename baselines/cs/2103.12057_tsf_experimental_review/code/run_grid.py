"""Run a grid of (architecture, config) experiments and save all results.

Usage:  python3 run_grid.py grid.json  --out results/
(also sets TORCH_THREADS=4 by default for CPU efficiency)
"""
import argparse
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from experiment import run_config

DEFAULT_GRID = [
    # ---------- MLP ----------
    {"model": "mlp", "past_history": 22, "horizon": 18, "hidden_sizes": [64, 64], "batch_size": 1024, "lr": 0.001, "epochs": 10},
    {"model": "mlp", "past_history": 22, "horizon": 18, "hidden_sizes": [32, 64, 128], "batch_size": 1024, "lr": 0.001, "epochs": 10},
    {"model": "mlp", "past_history": 22, "horizon": 18, "hidden_sizes": [128, 128], "batch_size": 1024, "lr": 0.001, "epochs": 10},
    {"model": "mlp", "past_history": 22, "horizon": 18, "hidden_sizes": [256, 256], "batch_size": 1024, "lr": 0.001, "epochs": 10},
    {"model": "mlp", "past_history": 22, "horizon": 18, "hidden_sizes": [32, 64, 128, 64, 32], "batch_size": 1024, "lr": 0.001, "epochs": 10},
    {"model": "mlp", "past_history": 36, "horizon": 18, "hidden_sizes": [32, 64, 128], "batch_size": 1024, "lr": 0.001, "epochs": 10},
    {"model": "mlp", "past_history": 36, "horizon": 18, "hidden_sizes": [256, 256], "batch_size": 1024, "lr": 0.001, "epochs": 10},
    # ---------- GRU ----------
    {"model": "gru", "past_history": 22, "horizon": 18, "hidden": 32, "n_layers": 1, "dropout": 0.0, "batch_size": 512, "lr": 0.001, "epochs": 10},
    {"model": "gru", "past_history": 22, "horizon": 18, "hidden": 64, "n_layers": 1, "dropout": 0.0, "batch_size": 512, "lr": 0.001, "epochs": 10},
    {"model": "gru", "past_history": 22, "horizon": 18, "hidden": 128, "n_layers": 1, "dropout": 0.0, "batch_size": 512, "lr": 0.001, "epochs": 10},
    {"model": "gru", "past_history": 22, "horizon": 18, "hidden": 64, "n_layers": 2, "dropout": 0.0, "batch_size": 512, "lr": 0.001, "epochs": 10},
    {"model": "gru", "past_history": 22, "horizon": 18, "hidden": 128, "n_layers": 2, "dropout": 0.0, "batch_size": 512, "lr": 0.001, "epochs": 10},
    {"model": "gru", "past_history": 36, "horizon": 18, "hidden": 64, "n_layers": 1, "dropout": 0.0, "batch_size": 512, "lr": 0.001, "epochs": 10},
    {"model": "gru", "past_history": 36, "horizon": 18, "hidden": 128, "n_layers": 1, "dropout": 0.0, "batch_size": 512, "lr": 0.001, "epochs": 10},
    # ---------- LSTM ----------
    {"model": "lstm", "past_history": 22, "horizon": 18, "hidden": 32, "n_layers": 1, "dropout": 0.0, "batch_size": 512, "lr": 0.001, "epochs": 10},
    {"model": "lstm", "past_history": 22, "horizon": 18, "hidden": 64, "n_layers": 1, "dropout": 0.0, "batch_size": 512, "lr": 0.001, "epochs": 10},
    {"model": "lstm", "past_history": 22, "horizon": 18, "hidden": 128, "n_layers": 1, "dropout": 0.0, "batch_size": 512, "lr": 0.001, "epochs": 10},
    {"model": "lstm", "past_history": 22, "horizon": 18, "hidden": 64, "n_layers": 2, "dropout": 0.0, "batch_size": 512, "lr": 0.001, "epochs": 10},
    {"model": "lstm", "past_history": 22, "horizon": 18, "hidden": 128, "n_layers": 2, "dropout": 0.0, "batch_size": 512, "lr": 0.001, "epochs": 10},
    {"model": "lstm", "past_history": 36, "horizon": 18, "hidden": 64, "n_layers": 1, "dropout": 0.0, "batch_size": 512, "lr": 0.001, "epochs": 10},
    {"model": "lstm", "past_history": 36, "horizon": 18, "hidden": 128, "n_layers": 1, "dropout": 0.0, "batch_size": 512, "lr": 0.001, "epochs": 10},
    # ---------- CNN ----------
    {"model": "cnn", "past_history": 22, "horizon": 18, "channels": 32, "n_layers": 2, "kernel": 3, "batch_size": 512, "lr": 0.001, "epochs": 10},
    {"model": "cnn", "past_history": 22, "horizon": 18, "channels": 64, "n_layers": 2, "kernel": 3, "batch_size": 512, "lr": 0.001, "epochs": 10},
    {"model": "cnn", "past_history": 22, "horizon": 18, "channels": 32, "n_layers": 3, "kernel": 3, "batch_size": 512, "lr": 0.001, "epochs": 10},
    {"model": "cnn", "past_history": 22, "horizon": 18, "channels": 64, "n_layers": 3, "kernel": 3, "batch_size": 512, "lr": 0.001, "epochs": 10},
    {"model": "cnn", "past_history": 36, "horizon": 18, "channels": 64, "n_layers": 2, "kernel": 3, "batch_size": 512, "lr": 0.001, "epochs": 10},
    # ---------- TCN ----------
    {"model": "tcn", "past_history": 22, "horizon": 18, "channels": 32, "n_blocks": 2, "kernel": 3, "dropout": 0.0, "batch_size": 512, "lr": 0.001, "epochs": 10},
    {"model": "tcn", "past_history": 22, "horizon": 18, "channels": 64, "n_blocks": 3, "kernel": 3, "dropout": 0.0, "batch_size": 512, "lr": 0.001, "epochs": 10},
    {"model": "tcn", "past_history": 22, "horizon": 18, "channels": 64, "n_blocks": 4, "kernel": 3, "dropout": 0.0, "batch_size": 512, "lr": 0.001, "epochs": 10},
    {"model": "tcn", "past_history": 36, "horizon": 18, "channels": 64, "n_blocks": 3, "kernel": 3, "dropout": 0.0, "batch_size": 512, "lr": 0.001, "epochs": 10},
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", default=None, help="optional json file with list of configs")
    ap.add_argument("--out", default="results")
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()

    if args.grid and os.path.exists(args.grid):
        with open(args.grid) as f:
            grid = json.load(f)
    else:
        grid = DEFAULT_GRID

    os.makedirs(args.out, exist_ok=True)
    os.makedirs(os.path.join(args.out, "per_series"), exist_ok=True)
    # write the grid used (for provenance)
    with open(os.path.join(args.out, "grid.json"), "w") as f:
        json.dump(grid, f, indent=1)

    rows = []
    raw_csv = os.path.join(args.out, "raw_results.csv")
    if os.path.exists(raw_csv):
        rows = pd.read_csv(raw_csv).to_dict("records")

    for i, cfg in enumerate(grid):
        name = f"{cfg['model']}_ph{cfg['past_history']}_cfg{i}"
        print(f"\n=== [{i+1}/{len(grid)}] {name} cfg={json.dumps(cfg)} ===", flush=True)
        try:
            result, ps = run_config(cfg["model"], cfg, base_seed=0)
        except Exception as e:
            print(f"FAILED {name}: {e}", flush=True)
            continue
        result["run_name"] = name
        rows.append(result)
        pd.DataFrame(rows).to_csv(raw_csv, index=False)
        ps.to_csv(os.path.join(args.out, "per_series", f"{name}.csv"), index=False)
        print(json.dumps(result), flush=True)

    print("\n=== ALL DONE ===")


if __name__ == "__main__":
    main()