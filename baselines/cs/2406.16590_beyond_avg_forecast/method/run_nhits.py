"""Train the N-HiTS global models (one per sampling frequency) and produce
test-segment forecasts for every series.

Results: results/forecasts/nhits_<freq>.npz (resume-safe, skips frequencies
that already have a forecast file), checkpoints under results/ckpt/.

Forecast arrays are stored padded to the frequency's model output length
(``output_horizon``); series whose own horizon is smaller only use the first
``horizon`` columns (the evaluation masks them accordingly).
"""

from __future__ import annotations

import os
import pickle
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from data_loader import load_data
from method.nhits import DEVICE, NHiTS, train_nhits, predict_nhits

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CKPT_DIR = os.path.join(OUT_DIR, "ckpt")
FC_DIR = os.path.join(OUT_DIR, "forecasts")


def run_frequency(series_list, freq, cfg):
    fpath = os.path.join(FC_DIR, f"nhits_{freq}.npz")
    c_path = os.path.join(CKPT_DIR, f"nhits_{freq}.pt")
    if os.path.exists(fpath):
        print(f"[nhits:{freq}] forecasts cached");
        return fpath
    t0 = time.time()
    if os.path.exists(c_path):
        ck = torch.load(c_path, map_location=DEVICE)
        model = NHiTS(cfg["input_window"], cfg["output_horizon"],
                      cfg["n_stacks"], cfg["n_blocks_per_stack"],
                      cfg["width"], cfg["n_pool_kernel_size"])
        model.load_state_dict(ck["state_dict"])
        model.to(DEVICE)
        stats = {"resumed": c_path}
        print(f"[nhits:{freq}] resumed from checkpoint {os.path.basename(c_path)}")
    else:
        model, stats = train_nhits(series_list, freq, cfg, outdir=CKPT_DIR, seed=config.SEED)
    print(f"[nhits:{freq}] ready in {time.time() - t0:.1f}s {stats}")

    out_len = cfg["output_horizon"]
    idx = []
    fcs = []
    for i, s in enumerate(series_list):
        if s.frequency != freq:
            continue
        fc = predict_nhits(model, s, cfg["input_window"], cfg["output_horizon"])
        if fc is None:
            continue
        idx.append(i)
        pad = np.full(out_len, np.nan)
        pad[: len(fc)] = fc
        fcs.append(pad)
    out = {"idx": np.array(idx, dtype=np.int64), "fc": np.stack(fcs)}
    with open(fpath, "wb") as fh:
        pickle.dump(out, fh)
    print(f"[nhits:{freq}] forecasts {out['fc'].shape} -> {os.path.basename(fpath)}")
    return fpath


def main(only_freqs=None, epochs_override=None):
    series_list, meta = load_data()
    os.makedirs(CKPT_DIR, exist_ok=True)
    os.makedirs(FC_DIR, exist_ok=True)
    freqs = only_freqs or config.FREQUENCIES
    for freq in freqs:
        cfg = dict(config.NHITS_CFG[freq])
        cfg.update(config.NHITS_TRAIN_CFG)
        if epochs_override is not None:
            cfg["epochs"] = epochs_override
        run_frequency(series_list, freq, cfg)
    return True


if __name__ == "__main__":
    freq_filter = sys.argv[1] if len(sys.argv) > 1 else None
    epochs_ov = int(sys.argv[2]) if len(sys.argv) > 2 else None
    main(only_freqs=[freq_filter] if freq_filter else None,
         epochs_override=epochs_ov)