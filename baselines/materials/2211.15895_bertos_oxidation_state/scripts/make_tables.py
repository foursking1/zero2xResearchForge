#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_tables.py - Render the evidence tables (PS/PC matrix aligned to the
paper's Table 1, anchor comparisons, dataset-size checks) from
evaluation_results.json (produced by evaluate.py)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.normpath(os.path.join(HERE, "..", "results"))
OUT = os.path.normpath(os.path.join(HERE, "..", "evidence"))

PAPER_T1 = {  # row=train model, col=test set (paper Table 1, PS %)
    "ICSD": {"ICSD": 96.82, "ICSD_CN": 96.28, "ICSD_oxide": 97.51, "ICSD_CN_oxide": 97.11},
    "ICSD_CN": {"ICSD": 95.92, "ICSD_CN": 96.27, "ICSD_oxide": 96.60, "ICSD_CN_oxide": 96.95},
    "ICSD_oxide": {"ICSD": 95.78, "ICSD_CN": 94.96, "ICSD_oxide": 97.61, "ICSD_CN_oxide": 97.14},
    "ICSD_CN_oxide": {"ICSD": 94.95, "ICSD_CN": 94.85, "ICSD_oxide": 96.70, "ICSD_CN_oxide": 96.97},
}

ANCHOR = {
    "ICSD__ICSD": 96.25, "ICSD_CN__ICSD_CN": 95.75, "ICSD_oxide__ICSD_oxide": 97.04,
}


def fmt_md_table(values, annot):
    models = list(values)
    dss = list(values[models[0]])
    lines = ["| Train \\ Test | " + " | ".join(dss) + " |",
             "|" + "---|" * (len(dss) + 1)]
    for m in models:
        cells = []
        for ds in dss:
            s = f"{values[m][ds]:.2f}"
            if annot and annot.get(m, {}).get(ds):
                s += f" ({annot[m][ds]:+.2f})"
            cells.append(s)
        lines.append(f"| {m} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main():
    os.makedirs(OUT, exist_ok=True)
    data = json.load(open(os.path.join(RES, "evaluation_results.json")))
    PS = {m: {ds: v for ds, v in row.items()} for m, row in data["matrix_PS"].items()}
    PC = data["matrix_PC"]
    metal = data["matrix_metal_PS"]
    nonmetal = data["matrix_nonmetal_PS"]
    sites = data["matrix_sites"]

    annot = {m: {ds: round(PS[m][ds] - PAPER_T1[m][ds], 2) for ds in PS[m]} for m in PS}
    with open(os.path.join(OUT, "table1_ps_matrix.md"), "w") as f:
        f.write("### Ours (frozen official checkpoints) PS % [diff vs paper Table 1 in parens]\n\n")
        f.write(fmt_md_table(PS, annot) + "\n\n")
        f.write("### Paper Table 1 PS %\n\n")
        f.write(fmt_md_table(PAPER_T1, None) + "\n")
    with open(os.path.join(OUT, "table1_pc_matrix.md"), "w") as f:
        f.write("### PC % (ours)      [paper PC values: Table 1 not published per-cell; "
                "diagonal comparisons below]\n\n")
        f.write(fmt_md_table(PC, None) + "\n")
    with open(os.path.join(OUT, "table1_metal_nonmetal.md"), "w") as f:
        f.write("### Metal / non-metal site-level PS % (ours)\n\n")
        f.write("### Metal\n\n" + fmt_md_table(metal, None) + "\n\n")
        f.write("### Non-metal\n\n" + fmt_md_table(nonmetal, None) + "\n\n")
        f.write("### Sites per (train x test)\n\n" + fmt_md_table(sites, None) + "\n")

    # anchor comparison summary
    rows = []
    for k, ref in ANCHOR.items():
        m, ds = k.split("__")
        ours = data["matrix_PS"][m][ds]
        rows.append([f"{m} x {ds}", f"{ours:.4f}", f"{ref:.2f}", f"{ours-ref:+.4f}"])
    with open(os.path.join(OUT, "anchor_comparison.md"), "w") as f:
        f.write("| Model x Test | ours PS% | anchor frozen-data PS% | diff (pp) |\n|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(r) + " |\n")
        f.write("\nNote: anchor values are the benchmark's reference recomputation; "
                "the paper Table 1 values are 96.82 / 96.27 / 97.61.\n")

    # dataset size checks (B3)
    with open(os.path.join(OUT, "dataset_sizes.md"), "w") as f:
        f.write("| dataset | train blocks | validation blocks | test blocks | test sites (raw) |\n")
        f.write("|---|---|---|---|---|\n")
        import zipfile
        for ds in ["ICSD", "ICSD_CN", "ICSD_oxide", "ICSD_CN_oxide"]:
            counts = {}
            raw_sites = {}
            with zipfile.ZipFile(os.path.join(os.path.normpath(os.path.join(HERE, "..", "..", "data")),
                                             "datasets", f"{ds}.zip")) as z:
                for split in ["train", "validation", "test"]:
                    text = z.read(f"{ds}/{split}.txt").decode()
                    blocks = [b for b in text.split("\n\n") if b.strip()]
                    counts[split] = len(blocks)
                    raw_sites[split] = sum(len(b.split("\n")) for b in blocks)
            f.write(f"| {ds} | {counts['train']} | {counts['validation']} | "
                    f"{counts['test']} | {raw_sites['test']} |\n")
    print("[ok] evidence tables written to", OUT)


if __name__ == "__main__":
    main()