"""End-to-end pipeline for the frozen ML-IAP dataset (1906.08888).

Runs descriptor feature extraction, >2 trainable energy/force surrogate models
with a leakage-safe protocol (inner 20% validation for hyper-parameters,
re-fit on full train, evaluate the frozen test once), reports per-element
energy/force MAE, the paper-anchor comparison and the claim labels.

Usage:
    python3 run_pipeline.py            # all elements
    python3 run_pipeline.py Cu Si      # selected elements
"""
import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import energy_models as EM
from dataset import SplitData
from io_data import ELEMENTS

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
CACHE = os.path.join(RESULTS, "_cache")
os.makedirs(CACHE, exist_ok=True)
os.makedirs(RESULTS, exist_ok=True)


def _jdefault(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, tuple):
        return list(o)
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

ALPHA_GRID = np.logspace(-8, 3, 24)
GAMMA_GRID = np.array([0.003, 0.01, 0.03, 0.1, 0.3, 1.0])
KALPHA_GRID = np.array([1e-6, 1e-4, 1e-2])
N_BASIS = 600

VAL_FRAC = 0.2
SEED = 0


def tune_linear_joint(elem, tr, alpha_grid, fit_indices, val_indices):
    """Tune (alpha, lambda_f) for the energy+force linear model cheaply via
    cached Gram pieces. score = val energy MAE + 50*val force MAE."""
    proto = EM.LinearEQModel()
    g = proto._gram(tr, fit_indices)
    best = None
    for a in alpha_grid:
        for lf in {0.01, 0.1, 0.3, 1.0}:
            m = EM.LinearEQModel(alpha=float(a), lambda_f=lf)
            m.solve_from_gram(g)
            mae_e, mae_f, _, _ = EM.batch_metrics_eval(m, tr, val_indices)
            score = mae_e + 50.0 * mae_f
            if best is None or score < best[0]:
                best = (score, mae_e, mae_f, float(a), float(lf))
    return best


def tune_quad(elem, tr, alpha_grid, fit_indices, val_indices):
    best = None
    for a in alpha_grid:
        m = EM.QuadEQModel(alpha=float(a)).fit(tr, fit_indices)
        mae_e, mae_f, _, _ = EM.batch_metrics_eval(m, tr, val_indices)
        if best is None or mae_e < best[0]:
            best = (mae_e, mae_f, a)
    return best


def tune_kernel(elem, tr, fit_indices, val_indices):
    best = None
    for g in GAMMA_GRID:
        for a in KALPHA_GRID:
            m = EM.KernelEQModel(gamma=float(g), alpha=float(a), n_basis=N_BASIS,
                                 seed=SEED).fit(tr, fit_indices)
            mae_e, mae_f, _, _ = EM.batch_metrics_eval(m, tr, val_indices)
            if best is None or mae_e < best[0]:
                best = (mae_e, mae_f, float(g), float(a))
    return best


def main(elements):
    np.random.seed(SEED)
    rows = []            # evidence table rows
    metrics = {"elements": {}, "anchor_comparison": {}, "protocol": {}}
    group_stats = {}     # per element group breakdown of counts
    MODEL_DIR = os.path.join(RESULTS, "models")
    os.makedirs(MODEL_DIR, exist_ok=True)

    for elem in elements:
        t0 = time.time()
        print(f"\n=== {elem} ===", flush=True)
        tr = SplitData(elem, "train", CACHE)
        te = SplitData(elem, "test", CACHE)
        fit_idx, val_idx = EM._design_split(tr.n_configs, VAL_FRAC, SEED)

        # ---------------- data stats ----------------
        train_counts = {g: int(np.sum(tr.groups == g)) for g in set(tr.groups.tolist())}
        test_counts = {g: int(np.sum(te.groups == g)) for g in set(te.groups.tolist())}
        group_stats[elem] = {"train": train_counts, "test": test_counts,
                             "train_n": tr.n_configs, "test_n": te.n_configs,
                             "train_atoms": tr.n_atoms, "test_atoms": te.n_atoms}

        # ---------------- models ----------------
        model_results = {}

        # linear SNAP proxy (energy + force joint fit)
        score_e, mae_e, mae_f, best_a, best_lf = tune_linear_joint(
            elem, tr, ALPHA_GRID, fit_idx, val_idx)
        m_lin = EM.LinearEQModel(alpha=best_a, lambda_f=best_lf).fit(tr, list(range(tr.n_configs)))
        tr_e, tr_f, _, _ = EM.batch_metrics_eval(m_lin, tr, list(range(tr.n_configs)))
        te_e, te_f, _, _ = EM.batch_metrics_eval(m_lin, te, list(range(te.n_configs)))
        model_results["linear_snap_proxy"] = dict(train_energy_mae=tr_e, train_force_mae=tr_f,
                                                  test_energy_mae=te_e, test_force_mae=te_f,
                                                  params=dict(alpha=best_a, lambda_f=best_lf),
                                                  tuner=dict(val_energy_mae=mae_e, val_force_mae=mae_f))

        # quadratic qSNAP proxy
        mae_e, mae_f, best_a = tune_quad(elem, tr, ALPHA_GRID, fit_idx, val_idx)
        m_q = EM.QuadEQModel(alpha=best_a).fit(tr, list(range(tr.n_configs)))
        tr_e, tr_f, _, _ = EM.batch_metrics_eval(m_q, tr, list(range(tr.n_configs)))
        te_e, te_f, _, _ = EM.batch_metrics_eval(m_q, te, list(range(te.n_configs)))
        model_results["quad_snap_proxy"] = dict(train_energy_mae=tr_e, train_force_mae=tr_f,
                                                test_energy_mae=te_e, test_force_mae=te_f,
                                                params=dict(alpha=best_a), tuner=dict(val_energy_mae=mae_e))

        # kernel GAP proxy
        mae_e, mae_f, best_g, best_a = tune_kernel(elem, tr, fit_idx, val_idx)
        m_k = EM.KernelEQModel(gamma=best_g, alpha=best_a, n_basis=N_BASIS, seed=SEED)
        m_k.fit(tr, list(range(tr.n_configs)))
        tr_e, tr_f, _, _ = EM.batch_metrics_eval(m_k, tr, list(range(tr.n_configs)))
        te_e, te_f, _, _ = EM.batch_metrics_eval(m_k, te, list(range(te.n_configs)))
        model_results["kernel_gap_proxy"] = dict(train_energy_mae=tr_e, train_force_mae=tr_f,
                                                 test_energy_mae=te_e, test_force_mae=te_f,
                                                 params=dict(gamma=best_g, alpha=best_a, n_basis=N_BASIS),
                                                 tuner=dict(val_energy_mae=mae_e))

        # MLP NNP proxy
        m_mlp = EM.MLPForceModel(hidden=(64, 64), max_iter=500, seed=SEED)
        m_mlp.fit(tr, list(range(tr.n_configs)))
        tr_e, tr_f, _, _ = EM.batch_metrics_eval(m_mlp, tr, list(range(tr.n_configs)))
        te_e, te_f, _, _ = EM.batch_metrics_eval(m_mlp, te, list(range(te.n_configs)))
        model_results["mlp_nnp_proxy"] = dict(train_energy_mae=tr_e, train_force_mae=tr_f,
                                              test_energy_mae=te_e, test_force_mae=te_f,
                                              params=dict(hidden=(64, 64), max_iter=500))

        # ---------------- save fitted models (for reproduce/analysis) ----
        import pickle as _pk
        with open(os.path.join(MODEL_DIR, f"{elem}_models.pkl"), "wb") as f:
            _pk.dump({"linear": m_lin, "quad": m_q, "kernel": m_k, "mlp": m_mlp}, f)

        # ---------------- per-group + per-config diagnostics for best 2 ----
        import pandas as _pd
        per_cfg = {}
        for name, mdl in [("kernel_gap_proxy", m_k), ("quad_snap_proxy", m_q)]:
            n_te = te.n_configs
            Epred, _Fpred = [], []
            errs_cfg = np.zeros(n_te)
            for ci in range(n_te):
                E, F = mdl.predict_config(te, ci)
                errs_cfg[ci] = abs(E - te.E_cfg[ci]) / te.num_atoms[ci] * 1000.0
            per_cfg[name] = errs_cfg
            gb = {}
            for g in set(te.groups.tolist()):
                m = te.groups == g
                gb[g] = float(errs_cfg[m].mean())
            model_results[name]["test_group_energy_mae"] = gb
        model_results["per_config_test_energy_mae_meV"] = per_cfg

        # naive baseline: constant per-atom reference energy
        navg = float(np.average(tr.E_cfg / tr.num_atoms))
        naive = np.abs(te.E_cfg - navg * te.num_atoms) / te.num_atoms * 1000.0
        naive_tr = np.abs(tr.E_cfg - navg * tr.num_atoms) / tr.num_atoms * 1000.0
        model_results["reference_energy_baseline"] = dict(
            train_energy_mae=float(naive_tr.mean()), test_energy_mae=float(naive.mean()))

        # ---------------- evidence rows ----------------
        ev_models = ["linear_snap_proxy", "quad_snap_proxy", "kernel_gap_proxy",
                     "mlp_nnp_proxy", "reference_energy_baseline"]
        for model in ev_models:
            md = model_results[model]
            for split, ekey, fkey in [("train", "train_energy_mae", "train_force_mae"),
                                      ("test", "test_energy_mae", "test_force_mae")]:
                if model == "reference_energy_baseline":
                    rows.append(dict(element=elem, model=model, split=split,
                                     metric="energy_mae_meV_per_atom", value=md[ekey]))
                    continue
                rows.append(dict(element=elem, model=model, split=split,
                                 metric="energy_mae_meV_per_atom", value=md[ekey]))
                rows.append(dict(element=elem, model=model, split=split,
                                 metric="force_mae_eV_ang", value=md[fkey]))

        metrics["elements"][elem] = {
            "n_train": tr.n_configs, "n_test": te.n_configs,
            "n_train_atoms": tr.n_atoms, "n_test_atoms": te.n_atoms,
            "train_counts_per_group": train_counts, "test_counts_per_group": test_counts,
            "models": model_results,
        }
        # incremental save so interrupted runs still preserve finished elements
        os.makedirs(os.path.join(RESULTS, "elements_raw"), exist_ok=True)
        with open(os.path.join(RESULTS, "elements_raw", f"{elem}.json"), "w") as f:
            json.dump({"element": elem, "dataset": {
                "n_train": tr.n_configs, "n_test": te.n_configs,
                "n_train_atoms": tr.n_atoms, "n_test_atoms": te.n_atoms,
                "train_group_counts": {g: int(np.sum(tr.groups == g)) for g in set(tr.groups.tolist())},
                "test_group_counts": {g: int(np.sum(te.groups == g)) for g in set(te.groups.tolist())},
            }, "models": model_results}, f, indent=2, default=_jdefault)
        print(f"  split {elem}: train={tr.n_configs} test={te.n_configs}", flush=True)
        for name, md in model_results.items():
            if "train_force_mae" in md:
                print(f"   {name:24s} traE={md['train_energy_mae']:7.2f} meV testE={md['test_energy_mae']:7.2f} "
                      f"traF={md['train_force_mae']:.4f} testF={md['test_force_mae']:.4f} [{md.get('params')}]", flush=True)
        print(f"  elapsed {time.time()-t0:.0f}s", flush=True)

    # naive over all
    metrics["protocol"] = {
        "descriptor": "Behler-Parrinello radial (G2 6 + shells 7) + angular (2) features, cutoff 5 A",
        "energy_conserving": ["linear_snap_proxy", "quad_snap_proxy", "kernel_gap_proxy"],
        "force_from_gradient": True,
        "mlp_nnp_proxy": "direct per-atom MLP (force head + energy head), non-conservative by design",
        "val_split": VAL_FRAC, "seed": SEED,
        "eval_metric": "energy MAE meV/atom; force MAE eV/A per component",
        "caveat": "models are simplified surrogates of the paper's GAP/MTP/SNAP/NNP; absolute values not comparable",
    }

    with open(os.path.join(RESULTS, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2, default=_jdefault)
    evidence = pd_frame(rows)
    evidence.to_csv(os.path.join(RESULTS, "evidence_table.csv"), index=False)
    with open(os.path.join(RESULTS, "group_stats.json"), "w") as f:
        json.dump(group_stats, f, indent=2)
    print("\nSaved results/metrics.json, results/evidence_table.csv.")


def pd_frame(rows):
    import pandas as pd
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("elements", nargs="*", default=ELEMENTS)
    args = ap.parse_args()
    main(args.elements if args.elements else ELEMENTS)