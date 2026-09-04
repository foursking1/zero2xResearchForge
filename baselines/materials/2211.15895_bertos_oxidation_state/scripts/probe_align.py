#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe_align.py - search over label-alignment / sequence-order variants that
could explain the reference PS values (96.25 / 95.75 / 97.04 vs our official
96.78 / 96.34 / 97.50) while keeping the same site counts (min(L,199))."""
import os
import sys
import torch
from transformers import BertTokenizerFast

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evaluate as ev

DATA = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data"))
COMBOS = ["ICSD__ICSD", "ICSD_CN__ICSD_CN", "ICSD_oxide__ICSD_oxide"]


def analyze(preds_by_block, gold_idx_by_block, blocks, variant):
    n_s = n_c = 0
    for blk, preds, gold in zip(blocks, preds_by_block, gold_idx_by_block):
        n_pos = len(gold)  # == min(L,199)
        for k in range(n_pos):
            if variant == "official":
                correct = k < len(preds) and preds[k] == gold[k]
            elif variant == "shift_left":
                correct = k < len(preds) and preds[k] == (gold[k + 1] if k + 1 < len(gold) else -999)
            elif variant == "shift_right":
                correct = k > 0 and k <= len(preds) and preds[k - 1] == gold[k]
            elif variant == "gold_cut_miss":
                # official but the FIRST predicted position is discarded (miss)
                correct = False
                if k + 1 < len(preds) and k + 1 < len(gold):
                    correct = preds[k + 1] == gold[k]
            n_s += 1
            n_c += int(correct)
    return n_c / n_s * 100


def main():
    tok = BertTokenizerFast.from_pretrained(os.path.join(DATA, "code", "tokenizer"), do_lower_case=False)
    variants = ["official", "shift_left", "shift_right", "gold_cut_miss"]
    print(f"{'combo':22s} " + "  ".join(f"{v:>14s}" for v in variants))
    for combo in COMBOS:
        m, ds = combo.split("__")
        blocks = ev.read_blocks(ds, "test", DATA)
        model = ev.load_model(m, DATA, torch.device("cpu"))
        td = ev.tokenize_blocks(blocks, tok, 200)
        # element-wise predictions for the model-seen span (positions 1..min(L,198))
        with torch.no_grad():
            logits = model(td["input_ids"], attention_mask=td["attention_mask"]).logits
        pred_all = logits.argmax(-1)
        preds_by_block = []
        gold_idx_by_block = []
        for j, blk in enumerate(blocks):
            labs_nonpad = td["labels"][j][td["labels"][j] != -100]
            preds = pred_all[j][td["labels"][j] != -100]
            preds_by_block.append(preds.tolist())
            gold = [int(blk[k][1]) + 5 for k in range(min(len(blk), 199))]
            gold_idx_by_block.append(gold)
        row = [analyze(preds_by_block, gold_idx_by_block, blocks, v) for v in variants]
        print(f"{combo:22s} " + "  ".join(f"{x:14.4f}" for x in row))


if __name__ == "__main__":
    main()