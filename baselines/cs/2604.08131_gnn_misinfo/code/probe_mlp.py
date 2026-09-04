"""
Probe the MLP baseline regimes to interpret the paper's MLP anchor of
66.8 ± 29.1:

  1. mlp_200step : 2x256/128 ReLU MLP, Adam lr=1e-3, fixed budget of 200
                   mini-batch update steps (the literal reading of the
                   paper's §3.3 "max 200 iterations" for a batched loop),
                   early stopping on val F1.
  2. mlp_sklearn : sklearn MLPClassifier(hidden 256/128, ReLU, early stop,
                   max_iter=200) as explicitly suggested in TASK.md.

Both reuse the exact same frozen split (results/splits/*.csv from the main
pipeline run) and train-only TF-IDF (max 5000) so results are comparable and
leak-free.

Usage:
    python probe_mlp.py --results ../results --seeds 0 1 2
Appends probe rows to results/metrics_probes.csv
"""

import argparse
import os

import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from pipeline import (to_csr_tensor, make_model, metrics,
                      predict_proba_binary)


def load_assets(results_dir, max_features=5000):
    csv_path = None
    for p in [os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "data", "welfake", "WELFake_Dataset.csv"),
              "/mnt/f/dataset/cs/2604.08131_gnn_misinfo/data/welfake/"
              "WELFake_Dataset.csv"]:
        if os.path.isfile(p):
            csv_path = p
            break
    df = pd.read_csv(csv_path).dropna(subset=["text"]).reset_index(drop=True)
    text = df["text"].values
    y = df["label"].values
    splits = {k: pd.read_csv(os.path.join(results_dir, "splits", f"{k}_index.csv")
                             )["index"].values for k in ("train", "val", "test")}
    vect = TfidfVectorizer(max_features=max_features)
    X_train = vect.fit_transform([text[i] for i in splits["train"]])
    X_val = vect.transform([text[i] for i in splits["val"]])
    X_test = vect.transform([text[i] for i in splits["test"]])
    return (X_train, X_val, X_test,
            y[splits["train"]], y[splits["val"]], y[splits["test"]])


def run_mlp_steps(X_train, y_train, X_val, y_val, X_test, y_test, seed,
                  n_steps=200, batch=512, patience=10, lr=1e-3):
    import torch
    torch.manual_seed(seed)
    np.random.seed(seed)
    rng_steps = np.random.RandomState(seed + 1)

    # import training machinery
    from pipeline import train_one_seed
    Xc = to_csr_tensor(X_train.astype(np.float32))
    Vc = to_csr_tensor(X_val.astype(np.float32))
    Tc = to_csr_tensor(X_test.astype(np.float32))
    model, t, hist = train_one_seed(
        "mlp", Xc, y_train, Vc, y_val, Tc, y_test, adj_norm=None,
        seed=seed, max_epochs=n_steps, patience=patience, lr=lr,
        mlp_mode="minibatch", mlp_n_steps=n_steps, mlp_batch=batch,
        X_train_sp=X_train, X_test_sp=X_test)
    t["seed"] = seed
    return model, t, hist


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "results"))
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--only", default="both",
                    help="both|mlp_200step|mlp_sklearn")
    args = ap.parse_args()
    seeds = [int(s) for s in args.seeds.split(",")]

    X_train, X_val, X_test, y_train, y_val, y_test = load_assets(args.results)

    rows = []
    Xc = to_csr_tensor(X_train.astype(np.float32))
    Vc = to_csr_tensor(X_val.astype(np.float32))
    Tc = to_csr_tensor(X_test.astype(np.float32))
    if args.only in ("both", "mlp_200step"):
        for seed in seeds:
            model, t, hist = run_mlp_steps(X_train, y_train, X_val, y_val,
                                           X_test, y_test, seed, n_steps=200,
                                           batch=512)
            rows.append({"model": "mlp_200step", "seed": seed,
                        **{k: t[k] for k in ("n", "f1", "precision", "recall",
                                             "accuracy", "best_epoch",
                                             "best_val_f1", "time_s")}})
            print(f"mlp_200step seed={seed}: F1={t['f1']:.4f} "
                  f"(2x256/128, 200 mini-batch steps)")
            hist.to_csv(os.path.join(args.results,
                                     f"history_mlp_200step_{seed}.csv"),
                        index=False)
            import torch
            with torch.no_grad():
                proba = predict_proba_binary(model, Tc)
            pd.DataFrame({"model": "mlp_200step", "seed": seed,
                          "original_index": None,
                          "y_true": y_test,
                          "y_pred": proba.argmax(1).numpy(),
                          "p_fake": proba[:, 1].numpy()}).to_csv(
                os.path.join(args.results,
                             f"predictions_mlp_200step_{seed}.csv"),
                index=False)

    if args.only in ("both", "mlp_sklearn"):
        from sklearn.neural_network import MLPClassifier
        for seed in seeds[:1]:
            sk = MLPClassifier(hidden_layer_sizes=(256, 128),
                               activation="relu", max_iter=200,
                               learning_rate_init=1e-3, alpha=0.0,
                               solver="adam", batch_size="auto",
                               shuffle=False, random_state=seed)
            sk.fit(X_train, y_train)
            yp = sk.predict(X_test)
            t = metrics(y_test, yp)
            rows.append({"model": "mlp_sklearn", "seed": seed,
                        **{k: t[k] for k in ("n", "f1", "precision", "recall",
                                             "accuracy")},
                        "best_epoch": sk.n_iter_, "best_val_f1": np.nan,
                        "time_s": np.nan})
            print(f"mlp_sklearn seed={seed}: F1={t['f1']:.4f} "
                  f"iters={sk.n_iter_}")

    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(args.results, "metrics_probes.csv"), index=False)
    print("saved results/metrics_probes.csv")
    print(out[["model", "seed", "n", "f1", "precision", "recall"]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())