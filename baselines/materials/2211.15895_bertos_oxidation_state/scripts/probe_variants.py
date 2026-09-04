#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe_variants.py - diagnostics: measure PS under several inference-protocol
variants to pin down the reference protocol used for the anchor values
(96.25 / 95.75 / 97.04). No scoring impact; purely diagnostic."""
import os
import sys
import torch
from transformers import BertTokenizerFast

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evaluate as ev

DATA = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data"))

SUB = {"ICSD__ICSD": 5215, "ICSD_CN__ICSD_CN": 3724, "ICSD_oxide__ICSD_oxide": 3603}


def classify(results, blocks, cap, metal_flags):
    """PS/PC given per-block (labs, preds) and gold cap rule."""
    n_s = n_c = n_comp = n_comp_ok = 0
    off = 0
    for (labs, preds), block in zip(results, blocks):
        n_pos = min(len(block), cap)
        n_comp += 1
        ok = True
        for k in range(n_pos):
            correct = k < len(preds) and preds[k] == (int(block[k][1]) + 5)
            n_s += 1
            n_c += int(correct)
            ok = ok and correct
        off += len(block)
        n_comp_ok += int(ok)
    return n_c / n_s, n_comp_ok / n_comp


def main():
    tok = BertTokenizerFast.from_pretrained(os.path.join(DATA, "code", "tokenizer"), do_lower_case=False)

    variants = ["official_198/199", "no_specials_199", "ml100_cap98", "no_attnmask"]
    print(f"{'combo':26s} " + "  ".join(f"{v:>20s}" for v in variants))
    for combo, nblk in SUB.items():
        m, ds = combo.split("__")
        blocks = ev.read_blocks(ds, "test", DATA)[:nblk]
        model = ev.load_model(m, DATA, torch.device("cpu"))
        flags = ev.metal_nonmetal_split(blocks)
        row = {}

        # A. official: max_length=200 with specials, cap 199
        td = ev.tokenize_blocks(blocks, tok, 200)
        res = ev.predict_model(model, td)
        row["official_198/199"] = classify(res, blocks, 199, flags)[0]

        # B. no special tokens, 200 element slots, compare preds[0:cap]
        enc = tok(  # pad to 200 without specials
            [[b[0] for b in blk] for blk in blocks],
            max_length=200, truncation=True, padding="max_length",
            is_split_into_words=True, return_tensors="pt",
        ).to("cpu")
        attn = enc["attention_mask"]
        with torch.no_grad():
            logits = model(enc["input_ids"], attention_mask=attn).logits
        preds_all = logits.argmax(-1)
        resB = []
        for j, blk in enumerate(blocks):
            plen = enc["attention_mask"][j].sum().item()
            resB.append(([], preds_all[j, :plen].tolist()))
        row["no_specials_199"] = classify(resB, blocks, 199, flags)[0]

        # C. max_length=100 => 98 element slots, cap 98
        tdC = ev.tokenize_blocks(blocks, tok, 100)
        resC = ev.predict_model(model, tdC)
        row["ml100_cap98"] = classify(resC, blocks, 98, flags)[0]

        # D. official tokenization but attention_mask all-ones (padding not masked)
        tdD = {"input_ids": td["input_ids"],
               "attention_mask": torch.ones_like(td["attention_mask"]),
               "labels": td["labels"]}
        resD = ev.predict_model(model, tdD)
        row["no_attnmask"] = classify(resD, blocks, 199, flags)[0]

        print(f"{combo:26s} " + "  ".join(f"{row[v]*100:20.4f}" for v in variants))


if __name__ == "__main__":
    main()