"""End-to-end reproduction of the ClouDens critical claim on frozen telemetry.

Usage (from agent_solution/):
    python scripts/run_repro.py --model GRU
    python scripts/run_repro.py --model ClouDens
    python scripts/run_repro.py --model both        # both then evidence table
    python scripts/run_repro.py --model evidence    # rebuild evidence table from saved results

Outputs under results/:
    recon_errors_<model>.npy    test forecast absolute errors [T, N, 1]
    grid_<model>.csv            all (strategy, threshold) NAB/confusion; best rows
    summary_<model>.json        canonical-threshold + per-profile-best results
    evidence_table.csv          final evidence table (via --model both/evidence)
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from loader import build_bundle, prepare_split, make_loaders, build_context_edges
from models import GRUWrapper, A3TGCNWrapper
from scoring import (mahalanobis_scores, likelihood_scores, threshold_mask)
from utils import set_random_seed, fmt_id_list

HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET = "/mnt/f/dataset/cs/2607.18127_cloudens/pivoted_data_all.parquet"
ANOMALY_CSV = "/mnt/f/dataset/cs/2607.18127_cloudens/data/labels/anomaly_windows.csv"
CACHE = os.path.join(HOME, "data")
RESULTS = os.path.join(HOME, "results")
os.makedirs(RESULTS, exist_ok=True)

SLIDE_WIN = 6
SEED = 42
HIDDEN = 32
LEARNING_RATE = 1e-3
MD_PERCENTILES = [99.5, 99.6, 99.7, 99.8, 99.9]
LF_THRESHOLDS = [0.998, 0.9985, 0.999, 0.9997, 0.99975, 0.9998]
MD_CANONICAL = 99.8
LF_CANONICAL = 0.99975
_CURRENT_MODEL = ""


def model_gname():
    return _CURRENT_MODEL


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--model", choices=["GRU", "ClouDens", "both", "evidence"], default="both")
    p.add_argument("--epochs", type=int, default=15)
    p.add_argument("--device", default="auto",
                   help="cpu, cuda or auto (cuda when a GPU with free VRAM exists)"
                        " -- GD: CPU-only A3T-GCN is ~10-40x slower than GPU")
    p.add_argument("--batch", type=int, default=32)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--outdir", default=RESULTS, help="results directory")
    return p.parse_args()


def resolve_device(arg):
    if arg != "auto":
        return arg
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def get_split(device="cpu", batch=32):
    bundle = build_bundle(PARQUET, ANOMALY_CSV, CACHE)
    split = prepare_split(bundle, slide_win=SLIDE_WIN, train_val_ratio=0.8, seed=SEED)
    edge_index, edge_weight = build_context_edges(bundle.cols)
    return bundle, split, edge_index, edge_weight


def make_wrapper(model_name, split, edge_index, edge_weight, device, batch):
    if model_name == "GRU":
        return GRUWrapper(split["num_nodes"], split["node_feat"], hidden_dim=HIDDEN,
                          layer_dim=1, batch_size=batch, device=device, lr=LEARNING_RATE)
    return A3TGCNWrapper(split["node_feat"], periods=SLIDE_WIN,
                         edge_index=torch.LongTensor(edge_index).to(device),
                         edge_weight=torch.FloatTensor(edge_weight).to(device),
                         batch_size=batch, device=device, lr=LEARNING_RATE)


def run_model(model_name, epochs, device, batch, seed, split, edge_index, edge_weight,
              bundle, force=False):
    err_file = os.path.join(RESULTS, f"recon_errors_{model_name}.npy")
    info_file = os.path.join(RESULTS, f"meta_{model_name}.json")
    if (os.path.exists(err_file) and os.path.exists(info_file) and not force):
        meta = json.load(open(info_file))
        if meta.get("batch") == batch and meta.get("epochs") == epochs and meta.get("seed") == seed:
            recon = np.load(err_file)
            print(f"[{model_name}] reusing cached reconstruction errors "
                  f"(seed={seed}, epochs={epochs}, batch={batch})", flush=True)
            return recon
        print(f"[{model_name}] cached recon errors are for a different config "
              f"({meta}); re-training with batch={batch}, epochs={epochs}, seed={seed}",
              flush=True)

    torch.set_num_threads(16)
    set_random_seed(seed)
    loaders = make_loaders({
        "train": (split["feats_tr"], split["targets_tr"]),
        "valid": (split["feats_va"], split["targets_va"]),
        "test": (split["feats_te"], split["targets_te"]),
    }, batch_size=batch)

    wrapper = make_wrapper(model_name, split, edge_index, edge_weight, device, batch)
    history = wrapper.train(loaders["train"], loaders["valid"], epochs=epochs)
    preds, _, recon, test_loss = wrapper.predict(loaders["test"], mode="test")
    np.save(err_file, recon)
    json.dump({"model": model_name, "seed": seed, "epochs": epochs, "batch": batch,
               "device": device, "test_loss": test_loss,
               "training_time_s": history["training_time"]},
              open(info_file, "w"), indent=2)
    print(f"[{model_name}] test recon errors {recon.shape}, test_loss={test_loss:.6f}", flush=True)
    import gc
    del loaders, wrapper, preds
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()
    return recon


def score_all(recon, split, bundle):
    """Return long-form DataFrame with every (strategy, threshold) result."""
    import gc
    test_labels = split["test_labels"]
    test_index = split["test_index"]
    atw = bundle.anomaly_windows_test

    rows = []
    print(f"[{model_gname()}] MD score vector...", flush=True)
    md_s = mahalanobis_scores(recon, topk=1)
    for percentile in MD_PERCENTILES:
        alarms = threshold_mask(md_s, percentile)
        rows.append(_nab_row("mahalanobis", percentile, alarms, test_labels,
                             test_index, atw, extra={"perc": percentile}))
    print(f"[{model_gname()}] LF score vector...", flush=True)
    lik = likelihood_scores(recon, long_window=30, short_window=2, topk=1)
    for lt in LF_THRESHOLDS:
        alarms = (lik > lt).astype(int)
        rows.append(_nab_row("likelihood", lt, alarms, test_labels,
                             test_index, atw, extra={"lt": lt}))
    gc.collect()
    df = pd.DataFrame(rows)
    print(f"[scoring] completed {len(df)} strategy/threshold combos", flush=True)
    return df


def _nab_row(strategy, threshold, alarms, test_labels, test_index, atw, extra=None):
    from utils import get_full_nab_result, detection_dict_to_columns
    res = get_full_nab_result(alarms, test_labels, test_index, atw)
    d = detection_dict_to_columns(res["standard"]["detection_counters"])
    row = {
        "strategy": strategy, "threshold": threshold,
        "TP": res["standard"]["TP"], "TN": res["standard"]["TN"],
        "FP": res["standard"]["FP"], "FN": res["standard"]["FN"],
        "tp_windows": res["standard"]["tp_windows"],
        "nab_standard": res["standard"]["normalized"],
        "nab_lowfn": res["reward_fn"]["normalized"],
        "detected_issue_total": 3, "detected_im_total": 9, "detected_testlog_total": 7,
        "detected_issue_ids": fmt_id_list(d["issue_ids"]),
        "detected_im_ids": fmt_id_list(d["im_ids"]),
        "detected_testlog_ids": fmt_id_list(d["testlog_ids"]),
        "n_alarms": int(alarms.sum()),
    }
    if extra:
        row.update(extra)
    return row


def build_evidence(grid_dfs, out_path):
    """Canonical-threshold rows (paper Table IV methodology) + per-profile best."""
    ev_rows = []
    for model, gdf in grid_dfs.items():
        for strat, th in (("mahalanobis", MD_CANONICAL), ("likelihood", LF_CANONICAL)):
            r = gdf[(gdf["strategy"] == strat) & (abs(gdf["threshold"] - th) < 1e-9)].iloc[0]
            ev_rows.append({
                "scoring_strategy": "mahalanobis" if strat == "mahalanobis" else "likelihood",
                "model": model,
                "fill_nan": "zero",
                "threshold": th,
                "selection": "canonical",
                "TP": int(r["TP"]), "TN": int(r["TN"]), "FP": int(r["FP"]), "FN": int(r["FN"]),
                "nab_standard": round(r["nab_standard"], 4),
                "nab_lowfn": round(r["nab_lowfn"], 4),
                "detected_issue_tracker": r["detected_issue_ids"],
                "detected_instant_messenger": r["detected_im_ids"],
                "detected_test_log": r["detected_testlog_ids"],
            })
        # per-profile best selection (like the reproduction package's priority files)
        for profile, col in (("standard", "nab_standard"), ("reward_fn", "nab_lowfn")):
            best = gdf.loc[gdf[col].idxmax()]
            ev_rows.append({
                "scoring_strategy": "mahalanobis" if best["strategy"] == "mahalanobis" else "likelihood",
                "model": model,
                "fill_nan": "zero",
                "threshold": best["threshold"],
                "selection": f"best_{profile}",
                "TP": int(best["TP"]), "TN": int(best["TN"]), "FP": int(best["FP"]), "FN": int(best["FN"]),
                "nab_standard": round(best["nab_standard"], 4),
                "nab_lowfn": round(best["nab_lowfn"], 4),
                "detected_issue_tracker": best["detected_issue_ids"],
                "detected_instant_messenger": best["detected_im_ids"],
                "detected_test_log": best["detected_testlog_ids"],
            })
    ev = pd.DataFrame(ev_rows)
    ev.to_csv(out_path, index=False)
    print(f"\nEvidence table written to {out_path}")
    print(ev.to_string(index=False))


def main():
    global RESULTS
    args = parse_args()
    device = resolve_device(args.device)
    RESULTS = args.outdir
    os.makedirs(RESULTS, exist_ok=True)
    print(f"== model={args.model} epochs={args.epochs} device={device} "
          f"batch={args.batch} seed={args.seed} | SLIDE_WIN={SLIDE_WIN} | outdir={RESULTS} ==", flush=True)
    model_names = {"GRU": ["GRU"], "ClouDens": ["ClouDens"], "both": ["GRU", "ClouDens"],
                   "evidence": []}[args.model]

    bundle, split, edge_index, edge_weight = get_split(device, args.batch)

    grid_dfs = {}
    for mn in model_names:
        global _CURRENT_MODEL
        _CURRENT_MODEL = mn
        recon = run_model(mn, args.epochs, device, args.batch, args.seed,
                          split, edge_index, edge_weight, bundle)
        g = score_all(recon, split, bundle)
        gdf = g.sort_values(["strategy"], kind="stable")
        gdf.to_csv(os.path.join(RESULTS, f"grid_{mn}.csv"), index=False)
        grid_dfs[mn] = gdf
        print(f"\n[{mn}] best standard NAB: {gdf.loc[gdf['nab_standard'].idxmax()].to_dict()}")

    if args.model in ("both", "evidence"):
        if not grid_dfs:
            for mn in ("GRU", "ClouDens"):
                gf = os.path.join(RESULTS, f"grid_{mn}.csv")
                if os.path.exists(gf):
                    grid_dfs[mn] = pd.read_csv(gf)
        build_evidence(grid_dfs, os.path.join(RESULTS, "evidence_table.csv"))


if __name__ == "__main__":
    main()