#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
per_element.py - Per-element (and per-class) oxidation-state accuracy tables for
chosen (model, dataset) combinations, using the same frozen checkpoints and
evaluation protocol as evaluate.py.

Usage:
  python3 per_element.py --data <data_root> --combos ICSD__ICSD,ICSD__ICSD_CN \
      --max_length 200 --site_cap 199 --outdir agent_solution/results
"""
import argparse
import csv
import json
import os

import torch
from transformers import BertTokenizerFast

import evaluate as ev


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None)
    ap.add_argument("--combos", default="ICSD__ICSD_CN,ICSD_CN__ICSD_CN",
                    help="Comma separated model__dataset pairs.")
    ap.add_argument("--max_length", type=int, default=200)
    ap.add_argument("--site_cap", type=int, default=199)
    ap.add_argument("--outdir", default=None)
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    data_root = args.data or os.path.normpath(os.path.join(here, "..", "..", "data"))
    outdir = args.outdir or os.path.normpath(os.path.join(here, "..", "results"))
    os.makedirs(outdir, exist_ok=True)

    tokenizer = BertTokenizerFast.from_pretrained(
        os.path.join(data_root, "code", "tokenizer"), do_lower_case=False)

    combos = [tuple(c.split("__")) for c in args.combos.split(",")]
    summary = {}
    for m, ds in combos:
        blocks = ev.read_blocks(ds, "test", data_root)
        tokenized = ev.tokenize_blocks(blocks, tokenizer, args.max_length)
        model = ev.load_model(m, data_root, torch.device("cpu"))
        results = ev.predict_model(model, tokenized)
        flags = ev.metal_nonmetal_split(blocks)
        agg = ev.aggregate(results, blocks, flags, args.site_cap)

        # per-element accuracy over capped scored sites
        el_corr, el_total = {}, {}
        for block_idx, (labs, preds) in enumerate(results):
            block = blocks[block_idx]
            n_scored = args.site_cap if len(block) >= args.site_cap else len(block)
            for k in range(n_scored):
                elem = block[k][0]
                pred = preds[k] if k < len(preds) else None
                el_total[elem] = el_total.get(elem, 0) + 1
                # class index = oxidation state + 5
                if pred is not None and pred == int(block[k][1]) + 5:
                    el_corr[elem] = el_corr.get(elem, 0) + 1

        csv_path = os.path.join(outdir, f"per_element_{m}x{ds}.csv")
        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["element", "n_sites", "n_correct", "accuracy", "metal"])
            for e in sorted(el_total):
                w.writerow([e, el_total[e], el_corr.get(e, 0),
                            round(el_corr.get(e, 0) / el_total[e] * 100, 3),
                            int(e in ev.METAL_ELEMENTS)])
        summary[f"{m}x{ds}"] = {
            "PS": agg["PS"], "PC": agg["PC"],
            "metal_PS": agg["metal_PS"], "nonmetal_PS": agg["nonmetal_PS"],
        }
        print(f"[ok] {m}x{ds} PS={agg['PS']*100:.4f}% PC={agg['PC']*100:.4f}% -> {csv_path}")

    with open(os.path.join(outdir, "per_element_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()