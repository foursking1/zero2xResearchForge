"""Evaluate a saved DNABERT-2+LoRA best checkpoint on the frozen test split.

This is the exact-reproduction path: the reported evidence numbers come from
the same training + this evaluation. Loading a checkpoint and evaluating the
test split takes only a few minutes even on CPU.

Usage:
    python3 eval_checkpoint.py --dataset prom_300_all [--device cpu]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch
from torch.utils.data import DataLoader, TensorDataset
from transformers import AutoTokenizer
from transformers.models.bert.configuration_bert import BertConfig as HFBertConfig

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_utils import TASK_METRIC, find_data_dir, load_dataset  # noqa: E402
from eval_metrics import evaluate  # noqa: E402

from peft import LoraConfig, TaskType, get_peft_model  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, choices=["EMP_H3", "mouse_0", "prom_300_all", "prom_core_all"])
    ap.add_argument("--model_path", default="zhihan1996/DNABERT-2-117M")
    ap.add_argument("--ckpt", default="results/models/{dataset}/best_lora_state.pt")
    ap.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"])
    ap.add_argument("--batch_size", type=int, default=16)
    ap.add_argument("--max_length", type=int, default=128)
    args = ap.parse_args()

    if args.device == "auto":
        args.device = "cuda" if torch.cuda.is_available() else "cpu"
    device = torch.device(args.device)

    ckpt_path = Path(args.ckpt.format(dataset=args.dataset))
    data = load_dataset(find_data_dir(), args.dataset)
    _, te_y = data["test"]

    tok = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
    cfg = HFBertConfig.from_pretrained(args.model_path, num_labels=2, attention_probs_dropout_prob=0.15)

    from transformers import AutoModelForSequenceClassification

    base = AutoModelForSequenceClassification.from_pretrained(args.model_path, config=cfg, trust_remote_code=True)
    lora_cfg = LoraConfig(
        task_type=TaskType.SEQ_CLS, r=16, lora_alpha=32, lora_dropout=0.05,
        target_modules=["Wqkv", "gated_layers", "wo"], bias="none",
    )
    model = get_peft_model(base, lora_cfg)
    ckpt = torch.load(ckpt_path, map_location=device)
    model.load_state_dict(ckpt["state"])
    model.to(device).eval()

    enc = tok(data["test"][0], padding="max_length", max_length=args.max_length, truncation=True, return_tensors="pt")
    loader = DataLoader(TensorDataset(enc["input_ids"], enc["attention_mask"], torch.tensor(te_y, dtype=torch.long)),
                        batch_size=args.batch_size)
    yt, yp = [], []
    t0 = time.time()
    with torch.no_grad():
        for ids, msk, lab in loader:
            ids, msk = ids.to(device), msk.to(device)
            logits = model(input_ids=ids, attention_mask=msk).logits
            yt.extend(lab.tolist()); yp.extend(logits.argmax(-1).tolist())
    met = TASK_METRIC[args.dataset]
    res = evaluate(yt, yp, met)
    print(f"[{args.dataset}] recomputed test {met}={res[met]} acc={res['acc']} f1={res['f1']} mcc={res['mcc']} ({time.time()-t0:.0f}s)")
    print(json.dumps(res))


if __name__ == "__main__":
    main()