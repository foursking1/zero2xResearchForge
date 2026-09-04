"""Step 3 — From-scratch sequence encoders: 1D CNN and BiLSTM.

Both models are trained from scratch on /data/solubility_train.csv only
(sequence input, cross-entropy loss, AdamW, every hyper-parameter chosen on the
validation split). Each model is trained 3 times with fixed seeds and reported
as mean +/- std, mirroring the paper's mean(std) table.

Protocol:
  * amino-acid indices (20 letters) -> learned embedding (dim 128)
  * sequences truncated to max_len=512 / padded with the pad token (see report);
  * early stopping on validation accuracy (patience 4, max 12 epochs);
  * the test split is used exactly once at the end with the best checkpoint
    (best validation accuracy highlighted epoch).

Determinism: fixed seeds, cudnn.deterministic=True, benchmark=False.
"""
import os
import json
import time
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from common import (
    load_split, ensure_dir, save_json, set_seed, get_device,
    seq_to_ids, accuracy_from_logits, AA2IDX,
)

SEED = 2024
HERE = os.path.dirname(__file__)
RESULTS = ensure_dir(os.path.join(HERE, "..", "results"))

MAX_LEN = 512
EMB_DIM = 128
BATCH = 256
EPOCHS = 12
PATIENCE = 4
LR = 1e-3
WEIGHT_DECAY = 1e-4
N_SEEDS = 3
SEEDS = [SEED, SEED + 1, SEED + 2]


class ProteinDataset(Dataset):
    """Deterministic dataset: the whole split is pre-encoded ONCE into an
    int16 array of shape (n, max_len); __getitem__ returns a row slice.
    num_workers is forced to 0 so batch order is exactly the seeded sequential
    sampler order (multi-worker loaders reorder batches by worker completion
    time, which destroys bit-exact reproducibility across runs)."""

    def __init__(self, seqs, labels, max_len):
        import numpy as np

        n = len(seqs)
        self.max_len = max_len
        self.x = np.zeros((n, max_len), dtype=np.int16) + 20
        self.lengths = np.zeros(n, dtype=np.int16)
        for i, s in enumerate(seqs):
            ids = seq_to_ids(s, max_len)
            self.x[i, : len(ids)] = ids
            self.lengths[i] = len(ids)
        self.labels = np.array(labels, dtype=np.int64)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, i):
        return (self.x[i].copy(), int(self.lengths[i]), int(self.labels[i]))


class CNNModel(nn.Module):
    def __init__(self, num_classes=2):
        super().__init__()
        self.emb = nn.Embedding(21, EMB_DIM, padding_idx=20)
        self.conv = nn.Sequential(
            nn.Conv1d(EMB_DIM, 128, 7, padding=3), nn.ReLU(),
            nn.MaxPool1d(3, stride=2),
            nn.Conv1d(128, 192, 5, padding=2), nn.ReLU(),
            nn.MaxPool1d(3, stride=2),
            nn.Conv1d(192, 192, 3, padding=1), nn.ReLU(),
        )
        self.drop = nn.Dropout(0.2)
        self.head = nn.Linear(192, num_classes)

    def forward(self, x, lengths=None):
        e = self.emb(x).transpose(1, 2)          # N, C, L
        h = self.conv(e)
        h = h.max(dim=2).values                   # global max pooling
        return self.head(self.drop(h))


class LSTMNet(nn.Module):
    def __init__(self, hidden=128, num_layers=1, num_classes=2):
        super().__init__()
        self.emb = nn.Embedding(21, EMB_DIM, padding_idx=20)
        self.lstm = nn.LSTM(EMB_DIM, hidden, num_layers=num_layers,
                            bidirectional=True, batch_first=True)
        self.drop = nn.Dropout(0.2)
        self.head = nn.Linear(2 * hidden, num_classes)

    def forward(self, x, lengths):
        e = self.emb(x)
        packed = nn.utils.rnn.pack_padded_sequence(
            e, lengths.detach().cpu(), batch_first=True, enforce_sorted=False)
        out, _ = self.lstm(packed)
        out, _ = nn.utils.rnn.pad_packed_sequence(out, batch_first=True)
        T = out.size(1)
        mask = torch.arange(T, device=x.device).unsqueeze(0) < lengths.unsqueeze(1)
        pooled = (out * mask.unsqueeze(-1)).sum(1) / mask.float().sum(1, keepdim=True)
        return self.head(self.drop(pooled))


def _init(module):
    for name, p in module.named_parameters():
        if "lstm" in name:
            if "weight_ih" in name:
                nn.init.xavier_uniform_(p)
            elif "weight_hh" in name:
                nn.init.orthogonal_(p)
            elif "bias" in name:
                nn.init.zeros_(p)
        elif "weight" in name and p.dim() >= 2:
            nn.init.xavier_uniform_(p)
        elif "bias" in name:
            nn.init.zeros_(p)


def train_once(model, dataloaders, device, seed, label):
    set_seed(seed)
    train_dl, valid_dl, test_dl = dataloaders
    model.apply(_init)
    model.to(device)

    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(
        opt, mode="max", factor=0.5, patience=2)
    lossf = nn.CrossEntropyLoss()

    best_acc, best_epoch, best_state = -1.0, -1, None
    history = []
    for ep in range(1, EPOCHS + 1):
        model.train()
        t0 = time.time()
        for x, l, y in train_dl:
            x, l, y = x.long().to(device), l.to(device), y.to(device)
            opt.zero_grad()
            logits = model(x, l)
            loss = lossf(logits, y)
            loss.backward()
            opt.step()
        model.eval()
        v_acc, val_loss = eval_acc_loss(model, valid_dl, lossf, device)
        sched.step(v_acc)
        history.append({"epoch": ep, "valid_acc": round(v_acc * 100, 4),
                        "valid_loss": round(val_loss, 5),
                        "train_time_s": round(time.time() - t0, 1)})
        flag = ""
        if v_acc > best_acc:
            best_acc, best_epoch = v_acc, ep
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            flag = " *"
        print(f"  [{label} seed={seed}] ep {ep:2d} val_acc={v_acc*100:6.2f}%  "
              f"val_loss={val_loss:.4f}  {time.time()-t0:.1f}s{flag}")

        if ep - best_epoch >= PATIENCE:
            print(f"    early stop at epoch {ep} (best ep {best_epoch})")
            break

    model.load_state_dict(best_state)
    test_acc = eval_acc(model, test_dl, device)
    print(f"  => {label} seed={seed}: TEST acc={test_acc*100:.4f}% "
          f"(best valid ep={best_epoch})")
    return {"seed": seed, "best_valid_acc_pct": round(best_acc * 100, 4),
            "best_epoch": best_epoch, "test_acc_pct": round(test_acc * 100, 4),
            "history": history}


def eval_acc(model, dl, device):
    model.eval()
    c = t = 0
    with torch.no_grad():
        for x, l, y in dl:
            x, l, y = x.long().to(device), l.to(device), y.to(device)
            preds = model(x, l).argmax(dim=1)
            t += y.numel()
            c += (preds == y).sum().item()
    return c / t


def eval_acc_loss(model, dl, lossf, device):
    model.eval()
    c = t = 0
    tot = 0.0
    with torch.no_grad():
        for x, l, y in dl:
            x, l, y = x.long().to(device), l.to(device), y.to(device)
            logits = model(x, l)
            tot += lossf(logits, y).item() * y.numel()
            preds = logits.argmax(dim=1)
            t += y.numel()
            c += (preds == y).sum().item()
    return c / t, tot / max(t, 1)


def run_model(name, model_cls, train, valid, test, device, workers):
    workers = 0  # deterministic loads (see ProteinDataset docstring)
    tr_dl = DataLoader(ProteinDataset(train["sequence"].tolist(),
                                      train["label"].values, MAX_LEN),
                       batch_size=BATCH, shuffle=True, num_workers=0,
                       generator=torch.Generator().manual_seed(SEED))
    va_dl = DataLoader(ProteinDataset(valid["sequence"].tolist(),
                                      valid["label"].values, MAX_LEN),
                       batch_size=BATCH, shuffle=False, num_workers=0)
    te_dl = DataLoader(ProteinDataset(test["sequence"].tolist(),
                                      test["label"].values, MAX_LEN),
                       batch_size=BATCH, shuffle=False, num_workers=0)

    runs = []
    for seed in SEEDS:
        runs.append(train_once(model_cls(), [tr_dl, va_dl, te_dl], device,
                               seed, name))
    accs = np.array([r["test_acc_pct"] for r in runs])
    valid_accs = np.array([r["best_valid_acc_pct"] for r in runs])
    return {
        "seeds": SEEDS,
        "test_acc_pct": round(float(accs.mean()), 4),
        "test_acc_std": round(float(accs.std()), 4),
        "test_accs_per_seed_pct": [round(a, 4) for a in accs.tolist()],
        "best_valid_acc_pct": round(float(valid_accs.mean()), 4),
        "best_valid_acc_std": round(float(valid_accs.std()), 4),
        "runs": runs,
    }


def main():
    set_seed(SEED)
    device, workers = get_device()
    print(f"[encoders] device={device} workers={workers} threads="
          f"{torch.get_num_threads()}")
    torch.set_num_threads(20 if torch.cuda.is_available() else 12)

    train = load_split("train")
    valid = load_split("valid")
    test = load_split("test")

    results = {}
    results["max_len"] = MAX_LEN
    results["device"] = str(device)

    results["CNN"] = run_model("CNN", CNNModel, train, valid, test, device, workers)
    results["LSTM"] = run_model("LSTM", lambda: LSTMNet(hidden=128),
                                train, valid, test, device, workers)

    save_json(results, os.path.join(RESULTS, "encoder_model_results.json"))
    summary = {}
    for k, v in results.items():
        if isinstance(v, dict):
            summary[k] = {kk: vv for kk, vv in v.items() if kk != "runs"}
        else:
            summary[k] = v
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()