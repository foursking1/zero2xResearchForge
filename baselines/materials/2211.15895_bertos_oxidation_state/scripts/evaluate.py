#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evaluate.py - Frozen-model evaluation of BERTOS oxidation-state prediction.

Reproduces the claims of Fu et al. (arXiv:2211.15895 / Adv. Sci. 2023) by
running the OFFICIAL pre-trained checkpoints (data/models/*.zip) on the
OFFICIAL frozen test splits (data/datasets/*.zip). No retraining, no network,
CPU inference only.

Conventions (matching the released official tooling, train_BERTOS.py / getOS.py):

  1. Data files are CoNLL blocks: one "ELEMENT oxidation_state" line per atomic
     site, blank line separates compounds. Block = list of (element, charge).
  2. Each element symbol is a single word; the BERT tokenizer with
     is_split_into_words=True yields exactly one token per element (Nb/Re are
     in the vocab file as "Nb "/"Re " with trailing spaces, so the shipped
     tokenizer maps those two symbols to [UNK]; still exactly one output token
     per element, so label alignment is 1:1).
  3. Sequences are truncated to ``max_length`` tokens (default 200, equal to
     the model's max_position_embeddings) => model predicts at most
     max_length-2 = 198 elements per compound. Labels are aligned via word_ids
     to the first token of each word (special tokens get -100).
  4. Scoring (PS / PC) counts gold sites per compound capped at ``site_cap``
     atoms (default 199, reproducing the anchor's frozen-data site counts,
     e.g. 295,515 for OS-ICSD test). A gold site beyond the model's predicted
     positions (i.e. the 199th atom when only 198 were predicted) counts as a
     miss.
  5. Prediction = argmax of the 14-way logits; class index - 5 = oxidation
     state (config id2label maps 0..13 -> '-5'..'8').
  6. PS  = correctly predicted atomic sites / scored atomic sites.
     PC  = compounds with all scored sites correct / all compounds.
     Metal / non-metal PS group sites by the standard metal element table.

Usage:
  python3 evaluate.py --data <data_root> [--max_length 200] [--site_cap 199]
                      [--jobs 4] [--outdir agent_solution/results]
                      [--models ICSD,ICSD_CN,ICSD_oxide,ICSD_CN_oxide]
"""
import argparse
import json
import os
import tempfile
import zipfile

import torch
from transformers import AutoConfig, BertForTokenClassification, BertTokenizerFast

MODELS = ["ICSD", "ICSD_CN", "ICSD_oxide", "ICSD_CN_oxide"]
DATASETS = ["ICSD", "ICSD_CN", "ICSD_oxide", "ICSD_CN_oxide"]

METAL_ELEMENTS = set("""
Li Be Na Mg Al K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Rb Sr Y Zr Nb Mo Tc Ru Rh
Pd Ag Cd In Sn Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os
Ir Pt Au Hg Tl Pb Bi Po Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db
Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv
""".replace("\n", " ").split())


def read_blocks(ds_name, split, data_root):
    """Read CoNLL blocks from frozen zip; each block is a list of (elem, charge)."""
    path = os.path.join(data_root, "datasets", f"{ds_name}.zip")
    with zipfile.ZipFile(path) as z:
        text = z.read(f"{ds_name}/{split}.txt").decode("utf-8")
    blocks = []
    for chunk in text.split("\n\n"):
        lines = [ln for ln in chunk.splitlines() if ln.strip()]
        if lines:
            blocks.append([tuple(ln.split()) for ln in lines])
    return blocks


def tokenize_blocks(blocks, tokenizer, max_length):
    """Uniform pad every block to `max_length` tokens; labels aligned to words."""
    word_sequences = [[b[0] for b in block] for block in blocks]
    label_sequences = [[int(b[1]) for b in block] for block in blocks]
    enc = tokenizer(
        word_sequences,
        max_length=max_length,
        truncation=True,
        padding="max_length",
        is_split_into_words=True,
        return_tensors="pt",
    )
    all_label_ids = torch.full_like(enc["input_ids"], -100)
    for i, (words, labels) in enumerate(zip(word_sequences, label_sequences)):
        word_ids = enc.word_ids(batch_index=i)
        previous = None
        for j, wid in enumerate(word_ids):
            if wid is None:
                continue
            if wid != previous:
                all_label_ids[i, j] = labels[wid]
                previous = wid
    return {
        "input_ids": enc["input_ids"],
        "attention_mask": enc["attention_mask"],
        "labels": all_label_ids,
    }


@torch.no_grad()
def predict_model(model, tokenized, batch_size=64):
    """Return per-block (labels, preds) lists over the elements the model saw."""
    ids = tokenized["input_ids"]
    mask = tokenized["attention_mask"]
    labels = tokenized["labels"]
    n = labels.shape[0]
    preds_all = torch.empty_like(labels)
    for i in range(0, n, batch_size):
        logits = model(input_ids=ids[i:i + batch_size],
                       attention_mask=mask[i:i + batch_size]).logits
        preds_all[i:i + batch_size] = logits.argmax(dim=-1)
    return [(labels[j][labels[j] != -100].tolist(),
             preds_all[j][labels[j] != -100].tolist())
            for j in range(n)]


def metal_nonmetal_split(blocks):
    """Per-site metal(1)/non-metal(0) flags over ALL raw sites, in order."""
    flags = []
    for block in blocks:
        flags.extend([1 if b[0] in METAL_ELEMENTS else 0 for b in block])
    return flags


def aggregate(results, blocks, elem_metal_flags, site_cap):
    """PS / PC / metal-non-metal / per-class accuracies under the site_cap rule.
    A gold site with no model prediction (only possible for the site_cap-th atom
    of compounds with > max_length-2 atoms) is counted as incorrect."""
    n_sites = n_correct = n_compounds = n_compounds_correct = 0
    per_class_corr, per_class_total = {}, {}
    metal_corr = metal_total = nonmetal_corr = nonmetal_total = 0
    raw_offset = 0
    for block_idx, (labs, preds) in enumerate(results):
        block = blocks[block_idx]
        n_scored = site_cap if len(block) >= site_cap else len(block)
        n_compounds += 1
        block_ok = True
        for k in range(n_scored):
            # class index = oxidation state + 5 (config id2label: 0..13 -> '-5'..'8')
            lab_idx = int(block[k][1]) + 5
            elem = block[k][0]
            pred = preds[k] if k < len(preds) else None
            correct = (pred is not None) and (pred == lab_idx)
            n_sites += 1
            if correct:
                n_correct += 1
            else:
                block_ok = False
            per_class_total[lab_idx] = per_class_total.get(lab_idx, 0) + 1
            if correct:
                per_class_corr[lab_idx] = per_class_corr.get(lab_idx, 0) + 1
            if elem_metal_flags[raw_offset + k]:
                metal_total += 1
                metal_corr += int(correct)
            else:
                nonmetal_total += 1
                nonmetal_corr += int(correct)
        raw_offset += len(block)
        n_compounds_correct += int(block_ok)
    return {
        "n_sites": n_sites,
        "n_correct": n_correct,
        "n_compounds": n_compounds,
        "n_compounds_correct": n_compounds_correct,
        "PS": n_correct / n_sites if n_sites else 0.0,
        "PC": n_compounds_correct / n_compounds if n_compounds else 0.0,
        "metal_PS": metal_corr / metal_total if metal_total else 0.0,
        "metal_sites": metal_total,
        "nonmetal_PS": nonmetal_corr / nonmetal_total if nonmetal_total else 0.0,
        "nonmetal_sites": nonmetal_total,
        "per_class": {str(lab + 5): {"correct": per_class_corr.get(lab, 0),
                                     "total": per_class_total.get(lab, 0)}
                      for lab in sorted(per_class_total)},
    }


def load_model(model_name, data_root, device):
    zip_path = os.path.join(data_root, "models", f"{model_name}.zip")
    tmpdir = tempfile.mkdtemp(prefix="bertos_model_")
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(tmpdir)
    model_dir = os.path.join(tmpdir, model_name)
    config = AutoConfig.from_pretrained(model_dir, num_labels=14)
    model = BertForTokenClassification.from_pretrained(model_dir, config=config)
    model.to(device).eval()
    return model


def _worker(args_tuple):
    m, ds, data_root, max_length, site_cap = args_tuple
    torch.set_num_threads(1)
    blocks = read_blocks(ds, "test", data_root)
    tokenizer = BertTokenizerFast.from_pretrained(
        os.path.join(data_root, "code", "tokenizer"), do_lower_case=False)
    tokenized = tokenize_blocks(blocks, tokenizer, max_length)
    model = load_model(m, data_root, torch.device("cpu"))
    res = predict_model(model, tokenized)
    agg = aggregate(res, blocks, metal_nonmetal_split(blocks), site_cap)
    return m, ds, agg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None,
                    help="Frozen data dir (with datasets/ and models/). "
                         "Default: <script>/../../data")
    ap.add_argument("--max_length", type=int, default=200,
                    help="Tokenizer truncation length (200 = model max position; "
                         "model predicts at most 198 elements per compound).")
    ap.add_argument("--site_cap", type=int, default=199,
                    help="Max gold sites per compound counted for PS/PC.")
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--models", type=str, default=",".join(MODELS))
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    data_root = args.data or os.path.normpath(os.path.join(here, "..", "..", "data"))
    outdir = args.outdir or os.path.normpath(os.path.join(here, "..", "results"))
    os.makedirs(outdir, exist_ok=True)

    print(f"[setup] data_root={data_root}  max_length={args.max_length}  "
          f"site_cap={args.site_cap}  jobs={args.jobs}")

    models_to_eval = [m for m in MODELS if m in args.models.split(",")]

    # tokenize once in the parent (children inherit via fork COW)
    tokenizer = BertTokenizerFast.from_pretrained(
        os.path.join(data_root, "code", "tokenizer"), do_lower_case=False)
    test_sets = {}
    for ds in DATASETS:
        blocks = read_blocks(ds, "test", data_root)
        test_sets[ds] = {
            "blocks": blocks,
            "tokenized": tokenize_blocks(blocks, tokenizer, args.max_length),
        }
        print(f"[data] {ds:15s} test blocks={len(blocks):6d} "
              f"total_sites={sum(len(b) for b in blocks):7d}")

    import multiprocessing as mp
    jobs_list = [(m, ds, data_root, args.max_length, args.site_cap)
                 for m in models_to_eval for ds in DATASETS]
    pool = mp.get_context("fork").Pool(processes=min(args.jobs, len(jobs_list)))
    matrix = {m: {} for m in models_to_eval}
    for m, ds, agg in pool.imap_unordered(
            _worker, jobs_list, chunksize=1):
        matrix[m][ds] = agg
        print(f"[eval] {m:15s} x {ds:15s} PS={agg['PS']*100:.4f}%  "
              f"PC={agg['PC']*100:.4f}%  sites={agg['n_sites']}  "
              f"compounds={agg['n_compounds']}")
    pool.close()
    pool.join()

    block_counts = {ds: len(test_sets[ds]["blocks"]) for ds in DATASETS}

    def _compact(agg):
        return {kk: (round(vv * 100, 4) if kk in ("PS", "PC", "metal_PS", "nonmetal_PS") else vv)
                for kk, vv in agg.items() if kk != "per_class"}

    payload = {
        "max_length": args.max_length,
        "site_cap": args.site_cap,
        "block_counts": block_counts,
        "matrix_PS": {m: {ds: round(matrix[m][ds]["PS"] * 100, 4) for ds in DATASETS}
                      for m in models_to_eval},
        "matrix_PC": {m: {ds: round(matrix[m][ds]["PC"] * 100, 4) for ds in DATASETS}
                      for m in models_to_eval},
        "matrix_metal_PS": {m: {ds: round(matrix[m][ds]["metal_PS"] * 100, 4) for ds in DATASETS}
                            for m in models_to_eval},
        "matrix_nonmetal_PS": {m: {ds: round(matrix[m][ds]["nonmetal_PS"] * 100, 4) for ds in DATASETS}
                               for m in models_to_eval},
        "matrix_sites": {m: {ds: matrix[m][ds]["n_sites"] for ds in DATASETS}
                         for m in models_to_eval},
        "summaries": {f"{m}__{ds}": _compact(matrix[m][ds])
                      for m in models_to_eval for ds in DATASETS},
    }

    out_path = os.path.join(outdir, "evaluation_results.json")
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"[ok] results -> {out_path}")


if __name__ == "__main__":
    main()