"""Train a strong MLP head on the cached frozen ResNet18 features.

This is equivalent to fine-tuning only the classification heads of the
MultiTaskResNet (backbone frozen), but on cached features so it costs only
seconds-to-minutes of CPU. Reports test OA / macro-F1 / label_1 accuracy.

Usage: TORCH_THREADS=8 python3 src/03b_mlp_probe.py
"""
import json
import os
import sys
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import N_L1, N_L2, RESULTS_DIR, SEED, load_labels, set_seed  # noqa: E402
from sklearn.metrics import accuracy_score, f1_score  # noqa: E402


class HeadMLP(nn.Module):
    def __init__(self, dim=512, hidden=1024, p=0.4):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, hidden), nn.BatchNorm1d(hidden), nn.ReLU(inplace=True),
            nn.Dropout(p),
            nn.Linear(hidden, hidden), nn.BatchNorm1d(hidden), nn.ReLU(inplace=True),
            nn.Dropout(p),
        )
        self.fc2 = nn.Linear(hidden, N_L2)
        self.fc1 = nn.Linear(hidden, N_L1)

    def forward(self, x):
        h = self.net(x)
        return self.fc2(h), self.fc1(h), h


def main():
    set_seed(SEED)
    torch.set_num_threads(int(os.environ.get("TORCH_THREADS", "10")))
    d = np.load(os.path.join(RESULTS_DIR, "features_resnet18_224.npz"))
    feat = torch.from_numpy(d["feat"]).float()
    lab = load_labels()
    l1, l2, split = lab["label_1"], lab["label_2"], lab["split"]
    tr, te = split == "train", split == "test"
    x_tr, x_te = feat[tr], feat[te]
    y2_tr = torch.from_numpy(l2[tr].astype(np.int64))
    y2_te = l2[te]
    y1_tr = torch.from_numpy(l1[tr].astype(np.int64))
    y1_te = l1[te]
    print(f"[mlp] train={x_tr.shape[0]} test={x_te.shape[0]}")

    model = HeadMLP()
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=40)
    best = -1
    t0 = time.time()
    for ep in range(40):
        model.train()
        rng = np.random.RandomState(SEED + ep)
        order = rng.permutation(x_tr.shape[0])
        for s in range(0, order.size, 512):
            ids = order[s:s + 512]
            lg2, lg1, _ = model(x_tr[ids])
            loss = F.cross_entropy(lg2, y2_tr[ids]) + 0.3 * F.cross_entropy(lg1, y1_tr[ids])
            opt.zero_grad(); loss.backward(); opt.step(); sched.step()
        model.eval()
        with torch.no_grad():
            lg2, lg1, _ = model(x_te)
        p2 = lg2.argmax(1).numpy(); p1 = lg1.argmax(1).numpy()
        oa = accuracy_score(y2_te, p2)
        mf1 = f1_score(y2_te, p2, average="macro", labels=list(range(N_L2)), zero_division=0)
        l1a = accuracy_score(y1_te, p1)
        print(f"[mlp] ep{ep+1:02d} OA={oa*100:.3f}% macroF1={mf1*100:.2f}% L1={l1a*100:.2f}% "
              f"({time.time()-t0:.0f}s)", flush=True)
        if oa > best:
            best = oa
            torch.save({"model": model.state_dict(), "oa": oa, "seed": SEED},
                       os.path.join(RESULTS_DIR, "mlp_probe.pt"))
    with open(os.path.join(RESULTS_DIR, "mlp_probe_summary.json"), "w") as fp:
        json.dump({"best_oa": float(best), "note": "frozen ResNet18 features + MLP head"},
                  fp, indent=2)
    print(f"[mlp] done best OA {best*100:.3f}% in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()