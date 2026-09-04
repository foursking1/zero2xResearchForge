"""Q2/Q3 anchor: DeepDTA-like 1D-CNN (ligand SMILES + protein sequence
one-hot -> scalar pK), retrained under the LP time split and, as leakage
control, under an equally sized random split (seed 0).

Protocol (mirrors paper Table 1 "DeepDTA"):
  * train on LP train / CL1 & non-covalent, early-stop on LP val
    (CL1 & non-covalent), evaluate on LP test CL2 non-covalent (2171).
  * random-split control evaluated on the SAME LP test CL2 non-covalent subset.

Outputs:
  results/evidence_table.csv (cnn rows)
  results/metrics_cnn.json
  results/predictions_cnn_<split>.csv
"""
import os
import sys
import json
import random
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

OUT = os.path.join(common.ROOT, "agent_solution", "results")
SEED = common.SEED
DEVICE = torch.device("cpu")
MAX_SMI = 100
MAX_SEQ = 800
BATCH = 128
MAX_EPOCHS = 40

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)


SMI_CHARS = list("CNcnOSosPHFfIbB#()/=@+\\[]-%0123456789.:;'np*Gg") + [" "]
SMI_VOCAB = {c: i for i, c in enumerate(sorted(set(SMI_CHARS)), start=1)}


def build_seq_tokenizer(seqs):
    chars = "".join(sorted(set("".join(seqs))))
    # restrict to 20 standard amino acids + X  -> keep index 0 as padding
    keep = "ACDEFGHIKLMNPQRSTVWYX"
    keep_idx = {c: i + 1 for i, c in enumerate(keep)}
    idx = {c: keep_idx.get(c, 0) for c in chars}
    return idx


def encode_seq(seq, tok, maxlen):
    v = np.zeros(maxlen, dtype=np.int64)
    n = min(len(seq), maxlen)
    for i in range(n):
        v[i] = tok.get(seq[i], 0)
    return v


def encode_smi(smi, maxlen=MAX_SMI):
    v = np.zeros(maxlen, dtype=np.int64)
    n = min(len(smi), maxlen)
    for i in range(n):
        v[i] = SMI_VOCAB.get(smi[i], 0)
    return v


class DeepDTA(nn.Module):
    def __init__(self, n_smi=len(SMI_VOCAB) + 1, n_seq=22, emb=128, filters=32):
        super().__init__()
        self.emb_smi = nn.Embedding(n_smi, emb, padding_idx=0)
        self.emb_seq = nn.Embedding(n_seq, emb, padding_idx=0)
        self.conv1 = nn.Conv1d(emb, filters, kernel_size=8, padding=4)
        self.conv2 = nn.Conv1d(filters, filters * 2, kernel_size=8, padding=4)
        self.conv3 = nn.Conv1d(filters * 2, filters * 4, kernel_size=4, padding=2)
        self.fc1 = nn.Linear(filters * 4 * 2, 512)
        self.fc2 = nn.Linear(512, 1)
        self.drop = nn.Dropout(0.2)
        self.relu = nn.ReLU()

    def forward(self, smi, seq):
        a = self.emb_smi(smi).permute(0, 2, 1)
        b = self.emb_seq(seq).permute(0, 2, 1)
        for conv in (self.conv1, self.conv2, self.conv3):
            a = self.relu(conv(a))
            b = self.relu(conv(b))
        a = a.max(dim=2).values
        b = b.max(dim=2).values
        h = torch.cat([a, b], dim=1)
        h = self.relu(self.fc1(h))
        h = self.drop(h)
        return self.fc2(h).squeeze(1)


def collate(Xsmi, Xseq):
    return torch.tensor(Xsmi, dtype=torch.long), torch.tensor(Xseq, dtype=torch.long)


def to_tensor(arr):
    return torch.tensor(arr, dtype=torch.long)


def run_fold(df, split_type, te_smi, te_seq, y_te, te_ok, te_pdb):
    if split_type == "time":
        split_df = df
    else:
        split_df = common.add_random_split(df, seed=SEED)
    trn = common.select_cl1_noncov(split_df[split_df["split"] == "train"])
    va = common.select_cl1_noncov(split_df[split_df["split"] == "val"])

    seq_tok = build_seq_tokenizer(trn["seq"].tolist() + va["seq"].tolist())

    Xs_tr = np.vstack([encode_smi(s) if isinstance(s, str) else np.zeros(MAX_SMI, dtype=np.int64) for s in trn["smiles"]])
    Xq_tr = np.vstack([encode_seq(s, seq_tok, MAX_SEQ) for s in trn["seq"]])
    y_tr = trn["pki"].values.astype(np.float32)

    Xs_va = np.vstack([encode_smi(s) if isinstance(s, str) else np.zeros(MAX_SMI, dtype=np.int64) for s in va["smiles"]])
    Xq_va = np.vstack([encode_seq(s, seq_tok, MAX_SEQ) for s in va["seq"]])
    y_va = va["pki"].values.astype(np.float32)

    # canonicalise the test-side SMILES for encoding (same encoding function)
    Xs_te = te_smi
    Xq_te = te_seq

    model = DeepDTA().to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    lossf = nn.MSELoss()

    n = len(y_tr)
    best_val = float("inf")
    best_state = None
    patience = 0
    t0 = time.time()
    for epoch in range(MAX_EPOCHS):
        model.train()
        perm = np.random.permutation(n)
        tot = 0.0
        for i in range(0, n, BATCH):
            idx = perm[i:i + BATCH]
            s, q = collate(Xs_tr[idx], Xq_tr[idx])
            yb = torch.tensor(y_tr[idx])
            opt.zero_grad()
            loss = lossf(model(s, q), yb)
            loss.backward()
            opt.step()
            tot += loss.item() * len(idx)
        # validation
        model.eval()
        with torch.no_grad():
            pv = np.concatenate([model(s, q).numpy() for s, q in
                                 zip(torch.split(to_tensor(Xs_va), 512), torch.split(to_tensor(Xq_va), 512))])
        rv = common.rmse(y_va, pv)
        if rv < best_val:
            best_val = rv
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            patience = 0
        else:
            patience += 1
        if epoch % 5 == 0 or patience >= 6:
            print(f"  [{split_type}] ep {epoch} train_loss={tot / n:.4f} val_rmse={rv:.3f} time={time.time()-t0:.0f}s")
        if patience >= 6:
            break

    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        pt = np.concatenate([model(s, q).numpy() for s, q in
                             zip(torch.split(to_tensor(Xs_te), 512), torch.split(to_tensor(Xq_te), 512))])
    pt = pt[te_ok]
    rmse_te = common.rmse(y_te, pt)
    r_te = common.pearson_r(y_te, pt)
    print(f"[CNN-{split_type}] test_rmse={rmse_te:.3f} R={r_te:.3f} (n={len(y_te)})")
    return {
        "split_type": split_type,
        "split_label": "Time-based split" if split_type == "time" else f"Random split (seed={SEED})",
        "model": "cnn_deepdta",
        "train_n": len(y_tr),
        "val_n": len(y_va),
        "rmse_train": float("nan"),
        "rmse_val": float(best_val),
        "rmse_test_cl2_noncov": rmse_te,
        "pearson_r": r_te,
        "n_test_cl2_noncov": int(len(y_te)),
    }, pd.DataFrame({
        "pdb_id": te_pdb[te_ok],
        "y_true": y_te,
        "y_pred": pt,
    })


def main():
    os.makedirs(OUT, exist_ok=True)
    df = common.load_lp_data()

    te = df[(df["split"] == "test") & (df["CL2"].astype(str) == "True")
            & (df["covalent"].astype(str) == "False")].copy()
    te_smi = np.array([encode_smi(s) for s in te["smiles"]])
    # seq tokenizer built ONLY from train/val data (no test seqs)
    seq_tok = build_seq_tokenizer(df[df["split"].isin(["train", "val"])]["seq"].tolist())
    te_seq = np.vstack([encode_seq(s, seq_tok, MAX_SEQ) for s in te["seq"]])
    y_te = te["pki"].values.astype(np.float32)
    assert len(y_te) == common.TEST_CL2_NONCOV_N

    rows = []
    for split_type in ["time", "random"]:
        rec, pdf = run_fold(df, split_type, te_smi, te_seq, y_te, np.ones(len(y_te), dtype=bool), te["pdb_id"].values)
        rows.append(rec)
        pdf.to_csv(os.path.join(OUT, f"predictions_cnn_{split_type}.csv"), index=False)

        # incremental checkpoint
        ev_path = os.path.join(OUT, "evidence_table.csv")
        ev = pd.DataFrame(rows)
        if os.path.exists(ev_path):
            prev = pd.read_csv(ev_path)
            prev = prev[prev["model"] != "cnn_deepdta"]
            ev = pd.concat([prev, ev], ignore_index=True)
        ev.to_csv(ev_path, index=False)
        with open(os.path.join(OUT, "metrics_cnn.json"), "w") as f:
            json.dump(rows, f, indent=2)

    print("CNN done.")


if __name__ == "__main__":
    main()