"""Compute ESM-2 embeddings (mean-pooled last hidden state) for TAPE sequences.

Writes, per {task, model}:
  results/embeddings/{task}_{shortmodel}_embeddings.npy  (float32, n_seqs x dim)
  results/embeddings/{task}_{shortmodel}_order.json      (sequence list, same order)

Usage: python embed_esm.py [--model facebook/esm2_t6_8M_UR50D|facebook/esm2_t33_650M_UR50D]
                            [--task fluorescence|stability]
Defaults: all models on both tasks.

The pretrained weights are loaded from the local HuggingFace cache
(facebook/esm2_t6_8M_UR50D & facebook/esm2_t33_650M_UR50D). Only sequences are used --
never labels -- so no label leakage can occur from the embedding step.
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import CSV_FILES, EMBED_DIR, EMBEDDING_MODELS, MODEL_SHORT, SEED, find_data_dir  # noqa: E402

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
torch.manual_seed(SEED)

MAX_TOKENS = 1024  # ESM-2 truncation length (all TAPE sequences are far shorter)


@torch.inference_mode()
def embed_batch(model, tokenizer, batch_seqs):
    enc = tokenizer.batch_encode_plus(
        list(batch_seqs),
        add_special_tokens=True,
        padding=True,
        truncation=True,
        max_length=MAX_TOKENS,
        return_tensors="pt",
    )
    enc = {k: v.to(DEVICE) for k, v in enc.items()}
    seq_ids = enc["input_ids"]
    mask = enc["attention_mask"].float()
    out = model(input_ids=seq_ids, attention_mask=enc["attention_mask"])
    hidden = out.last_hidden_state  # (B, L, D) fp16 under autocast
    mask3 = mask.unsqueeze(-1)
    pooled = (hidden * mask3).sum(1) / (mask3.sum(1) + 1e-8)
    return pooled.float().cpu().numpy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=EMBEDDING_MODELS, default=None)
    ap.add_argument("--task", choices=list(CSV_FILES.keys()), default=None)
    ap.add_argument("--batch", type=int, default=128)
    args = ap.parse_args()

    models = [args.model] if args.model else EMBEDDING_MODELS
    tasks = [args.task] if args.task else list(CSV_FILES.keys())

    data_dir = find_data_dir()
    os.makedirs(EMBED_DIR, exist_ok=True)

    for model_name in models:
        from transformers import AutoModel, AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
        model = model.to(DEVICE).eval()
        if DEVICE == "cuda":
            model.half()  # fp16 forward for speed / reduced memory

        for task in tasks:
            df = pd.read_csv(os.path.join(data_dir, CSV_FILES[task]))
            seqs = df["protein"].tolist()
            short = MODEL_SHORT[model_name]
            out_arr = os.path.join(EMBED_DIR, f"{task}_{short}_embeddings.npy")
            out_json = os.path.join(EMBED_DIR, f"{task}_{short}_order.json")
            if os.path.isfile(out_arr) and os.path.isfile(out_json):
                print(f"[skip] {task}/{short} already embedded")
                continue

            all_vecs = []
            t0 = time.time()
            for i in range(0, len(seqs), args.batch):
                batch = seqs[i:i + args.batch]
                all_vecs.append(embed_batch(model, tokenizer, batch))
                if i // args.batch % 20 == 0 and i > 0:
                    print(f"  {task}/{model_name} {i}/{len(seqs)} "
                          f"{time.time()-t0:.0f}s", flush=True)
            arr = np.concatenate(all_vecs, axis=0).astype(np.float32)
            np.save(out_arr, arr)
            with open(out_json, "w") as fh:
                json.dump({"order": seqs, "model": model_name, "task": task,
                           "device": DEVICE, "n": len(seqs),
                           "dim": int(arr.shape[1])}, fh, indent=1)
            print(f"[done] {task}/{model_name}: {arr.shape}, "
                  f"{time.time()-t0:.0f}s -> {out_arr}", flush=True)


if __name__ == "__main__":
    main()