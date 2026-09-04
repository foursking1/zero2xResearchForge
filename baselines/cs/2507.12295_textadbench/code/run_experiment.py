#!/usr/bin/env python3
"""Text-ADBench reproduction: SMS-Spam + LLaMA-3-8B (mntp) EOS embeddings.

Shallow vs deep anomaly detectors on the official frozen Text-ADBench
embeddings (single configuration that anchors the paper's §5.2 'deep
detectors show no advantage' claim).

Protocol (paper §5 / official repo anomaly_detection/main.py):
    model.fit(train_data)                      # 4,044 normal-only samples
    score = model.decision_function(test_data) # 1,490 samples
    auroc   = roc_auc_score(test_label, score)

Frozen inputs (SHA-256 verified, see data/source_manifest.json):
    train/mntp_eos_token_embeddings.npy  (4044, 4096) float32
    train/mntp_embedding_labels.npy      (4044,) all 0 (normal)
    test/mntp_eos_token_embeddings.npy   (1490, 4096) float32
    test/mntp_embedding_labels.npy       (1490,) 743 normal / 747 spam

Anti-leakage: test labels are NEVER used for validation / selection;
embeddings are byte-identical to the official freeze.
"""

import argparse
import json
import logging
import os
import sys

import numpy as np
from sklearn.metrics import roc_auc_score

os.environ.setdefault("OMP_NUM_THREADS", "16")
os.environ.setdefault("MKL_NUM_THREADS", "16")

import torch

try:
    from pyod.models.knn import KNN
    from pyod.models.iforest import IForest
    from pyod.models.ocsvm import OCSVM
    from pyod.models.lof import LOF
    from pyod.models.pca import PCA
    from pyod.models.kde import KDE
    from pyod.models.ecod import ECOD
    from pyod.models.auto_encoder import AutoEncoder
    from pyod.models.deep_svdd import DeepSVDD
    import pyod
    from dpad import DPAD
    # DeepSVDD device port (math identical to pyod 3.6.4, plus cuda speed)
    from deep_port import DeepSVDDDevice
except ImportError as e:  # pragma: no cover - fallback if repo layouts differ
    raise SystemExit(
        f"Missing dependency {e}. Install pyod==3.6.4 and run from code/ dir "
        f"so 'dpad' is importable."
    )

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("textadbench")

# ---------------------------------------------------------------------------
# Data location resolution (works in the offline judge sandbox and on WSL)
# ---------------------------------------------------------------------------
DEFAULT_DATA_DIRS = [
    os.environ.get("TEXTAD_DATA_DIR", ""),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data",
                 "embeddings", "sms_spam", "Llama3-8b"),  # bundled copy
    "data/embeddings/sms_spam/Llama3-8b",
    "embeddings/sms_spam/Llama3-8b",
    "/mnt/f/dataset/cs/2507.12295_textadbench/embeddings/sms_spam/Llama3-8b",
    "/mnt/d/dataset/cs/2507.12295_textadbench/embeddings/sms_spam/Llama3-8b",
    "F:/dataset/cs/2507.12295_textadbench/embeddings/sms_spam/Llama3-8b",
]

EXPECTED_SHAPES = {"train": (4044, 4096), "test": (1490, 4096)}

SEED_LIST = [42, 2024, 7, 123, 8888]  # 5 repeats, paper reports 5-run average


def resolve_data_dir(explicit=None):
    candidates = ([explicit] if explicit else []) + DEFAULT_DATA_DIRS
    for c in candidates:
        if not c:
            continue
        train = os.path.join(c, "train")
        test = os.path.join(c, "test")
        if (
            os.path.isfile(os.path.join(train, "mntp_eos_token_embeddings.npy"))
            and os.path.isfile(os.path.join(train, "mntp_embedding_labels.npy"))
            and os.path.isfile(os.path.join(test, "mntp_eos_token_embeddings.npy"))
            and os.path.isfile(os.path.join(test, "mntp_embedding_labels.npy"))
        ):
            return c
    raise SystemExit(
        "Frozen data not found. Pass --data-dir pointing at the "
        "sms_spam/Llama3-8b directory with train/ and test/ subfolders."
    )


def load_data(data_dir):
    train = {
        "X": np.load(
            os.path.join(data_dir, "train", "mntp_eos_token_embeddings.npy"),
            allow_pickle=True,
        ),
        "y": np.asarray(
            np.load(os.path.join(data_dir, "train", "mntp_embedding_labels.npy"),
                    allow_pickle=True)
        ).ravel(),
    }
    test = {
        "X": np.load(
            os.path.join(data_dir, "test", "mntp_eos_token_embeddings.npy"),
            allow_pickle=True,
        ),
        "y": np.asarray(
            np.load(os.path.join(data_dir, "test", "mntp_embedding_labels.npy"),
                    allow_pickle=True)
        ).ravel(),
    }
    assert train["X"].shape == EXPECTED_SHAPES["train"], f"Unexpected train shape {train['X'].shape}"
    assert test["X"].shape == EXPECTED_SHAPES["test"], f"Unexpected test shape {test['X'].shape}"
    assert (train["y"] == 0).all(), "train labels should be all-normal (0)"
    n_test_pos = int((test["y"] == 1).sum())
    log.info(
        "train X %s  train labels all-normal %s | test X %s  #anomaly=%d/%d",
        train["X"].shape, (train["y"] == 0).all(), test["X"].shape,
        n_test_pos, len(test["y"]),
    )
    return train, test


# ---------------------------------------------------------------------------
# Detector factories --------------------------------------------------------
# ---------------------------------------------------------------------------
def _shallow_factories():
    """Official arguments/*.json params (LLM embedding row) mapped to
    pyod 3.6.4. contamination=0.1 does not affect AUROC (raw scores used)."""
    return {
        "knn": lambda seed: KNN(n_neighbors=3, contamination=0.1),
        "iforest": lambda seed: IForest(contamination=0.1, random_state=seed),
        "ocsvm": lambda seed: OCSVM(kernel="rbf", contamination=0.1),
        "lof": lambda seed: LOF(n_neighbors=30, contamination=0.1),
        "pca": lambda seed: PCA(n_components=0.9, contamination=0.1, random_state=seed),
        "kde": lambda seed: KDE(bandwidth=50, metric="euclidean", contamination=0.1),
        "ecod": lambda seed: ECOD(contamination=0.1),
    }


def _deep_factories(n_features, device="cpu"):
    """Official arguments/ae_llm.json, dsvdd_llm.json, dpad_llm.json.
    pyod 3.6.4 has no `lr` alias for DeepSVDD (uses learning_rate) and no
    null output_activation -> mapped to `identity` (i.e. linear readout).
    Only the hyper-parameters the paper set are overridden; the rest fall
    back to pyod defaults (matching how the official repo invoked pyod)."""
    ae_cfg = dict(
        preprocessing=False, lr=1e-4, epoch_num=300, batch_size=1000,
        optimizer_name="adam", hidden_activation_name="leaky_relu",
        hidden_neuron_list=[4096, 2048, 2048, 1024],
    )
    dsvdd_cfg = dict(
        # preprocess warning: pyod 2.0.2 json sets preprocessing=False
        preprocessing=False, learning_rate=1e-4, epochs=300, batch_size=1000,
        optimizer="adam", hidden_activation="leaky_relu",
        hidden_neurons=[4096, 2048, 2048, 1024],
        output_activation="identity",  # json had null -> linear readout
        validation_size=0.0, dropout_rate=0.0,
        l2_regularizer=0.01, use_ae=True, n_features=n_features,
    )
    dpad_cfg = dict(
        learning_rate=1e-4, n_epochs=200, hidden_neurons=[4096, 2048, 2048, 1024],
        hidden_activation="leaky_relu", gamma=0.01, lamb=0.1, k=10,
        device=device, contamination=0.1, n_features=n_features,
    )

    def make_ae(seed):
        return AutoEncoder(contamination=0.1, random_state=seed,
                           device=device, verbose=0, **ae_cfg)

    def make_dsvdd(seed):
        torch.manual_seed(seed)
        np.random.seed(seed)
        return DeepSVDDDevice(contamination=0.1, random_state=seed,
                              device=device, verbose=0, **dsvdd_cfg)

    def make_dpad(seed):
        torch.manual_seed(seed)
        np.random.seed(seed)
        m = DPAD(**dpad_cfg)
        m.random_state = seed
        return m

    return {"ae": make_ae, "dsvdd": make_dsvdd, "dpad": make_dpad}


def get_factory(name, n_features, device="cpu"):
    shallow = _shallow_factories()
    if name in shallow:
        return shallow[name]
    deep = _deep_factories(n_features, device=device)
    if name in deep:
        return deep[name]
    raise KeyError(name)


# ---------------------------------------------------------------------------
# Fitting / scoring ---------------------------------------------------------
# ---------------------------------------------------------------------------
def fit_score(factory, train_X, test_X, seed):
    """Deterministic, leakage-free pipeline."""
    rng = np.random.RandomState(seed)
    detector = factory(seed)
    detector.fit(train_X)
    score = detector.decision_function(test_X)
    return np.asarray(score, dtype=np.float32)


def evaluate(score, test_y):
    return roc_auc_score(test_y, score)


def save_scores(base_dir, method, seed, score):
    out_dir = os.path.join(base_dir, "scores")
    os.makedirs(out_dir, exist_ok=True)
    np.save(os.path.join(out_dir, f"{method}_seed{seed}_test_scores.npy"), score)


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", default=None, help="dir with train/ and test/ subfolders of frozen .npy")
    ap.add_argument("--methods", default="all", help="comma list or 'all'")
    ap.add_argument("--seeds", default=None, help="comma list of int seeds (default: SEED_LIST)")
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    ap.add_argument("--outdir", default="results", help="output folder")
    args = ap.parse_args()

    torch.manual_seed(42)
    np.random.seed(42)
    if args.device == "cuda":
        torch.cuda.set_device(0)
    torch.set_num_threads(16)

    data_dir = resolve_data_dir(args.data_dir)
    log.info("Using frozen data at %s", data_dir)
    train, test = load_data(data_dir)
    train_X, test_X = train["X"], test["X"]

    if args.methods == "all":
        methods = list(_shallow_factories()) + list(_deep_factories(train_X.shape[1], device=args.device))
    else:
        methods = [m.strip() for m in args.methods.split(",") if m.strip()]
    seeds = [int(s) for s in args.seeds.split(",")] if args.seeds else SEED_LIST

    os.makedirs(args.outdir, exist_ok=True)
    results = []
    env_info = {
        "pyod": getattr(pyod, "__version__", "?"),
        "torch": torch.__version__,
        "numpy": np.__version__,
        "device": args.device,
    }

    for method in methods:
        factory = get_factory(method, train_X.shape[1], device=args.device)
        n_deep = 0
        per_seed = []
        for seed in seeds:
            log.info("[%s] seed=%d  fitting", method, seed)
            torch.manual_seed(seed)
            np.random.seed(seed)
            score = fit_score(factory, train_X, test_X, seed)
            auroc = evaluate(score, test["y"])
            per_seed.append(float(auroc))
            save_scores(args.outdir, method, seed, score)
            log.info("[%s] seed=%d  AUROC=%.4f", method, seed, auroc)
        mean = float(np.mean(per_seed))
        std = float(np.std(per_seed))
        results.append({
            "method": method,
            "type": "deep" if method in ("ae", "dsvdd", "dpad") else "shallow",
            "n_train": int(train_X.shape[0]), "n_test": int(test_X.shape[0]),
            "auroc": mean, "auroc_std": std, "seeds": seeds, "per_seed": per_seed,
        })

    with open(os.path.join(args.outdir, "env_info.json"), "w") as f:
        json.dump(env_info, f, indent=2)

    with open(os.path.join(args.outdir, "auroc_per_seed.json"), "w") as f:
        json.dump(
            [{"method": r["method"], "seeds": r["seeds"], "per_seed": r["per_seed"],
              "mean": r["auroc"], "std": r["auroc_std"]} for r in results],
            f, indent=2,
        )

    # per-method JSON so concurrent runs never clobber each other
    for r in results:
        with open(os.path.join(args.outdir, f"auroc_{r['method']}.json"), "w") as f:
            json.dump({"method": r["method"], "seeds": r["seeds"],
                       "per_seed": r["per_seed"], "mean": r["auroc"],
                       "std": r["auroc_std"]}, f, indent=2)
    for r in results:
        log.info("FINAL %s  AUROC=%.4f ± %.4f", r["method"], r["auroc"], r["auroc_std"])


if __name__ == "__main__":
    main()