"""
SATIN (2304.11619) - SAT-4 majority-class baseline + supervised CNN.

1) Majority-class baseline on the test split (gives the trivial lower bound;
   if the CNN does not beat this, the claim is not reproduced).
2) Small CNN (3 conv + 2 fc) trained from scratch on the training split.
   Reports overall accuracy, per-class accuracy, and confusion matrix.

Outputs: ../results/satin_baseline_cnn_metrics.json
"""
import os, json
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("TORCH_NUM_THREADS", "2")
torch.set_num_threads(2)

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
RNG_SEED = 20260817
EPOCHS = 6
BATCH_SIZE = 512
LR = 1e-3
SUBSET_TRAIN = 20000  # speed: subsample of the 80k training split (fixed seed)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
CLASS_NAMES = ["barren land", "trees", "grassland", "buildings"]


class SmallCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(), nn.MaxPool2d(2),
        )  # 28->14->7->3
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 3 * 3, 256), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(256, 4),
        )

    def forward(self, x):
        return self.classifier(self.features(x))


def main():
    d = np.load(os.path.join(RESULTS, "satin_arrays.npz"), allow_pickle=False)
    X_tr, y_tr = d["X_train"], d["y_train"]
    X_te, y_te = d["X_test"], d["y_test"]
    # subsample training split (stratified, fixed seed) for CPU tractability
    if SUBSET_TRAIN and SUBSET_TRAIN < len(y_tr):
        rng = np.random.RandomState(RNG_SEED)
        from sklearn.model_selection import train_test_split as tts
        X_tr, _, y_tr, _ = tts(X_tr, y_tr, train_size=SUBSET_TRAIN, random_state=RNG_SEED, stratify=y_tr)
    mean = d["mean"].astype(np.float32)
    std = d["std"].astype(np.float32)

    def norm(X):
        X = X.astype(np.float32).transpose(0, 3, 1, 2)
        return (X - mean) / std

    X_tr_n = norm(X_tr)
    X_te_n = norm(X_te)

    # --- 1) majority baseline (fit on train, apply on test) ---
    maj_class = np.bincount(y_tr).argmax()
    maj_pred = np.full(len(y_te), maj_class)
    maj_oa = accuracy_score(y_te, maj_pred)
    maj_per_class = accuracy_score(y_te, maj_pred, sample_weight=None)
    # per-class recall of majority baseline
    from sklearn.metrics import recall_score
    maj_recall = recall_score(y_te, maj_pred, average=None, labels=[0, 1, 2, 3], zero_division=0)

    # --- 2) supervised CNN ---
    torch.manual_seed(RNG_SEED)
    np.random.seed(RNG_SEED)
    model = SmallCNN().to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    lossfn = nn.CrossEntropyLoss()

    n = X_tr_n.shape[0]
    history = []
    for epoch in range(EPOCHS):
        model.train()
        perm = np.random.permutation(n)
        tot_loss, n_batch = 0.0, 0
        for i in range(0, n, BATCH_SIZE):
            idx = perm[i:i + BATCH_SIZE]
            xb = torch.tensor(X_tr_n[idx]).to(DEVICE)
            yb = torch.tensor(y_tr[idx]).to(DEVICE)
            opt.zero_grad()
            out = model(xb)
            loss = lossfn(out, yb)
            loss.backward()
            opt.step()
            tot_loss += loss.item()
            n_batch += 1
        # quick train acc
        model.eval()
        with torch.no_grad():
            accs = []
            for i in range(0, n, BATCH_SIZE):
                xb = torch.tensor(X_tr_n[i:i + BATCH_SIZE]).to(DEVICE)
                accs.append((model(xb).argmax(1).cpu().numpy() == y_tr[i:i + BATCH_SIZE]).mean())
            train_acc = float(np.mean(accs))
        history.append({"epoch": epoch + 1, "loss": tot_loss / n_batch, "train_acc": train_acc})
        print(f"epoch {epoch+1}/{EPOCHS} loss={tot_loss/n_batch:.4f} train_acc={train_acc:.4f}", flush=True)

    # evaluate on test
    model.eval()
    preds = []
    with torch.no_grad():
        for i in range(0, X_te_n.shape[0], BATCH_SIZE):
            xb = torch.tensor(X_te_n[i:i + BATCH_SIZE]).to(DEVICE)
            preds.append(model(xb).argmax(1).cpu().numpy())
    preds = np.concatenate(preds)
    cnn_oa = accuracy_score(y_te, preds)
    cnn_cm = confusion_matrix(y_te, preds, labels=[0, 1, 2, 3])
    cnn_per_class = recall_score(y_te, preds, average=None, labels=[0, 1, 2, 3], zero_division=0)
    cnn_report = classification_report(y_te, preds, labels=[0, 1, 2, 3],
                                       target_names=CLASS_NAMES, output_dict=True, zero_division=0)

    out = {
        "seed": RNG_SEED,
        "epochs": EPOCHS,
        "batch_size": BATCH_SIZE,
        "train_subset_n": int(len(X_tr)),
        "device": "cpu",
        "threads": torch.get_num_threads(),
        "majority_baseline": {
            "majority_class": int(maj_class),
            "majority_class_name": CLASS_NAMES[int(maj_class)],
            "overall_acc": float(maj_oa),
            "per_class_recall": {CLASS_NAMES[i]: float(maj_recall[i]) for i in range(4)},
        },
        "supervised_cnn": {
            "overall_acc": float(cnn_oa),
            "per_class_recall": {CLASS_NAMES[i]: float(cnn_per_class[i]) for i in range(4)},
            "confusion_matrix": cnn_cm.tolist(),
            "classification_report": cnn_report,
            "train_history": history,
        },
    }
    with open(os.path.join(RESULTS, "satin_baseline_cnn_metrics.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps({"majority_OA": maj_oa, "cnn_OA": cnn_oa, "cnn_per_class": out["supervised_cnn"]["per_class_recall"]}, indent=2))
    print("confusion matrix:\n", cnn_cm)


if __name__ == "__main__":
    main()
