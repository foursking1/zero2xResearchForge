"""Position-aware CNN regression head over per-residue ESM-2 650M hidden states.

Motivation (cf. paper): mean pooling discards position; TAPE's best pretrained
models use a position-sensitive head (attention/LSTM over hidden states). This
script consumes the per-position features cached by featurize_per_position.py
and trains a small 1D-conv head over the sequence of ESM hidden vectors, with
early stopping on the validation split. It then appends rows to
results/evidence_table.csv and refreshes results/metrics.json.

Usage: python train_seq_head.py [--task fluorescence] [--epochs 40] [--device cuda|cpu]
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from scipy.stats import spearmanr
from sklearn.metrics import mean_squared_error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import CSV_FILES, RESULTS_DIR, SEED, find_data_dir  # noqa: E402

torch.manual_seed(SEED)
np.random.seed(SEED)
CACHE = os.path.join(RESULTS_DIR, "seqcache")


class ESMSeqHead(nn.Module):
    def __init__(self, d_in=1280, d_hid=176, d_conv=176, pooling="meanmax"):
        super().__init__()
        self.pos_proj = nn.Sequential(
            nn.Linear(d_in, d_hid), nn.LayerNorm(d_hid), nn.GELU())
        self.conv1 = nn.Conv1d(d_hid, d_conv, kernel_size=9, padding=4, groups=4)
        self.conv2 = nn.Conv1d(d_conv, d_conv, kernel_size=5, padding=2, groups=4)
        self.act = nn.GELU()
        p = 2 * d_conv if pooling == "meanmax" else d_conv
        self.pooling = pooling
        self.head = nn.Sequential(
            nn.Linear(p, 128), nn.GELU(), nn.Dropout(0.1), nn.Linear(128, 1))

    def forward(self, x):            # (B, L, D)
        x = self.pos_proj(x)         # position-wise learned projection
        x = x.transpose(1, 2)        # (B, D, L)
        x = self.act(self.conv1(x))
        x = self.act(self.conv2(x))
        if self.pooling == "meanmax":
            g = torch.cat([x.mean(2), x.max(2).values], dim=1)
        else:
            g = x.mean(2)
        return self.head(g).squeeze(-1)


def load_split(task, split):
    meta = json.load(open(os.path.join(CACHE, f"{task}_{split}_meta.json")))
    lens = np.load(os.path.join(CACHE, f"{task}_{split}_lens.npy"))
    data = np.lib.format.open_memmap(
        os.path.join(CACHE, f"{task}_{split}_feats.dat"), mode="r")
    return data, lens, meta


def sim_batch(data, lens, idx, batch, maxL):
    """Pack a batch of memmap rows into a (B, maxL?, D) tensor; variable lengths handled via mask."""
    B = len(idx)
    arr = np.zeros((B, maxL, data.shape[-1]), dtype=np.float32)
    mask = np.zeros((B, maxL), dtype=np.float32)
    for j, i in enumerate(idx):
        row = np.ascontiguousarray(data[int(i)][:int(lens[int(i)])]).astype(np.float32)
        arr[j, :len(row)] = row
        mask[j, :len(row)] = 1.0
    return torch.from_numpy(arr), torch.from_numpy(mask)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", choices=list(CSV_FILES.keys()), default=None)
    ap.add_argument("--epochs", type=int, default=45)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--lr", type=float, default=6e-4)
    ap.add_argument("--device", default=("cuda" if torch.cuda.is_available() else "cpu"))
    args = ap.parse_args()

    tasks = [args.task] if args.task else list(CSV_FILES.keys())
    device = torch.device(args.device)
    for task in tasks:
        t0 = time.time()
        df = pd.read_csv(os.path.join(find_data_dir(), CSV_FILES[task]))
        y = {st: np.asarray(df[df.stage == st].label, dtype=np.float32)
             for st in ["train", "valid", "test"]}
        tr, tr_lens, mtr = load_split(task, "train")
        va, va_lens, _ = load_split(task, "valid")
        te, te_lens, _ = load_split(task, "test")
        Ltr, Lva, Lte = mtr["seq_len"], va.shape[1], te.shape[1]
        print(f"\n[{task}] train {tr.shape} valid {va.shape} test {te.shape} "
              f"on {device}", flush=True)

        # standardization from train statistics (pooled over residues)
        mu = np.zeros(tr.shape[-1], dtype=np.float64)
        cnt = 0
        for i in range(len(tr)):
            l = int(tr_lens[i])
            mu += tr[i][:l].astype(np.float64).sum(0)
            cnt += l
        mu /= cnt
        var = np.zeros(tr.shape[-1], dtype=np.float64)
        for i in range(len(tr)):
            l = int(tr_lens[i])
            d = tr[i][:l].astype(np.float64) - mu
            var += (d ** 2).sum(0)
        var /= cnt
        std = np.sqrt(var + 1e-6)
        mu_t = torch.from_numpy(mu.astype(np.float32)).to(device)
        std_t = torch.from_numpy(std.astype(np.float32)).to(device)

        def transform(arr_t):
            return (arr_t - mu_t) / std_t

        model = ESMSeqHead().to(device)
        opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-3)
        mse = nn.MSELoss()
        n_tr = len(tr)
        idx_full = np.arange(n_tr)
        best = {"spearman": -1.0, "state": None, "epoch": 0}
        bad = 0
        for ep in range(args.epochs):
            model.train()
            np.random.shuffle(idx_full)
            running = 0.0
            for i in range(0, n_tr, args.batch):
                idx = idx_full[i:i + args.batch]
                xb, mb = sim_batch(tr, tr_lens, idx, args.batch, Ltr)
                xb = transform(xb.to(device))
                yb = torch.from_numpy(y["train"][idx]).to(device)
                opt.zero_grad()
                loss = mse(model(xb), yb)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step()
                running += loss.item() * len(idx)
            # validation (early stopping on rank correlation)
            model.eval()
            with torch.no_grad():
                preds_v = []
                for i in range(0, len(va), args.batch):
                    idx = np.arange(len(va))[i:i + args.batch]
                    xb, mb = sim_batch(va, va_lens, idx, args.batch, Lva)
                    preds_v.append(model(transform(xb.to(device))).cpu().numpy())
            pv = np.concatenate(preds_v)
            rv = float(spearmanr(pv, y["valid"]).correlation)
            if rv > best["spearman"]:
                best["spearman"] = rv
                best["epoch"] = ep + 1
                best["state"] = {k: v.clone() for k, v in model.state_dict().items()}
                bad = 0
            else:
                bad += 1
            if ep % 5 == 0 or ep == args.epochs - 1:
                print(f"  ep {ep+1:3d} loss={running/n_tr:.4f} valid_rho={rv:.4f} "
                      f"best={best['spearman']:.4f} (ep{best['epoch']})", flush=True)
            if bad >= 8:
                break

        model.load_state_dict(best["state"])
        model.eval()
        with torch.no_grad():
            preds_t = []
            for i in range(0, len(te), args.batch):
                idx = np.arange(len(te))[i:i + args.batch]
                xb, mb = sim_batch(te, te_lens, idx, args.batch, Lte)
                preds_t.append(model(transform(xb.to(device))).cpu().numpy())
        pt = np.concatenate(preds_t)
        rho = float(spearmanr(pt, y["test"]).correlation)
        rmse = float(np.sqrt(mean_squared_error(y["test"], pt)))

        row = {"task": task, "representation": "esm2-esm2_t33_650M",
               "model": "esm-seq-cnn-head", "spearman_rho": round(rho, 6),
               "rmse": round(rmse, 6), "n_test": int(len(te)),
               "epochs_run": ep + 1, "best_epoch": best["epoch"],
               "best_valid_spearman": round(best["spearman"], 6),
               "time_s": round(time.time() - t0, 1)}
        table = pd.read_csv(os.path.join(RESULTS_DIR, "evidence_table.csv"))
        print(f"\n[{task}] esm-seq-cnn-head test rho={rho:.4f} rmse={rmse:.4f} "
              f"(valid rho {best['spearman']:.4f}, {best['epoch']} epochs) "
              f"time={time.time()-t0:.0f}s", flush=True)

        # save test predictions into results/test_predictions_{task}.csv
        tp = os.path.join(RESULTS_DIR, f"test_predictions_{task}.csv")
        pdf = pd.read_csv(tp) if os.path.isfile(tp) else None
        np.save(os.path.join(RESULTS_DIR, f"seq_head_pred_{task}.npy"), pt)
        row["pred_file"] = f"seq_head_pred_{task}.npy"
        table = pd.concat([table, pd.DataFrame([row])], ignore_index=True)
        table.to_csv(os.path.join(RESULTS_DIR, "evidence_table.csv"), index=False)

        figdir = os.path.join(os.path.dirname(RESULTS_DIR), "evidence", "figures")
        os.makedirs(figdir, exist_ok=True)
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.figure(figsize=(4.5, 4.2))
        plt.scatter(y["test"][::10], pt[::10], s=4, alpha=0.4)
        plt.xlabel("true label"); plt.ylabel("predicted")
        plt.title(f"{task}: esm-seq-cnn-head, rho={rho:.3f}")
        plt.tight_layout()
        plt.savefig(os.path.join(figdir, f"scatter_seqhead_{task}.png"), dpi=150)
        plt.close()
        del tr, va, te

    import make_metrics
    make_metrics.main()


if __name__ == "__main__":
    main()