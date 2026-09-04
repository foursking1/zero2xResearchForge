"""Zero-shot protein LM scoring.

Two modes (both masked-marginal over ESM-2 masked LMs):

  tables (default): a single masked forward per *position* of the target
      sequence builds a log-prob table L[p][aa].  A variant is scored as
      sum_i (L[p_i][mut_i] - L[p_i][wt_i]) over its mutated positions
      (independent-site approximation, exact for single mutants).

  joint: a masked forward per *unique mutation mask* of the variant set
      (all mutated positions masked simultaneously).  Exact masked marginal
      for multi-mutants too.  Costly when unique masks >> sequence length
      (e.g. GFP multi-mutants), so `tables` is the default.

Log-probs are computed from a softmax over the 20 canonical amino acids
(ProteinGym / ESM convention).  Models are ESM-2 family
(facebook/esm2_t6_8M_UR50D, facebook/esm2_t33_650M_UR50D).

Usage:
  python 01_score_lm.py --mode tables --models esm2_t33_650M
  python 01_score_lm.py --mode joint  --assays GFP_AEQVI_Sarkisyan_2016
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

from common import AA20, AA_TO_IDX, ASSAYS, ROOT, get_target_seq, load_assay, load_reference

MODEL_NAMES = {
    "esm2_t6_8M": "facebook/esm2_t6_8M_UR50D",
    "esm2_t33_650M": "facebook/esm2_t33_650M_UR50D",
}


def aa_vocab_ids(tokenizer):
    """Vocab ids of the 20 canonical amino acids (in AA20 order).  The ESM
    tokenizer alphabet is NOT alphabetical, so this must come from the tokenizer."""
    from common import AA20
    return [tokenizer.convert_tokens_to_ids(c) for c in AA20]


def token_id_offsets(tokenizer, seq):
    """Return (ids, offset): offset = number of leading special tokens."""
    ids = tokenizer(seq, return_tensors="pt", add_special_tokens=True)["input_ids"][0]
    tokens = tokenizer.convert_ids_to_tokens(ids.tolist())
    offset = 0
    while tokens[offset] not in AA20:
        offset += 1
    n_eos = 1 if len(tokens) > offset and tokens[-1] == "<eos>" else 0
    assert len(seq) + offset + n_eos == len(ids), (len(seq), offset, n_eos, len(ids))
    return ids, offset


def best_batch(L, device, use_fp16):
    """Pick a batch size that keeps attention + hidden-state memory sane."""
    if device.type == "cpu":
        return 8
    if L > 800:
        return 16
    if L > 400:
        return 32
    # short sequences: memory-bound by hidden states (B*L*84500 bytes fp16 on 650M)
    return max(32, min(512, int(2.2e9 / max(1.0, L * 84500))))


@torch.no_grad()
def score_tables(model, tokenizer, seq, device, aa_cols, use_fp16):
    """Per-position masked-marginal tables over the full-length sequence."""
    ids, off = token_id_offsets(tokenizer, seq)
    L = len(ids)
    positions = list(range(off, L - 1))  # amino-acid token positions
    table = np.full((L, 20), -np.inf, dtype=np.float64)
    bs = best_batch(L, device, use_fp16)
    for b0 in range(0, len(positions), bs):
        chunk = positions[b0 : b0 + bs]
        flat = ids.unsqueeze(0).expand(len(chunk), -1).clone().to(device)
        for bi, p in enumerate(chunk):
            flat[bi, p] = tokenizer.mask_token_id
        attn = torch.ones(len(chunk), L, dtype=torch.long, device=device)
        logits = model(flat, attention_mask=attn)["logits"]
        if logits.dtype != torch.float32:
            logits = logits.float()
        lp = torch.log_softmax(logits, dim=-1)
        lp20 = lp[:, :, aa_cols]
        lp20 = lp20 - torch.logsumexp(lp20, dim=-1, keepdim=True)
        for bi, p in enumerate(chunk):
            table[p] = lp20[bi, p].cpu().numpy()
    return table, off


@torch.no_grad()
def score_joint(model, tokenizer, seq, device, aa_cols, use_fp16, df):
    """Joint masked-marginal: one forward per unique mutation mask."""
    ids, off = token_id_offsets(tokenizer, seq)
    L = len(ids)
    groups = {}
    for vi, subs in enumerate(df["subs"]):
        mask = tuple(sorted({p + off for p, _, _ in subs}))
        groups.setdefault(mask, []).append(vi)
    masks = sorted(groups.keys())
    scores = np.full(len(df), np.nan, dtype=np.float64)
    bs = best_batch(L, device, use_fp16)
    if L <= 400:
        bs = max(bs, 256)
    bs = min(bs, len(masks))
    n_batches, t0 = 0, time.time()
    for b0 in range(0, len(masks), bs):
        chunk = masks[b0 : b0 + bs]
        pos_sets = [np.array(m, dtype=np.int64) for m in chunk]
        flat = ids.unsqueeze(0).expand(len(chunk), -1).clone().to(device)
        for bi, ps in enumerate(pos_sets):
            flat[bi, ps] = tokenizer.mask_token_id
        attn = torch.ones(len(chunk), L, dtype=torch.long, device=device)
        logits = model(flat, attention_mask=attn)["logits"]
        if logits.dtype != torch.float32:
            logits = logits.float()
        lp = torch.log_softmax(logits, dim=-1)
        lp20 = lp[:, :, aa_cols]
        lp20 = lp20 - torch.logsumexp(lp20, dim=-1, keepdim=True)
        for bi, m in enumerate(chunk):
            ps = pos_sets[bi].tolist()
            logp = lp20[bi, ps].cpu().numpy()
            idx_of = {int(p): k for k, p in enumerate(ps)}
            for vi in groups[m]:
                s = 0.0
                for p0, wt_aa, mut_aa in df["subs"].iloc[vi]:
                    pvals = logp[idx_of[int(p0 + off)]]
                    s += pvals[AA_TO_IDX[mut_aa]] - pvals[AA_TO_IDX[wt_aa]]
                scores[vi] = s
        n_batches += 1
        if n_batches % 10 == 0:
            print(f"    ... {n_batches} batches, {time.time()-t0:.0f}s", flush=True)
    return scores, len(masks), n_batches


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="tables", choices=["tables", "joint"])
    ap.add_argument("--models", default="esm2_t33_650M,esm2_t6_8M")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--assays", default="")
    args = ap.parse_args()

    ref = load_reference()
    assay_list = args.assays.split(",") if args.assays else ASSAYS
    device = (torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")) if args.device == "auto" else torch.device(args.device)

    for key in args.models.split(","):
        key = key.strip()
        if not key:
            continue
        from transformers import AutoTokenizer, EsmForMaskedLM

        t0 = time.time()
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAMES[key])
        model = EsmForMaskedLM.from_pretrained(MODEL_NAMES[key]).to(device).eval()
        use_fp16 = device.type == "cuda"
        if use_fp16:
            model = model.half()
        n_params = sum(p.numel() for p in model.parameters()) / 1e6
        aa_cols = torch.tensor(aa_vocab_ids(tokenizer), dtype=torch.long, device=device)
        print(f"[{key}] {MODEL_NAMES[key]} {n_params:.0f}M on {device} fp16={use_fp16} load {time.time()-t0:.1f}s", flush=True)

        out_dir = os.path.join(ROOT, "results", "lm_scores", args.mode, key)
        os.makedirs(out_dir, exist_ok=True)

        for fid in assay_list:
            t0 = time.time()
            seq = get_target_seq(ref, fid)
            df = load_assay(fid)
            if args.mode == "tables":
                table, off = score_tables(model, tokenizer, seq, device, aa_cols, use_fp16)
                scores = np.empty(len(df), dtype=np.float64)
                for vi, subs in enumerate(df["subs"]):
                    s = 0.0
                    for p0, wt_aa, mut_aa in subs:
                        s += table[p0 + off, AA_TO_IDX[mut_aa]] - table[p0 + off, AA_TO_IDX[wt_aa]]
                    scores[vi] = s
                note = f"tables {time.time()-t0:.1f}s"
            else:
                scores, nm, nb = score_joint(model, tokenizer, seq, device, aa_cols, use_fp16, df)
                note = f"joint {nm} masks {nb} batches {time.time()-t0:.1f}s"

            df["score"] = scores
            out_csv = os.path.join(out_dir, f"{fid}.csv")
            df[["mutant", "DMS_score", "DMS_score_bin", "score"]].to_csv(out_csv, index=False)
            print(f"[{key}] {fid}: {len(df)} variants, {note} -> {out_csv}", flush=True)

        meta = {"model": MODEL_NAMES[key], "device": str(device), "fp16": use_fp16,
                "mode": args.mode}
        with open(os.path.join(out_dir, "meta.json"), "w") as f:
            json.dump(meta, f, indent=2)


if __name__ == "__main__":
    main()