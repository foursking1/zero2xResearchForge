"""Compute and cache per-residue ESM-2 650M hidden states (fp16 memmap) for each split.

Writes under results/seqcache/:
  {task}_{split}_feats.dat (float16 memmap, n x L_padded x 1280)  -- last-layer hidden states
  {task}_{split}_lens.npy  (int32 sequence lengths)
  {task}_{split}_meta.json

Only sequences are embedded; labels are never touched.
Hidden states include only residue positions (special <cls>/<eos> tokens removed).
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import torch
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import CSV_FILES, RESULTS_DIR, SEED, find_data_dir  # noqa: E402

MODEL = "facebook/esm2_t33_650M_UR50D"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
torch.manual_seed(SEED)
CACHE = os.path.join(RESULTS_DIR, "seqcache")
SPECIAL_IDS = {0, 1, 2}  # <cls>, <pad>, <eos>


@torch.inference_mode()
def featurize(model, tokenizer, seqs, batch=32):
    out_feats = []
    out_lens = []
    for i in tqdm(range(0, len(seqs), batch), leave=False):
        chunk = list(seqs[i:i + batch])
        enc = tokenizer(chunk, padding=True, truncation=True, max_length=1024,
                        return_tensors="pt")
        enc = {k: v.to(DEVICE) for k, v in enc.items()}
        h = model(input_ids=enc["input_ids"], attention_mask=enc["attention_mask"])
        hidden = h.last_hidden_state.half()  # (B, L, 1280)
        ids = enc["input_ids"]
        L = hidden.shape[1]
        # keep per-residue positions only
        feat = torch.zeros(len(chunk), L, hidden.shape[-1], dtype=torch.float16,
                           device=DEVICE)
        for j in range(len(chunk)):
            pos = (ids[j] >= N_AA_OFFSET).nonzero().flatten()
            feat[j, :len(pos)] = hidden[j, pos]
        out_feats.append(feat.float().cpu().numpy())
        out_lens.append(((ids >= N_AA_OFFSET).sum(1).cpu().numpy()))
    maxL = max(int(x) for x in np.concatenate(out_lens))
    all_f = np.zeros((len(seqs), maxL, hidden.shape[-1]), dtype=np.float16)
    off = 0
    for f, lens in zip(out_feats, out_lens):
        n = len(lens)
        for j in range(n):
            all_f[off + j, :lens[j]] = f[j][:lens[j]]
        off += n
    return all_f, np.concatenate(out_lens).astype(np.int32)


N_AA_OFFSET = 4  # ESM-2: token ids >=4 are the 20 standard amino acids


def main():
    from transformers import AutoModel, AutoTokenizer
    os.makedirs(CACHE, exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModel.from_pretrained(MODEL).to(DEVICE).eval().half()
    data_dir = find_data_dir()

    for task in CSV_FILES:
        df = pd.read_csv(os.path.join(data_dir, CSV_FILES[task]))
        for split in ["train", "valid", "test"]:
            sub = df[df.stage == split].reset_index(drop=True)
            meta_f = os.path.join(CACHE, f"{task}_{split}_meta.json")
            if os.path.isfile(meta_f) and os.path.isfile(os.path.join(CACHE, f"{task}_{split}_feats.dat")):
                print(f"[skip] {task}/{split} cached"); continue
            t0 = time.time()
            feats, lens = featurize(model, tokenizer, sub["protein"].tolist())
            arr = np.lib.format.open_memmap(
                os.path.join(CACHE, f"{task}_{split}_feats.dat"),
                mode="w+", dtype=np.float16, shape=feats.shape)
            arr[:] = feats
            del arr
            np.save(os.path.join(CACHE, f"{task}_{split}_lens.npy"), lens)
            json.dump({"task": task, "split": split, "n": len(sub),
                       "seq_len": int(feats.shape[1]), "dim": 1280,
                       "model": MODEL}, open(meta_f, "w"), indent=1)
            print(f"[done] {task}/{split}: {feats.shape} in {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()