"""DNABERT-2-117M fine-tuning on the 4 frozen GUE tasks with LoRA.

Protocol (aligned with the DNABERT-2 paper's fine-tuning convention):
  - tokenizer/model: zhihan1996/DNABERT-2-117M (BPE, trust_remote_code);
    the checkpoint's custom config class is replaced by the equivalent
    transformers BertConfig so that loading works with the installed
    transformers version (weights themselves are untouched).
  - adapter: LoRA (r=16, alpha=32) on attention Wqkv / MLP wo / gated_layers
    + a fresh classification head; backbone weights frozen.
  - training: cross-entropy, AdamW, linear LR schedule with warmup,
    early stopping on the validation primary metric (MCC for EMP_H3 /
    mouse_0, macro-F1 for the two promoter tasks), fixed seed=42.
  - data discipline: only the frozen train/val/test splits are used;
    the test split is touched only for final evaluation.

Single-task CLI entry; a driver script loops over all tasks.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import f1_score, matthews_corrcoef
from torch.utils.data import DataLoader, TensorDataset
from transformers import AutoTokenizer
from transformers.optimization import get_linear_schedule_with_warmup
from transformers.models.bert.configuration_bert import BertConfig as HFBertConfig

from peft import LoraConfig, TaskType, get_peft_model

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_utils import TASK_METRIC, find_data_dir, load_dataset  # noqa: E402
from eval_metrics import evaluate  # noqa: E402


def seed_everything(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def tokenize(tok, seqs, max_length: int):
    enc = tok(
        seqs,
        padding="max_length",
        max_length=max_length,
        truncation=True,
        return_tensors="pt",
    )
    return enc["input_ids"], enc["attention_mask"]


def make_loader(ids, mask, labels, bs: int, shuffle: bool):
    ds = TensorDataset(ids, mask, torch.tensor(labels, dtype=torch.long))
    g = torch.Generator().manual_seed(42) if shuffle else None
    return DataLoader(ds, batch_size=bs, shuffle=shuffle, generator=g)


def val_primary(model, loader, task_metric: str, device):
    model.eval()
    yt, yp = [], []
    with torch.no_grad():
        for ids, msk, lab in loader:
            ids, msk = ids.to(device), msk.to(device)
            logits = model(input_ids=ids, attention_mask=msk, return_dict=True).logits
            yt.extend(lab.tolist())
            yp.extend(logits.argmax(dim=-1).tolist())
    return evaluate(yt, yp, task_metric), yt, yp


def run_task(args, ds: str, device, weights_cache_args=None):
    data_dir = Path(args.data_dir) if args.data_dir else find_data_dir()
    data = load_dataset(data_dir, ds)
    tr_seqs, tr_y = data["train"]
    va_seqs, va_y = data["val"]
    te_seqs, te_y = data["test"]

    if args.max_train and len(tr_seqs) > args.max_train:
        rng = np.random.RandomState(args.seed)
        keep = rng.choice(len(tr_seqs), args.max_train, replace=False)
        tr_seqs = [tr_seqs[i] for i in keep]
        tr_y = [tr_y[i] for i in keep]

    tok = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
    cfg = HFBertConfig.from_pretrained(
        args.model_path, num_labels=2, attention_probs_dropout_prob=args.attn_dropout
    )
    from transformers import AutoModelForSequenceClassification

    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_path, config=cfg, trust_remote_code=True
    )
    lora_cfg = LoraConfig(
        task_type=TaskType.SEQ_CLS,
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=args.targets,
        bias="none",
    )
    model = get_peft_model(model, lora_cfg)
    model = model.to(device)

    train_ids, train_mask = tokenize(tok, tr_seqs, args.max_length)
    val_ids, val_mask = tokenize(tok, va_seqs, args.max_length)
    test_ids, test_mask = tokenize(tok, te_seqs, args.max_length)

    train_loader = make_loader(train_ids, train_mask, tr_y, args.batch_size, shuffle=True)
    val_loader = make_loader(val_ids, val_mask, va_y, args.batch_size, shuffle=False)

    task_metric = TASK_METRIC[ds]
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr)
    steps_total = len(train_loader) * args.epochs
    sched = get_linear_schedule_with_warmup(
        opt, num_warmup_steps=int(0.06 * steps_total), num_training_steps=steps_total
    )

    best_val, best_state, stop_after = -1e9, None, 0
    history = []
    t_start = time.time()
    for ep in range(1, args.epochs + 1):
        model.train()
        tot_loss = 0.0
        for step, (ids, msk, lab) in enumerate(train_loader):
            ids, msk, lab = ids.to(device), msk.to(device), lab.to(device)
            opt.zero_grad()
            out = model(input_ids=ids, attention_mask=msk, labels=lab)
            out.loss.backward()
            torch.nn.utils.clip_grad_norm_(
                [p for p in model.parameters() if p.requires_grad and p.grad is not None], 1.0
            )
            opt.step()
            sched.step()
            tot_loss += out.loss.item()
        vac, yt, _ = val_primary(model, val_loader, task_metric, device)
        history.append({"epoch": ep, "val_primary": vac[task_metric], "val": vac, "loss": tot_loss / max(1, step + 1)})
        print(f"[{ds}] epoch {ep}: loss={history[-1]['loss']:.4f} val_{task_metric}={vac[task_metric]:.4f} ({time.time()-t_start:.0f}s)")
        if vac[task_metric] > best_val:
            best_val = vac[task_metric]
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            stop_after = 0
        else:
            stop_after += 1
            if stop_after >= args.patience:
                break

    # reload best, evaluate on TEST
    model.load_state_dict(best_state)
    vac, _, _ = val_primary(model, val_loader, task_metric, device)  # final val
    tec, te_yt, te_yp = val_primary(model, DataLoader(
        TensorDataset(test_ids, test_mask, torch.tensor(te_y, dtype=torch.long)),
        batch_size=args.batch_size), task_metric, device)

    result = {
        "dataset": ds,
        "model": "dnabert2_117m",
        "method": f"dnabert2_lora_r{args.lora_r}",
        "train_n": len(tr_seqs), "val_n": len(va_seqs), "test_n": len(te_seqs),
        "epochs_run": len(history),
        "best_epoch": int(np.argmax([h["val_primary"] for h in history])) + 1,
        "trainable_params": int(sum(p.numel() for p in model.parameters() if p.requires_grad)),
        "primary_metric": task_metric,
        "val": vac,
        "test": tec,
        "history": history,
        "time_s": round(time.time() - t_start, 1),
        "seed": args.seed,
        "lr": args.lr,
    }
    return result, best_state


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, choices=["EMP_H3", "mouse_0", "prom_300_all", "prom_core_all"])
    ap.add_argument("--data_dir", default=None)
    ap.add_argument("--model_path", default="zhihan1996/DNABERT-2-117M")
    ap.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--patience", type=int, default=2)
    ap.add_argument("--batch_size", type=int, default=16)
    ap.add_argument("--max_length", type=int, default=512)
    ap.add_argument("--max_train", type=int, default=0, help="0 = use full frozen train split")
    ap.add_argument("--attn_dropout", type=float, default=0.15)
    ap.add_argument("--lora_r", type=int, default=16)
    ap.add_argument("--lora_alpha", type=int, default=32)
    ap.add_argument("--lora_dropout", type=float, default=0.05)
    ap.add_argument("--targets", nargs="+", default=["Wqkv", "gated_layers", "wo"])
    ap.add_argument("--out", default="results/finetune")
    ap.add_argument("--run_tag", default="full")
    ap.add_argument("--save_dir", default="results/models", help="dir to store best LoRA state_dict checkpoint")
    args = ap.parse_args()

    if args.device == "auto":
        args.device = "cuda" if torch.cuda.is_available() else "cpu"
    seed_everything(args.seed)

    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    res, best_state = run_task(args, args.dataset, args.device)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = args.run_tag
    (out_dir / f"{args.dataset}_{tag}_metrics.json").write_text(json.dumps(res, indent=2))
    ckpt_dir = Path(args.save_dir) / args.dataset
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {"state": best_state, "seed": args.seed, "metric": res["primary_metric"], "test": res["test"]},
        ckpt_dir / "best_lora_state.pt",
    )
    print(f"wrote {out_dir / f'{args.dataset}_{tag}_metrics.json'}")
    print(f"wrote checkpoint {ckpt_dir / 'best_lora_state.pt'}")
    print(json.dumps({"dataset": args.dataset, "test": res["test"]}, indent=1))


if __name__ == "__main__":
    main()