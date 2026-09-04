#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compute_extra.py - supplementary diagnostics for ICSD_CN model x ICSD_CN test:
per-class accuracy, compound-level average site accuracy (PCASA), and the
per-position accuracy profile (helps motivate the site-cap/truncation choice)."""
import json
import os
import sys

import torch
from transformers import BertTokenizerFast

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evaluate as ev

DATA = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data"))
OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results"))

M, DS = "ICSD_CN", "ICSD_CN"


def main():
    tok = BertTokenizerFast.from_pretrained(os.path.join(DATA, "code", "tokenizer"), do_lower_case=False)
    blocks = ev.read_blocks(DS, "test", DATA)
    td = ev.tokenize_blocks(blocks, tok, 200)
    model = ev.load_model(M, DATA, torch.device("cpu"))
    res = ev.predict_model(model, td)

    agg = ev.aggregate(res, blocks, ev.metal_nonmetal_split(blocks), 199)

    # per-class
    per_class = {}
    for block_idx, (labs, preds) in enumerate(res):
        blk = blocks[block_idx]
        for k in range(min(len(blk), 199)):
            lab = int(blk[k][1]) + 5
            correct = k < len(preds) and preds[k] == lab
            c = per_class.setdefault(lab, [0, 0])
            c[1] += 1
            c[0] += int(correct)

    # PCASA: mean over compounds of site accuracy within compound
    pcasa_sum = 0.0
    for block_idx, (labs, preds) in enumerate(res):
        blk = blocks[block_idx]
        n = min(len(blk), 199)
        n_c = sum(1 for k in range(n) if k < len(preds) and preds[k] == (int(blk[k][1]) + 5))
        pcasa_sum += n_c / n
    pcasa = pcasa_sum / len(blocks)

    # per-position profile (positions 0..198), aggregated over all blocks
    pos_corr = {}
    pos_total = {}
    for block_idx, (labs, preds) in enumerate(res):
        blk = blocks[block_idx]
        for k in range(min(len(blk), 199)):
            pos_total[k] = pos_total.get(k, 0) + 1
            if k < len(preds) and preds[k] == (int(blk[k][1]) + 5):
                pos_corr[k] = pos_corr.get(k, 0) + 1

    out = {
        "model": M, "dataset": DS, "PS": agg["PS"], "PC": agg["PC"],
        "PCASA": pcasa,
        "metal_PS": agg["metal_PS"], "nonmetal_PS": agg["nonmetal_PS"],
        "per_class": {f"idx{os}": {"class": f"{os - 5}", "correct": v[0], "total": v[1],
                                    "acc": v[0] / v[1]}
                      for os, v in sorted(per_class.items())},
        "position_acc": {str(k): round(pos_corr.get(k, 0) / v * 100, 2) for k, v in sorted(pos_total.items())
                         if v >= 20},
    }
    with open(os.path.join(OUT, "extra_icsd_cn.json"), "w") as f:
        json.dump(out, f, indent=2, default=float)
    print(f"PS={agg['PS']*100:.4f}  PC={agg['PC']*100:.4f}  PCASA={pcasa*100:.4f}")
    print(f"metal={agg['metal_PS']*100:.4f}  nonmetal={agg['nonmetal_PS']*100:.4f}")


if __name__ == "__main__":
    main()