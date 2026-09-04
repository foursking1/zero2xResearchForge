"""Explore and validate the frozen ProteinGym data.

Checks:
  1. Each assay CSV row count and format (mutant,DMS_score,DMS_score_bin).
  2. DMS_score direction (higher = higher fitness, per ProteinGym processing).
  3. mutant strings (e.g. 'M1I') map onto the target_seq from the
     ProteinGym reference file (WT residue at 1-indexed position matches).
  4. Multi-mutant handling (GFP, ':' separated).
"""
import json
import os
import re

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # agent_solution/
DATA = os.path.join(os.path.dirname(ROOT), "data")

ASSAYS = [
    "ADRB2_HUMAN_Jones_2020",
    "BLAT_ECOLX_Deng_2012",
    "BRCA1_HUMAN_Findlay_2018",
    "GAL4_YEAST_Kitzman_2015",
    "GFP_AEQVI_Sarkisyan_2016",
    "PTEN_HUMAN_Matreyek_2021",
]

AA20 = "ACDEFGHIKLMNPQRSTVWY"


def _np_default(o):
    import numpy as np
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    return str(o)


def parse_mutant(m):
    """'K3R:V55A' -> [(0, 'K', 'R'), (55, 'V', 'A')] (0-indexed positions)."""
    out = []
    for part in m.split(":"):
        g = re.fullmatch(r"([A-Z])(\d+)([A-Z])", part)
        if not g:
            raise ValueError(f"unparsable mutant {part!r} in {m!r}")
        wt, pos, mut = g.groups()
        out.append((int(pos) - 1, wt, mut))
    return out


def main():
    ref = pd.read_csv(os.path.join(DATA, "ProteinGym_reference_file_substitutions.csv"))
    summary = {}
    for fid in ASSAYS:
        df = pd.read_csv(os.path.join(DATA, f"{fid}.csv"))
        assert list(df.columns) == ["mutant", "DMS_score", "DMS_score_bin"], df.columns
        r = ref[ref["DMS_id"] == fid].iloc[0]
        seq = r["target_seq"]
        raw_lines = sum(1 for _ in open(os.path.join(DATA, f"{fid}.csv"), "r"))
        info = {
            "DMS_id": fid,
            "uni_prot_id": r["UniProt_ID"],
            "taxon": r["taxon"],
            "n_raw_lines_incl_header": raw_lines,
            "n_variants": len(df),
            "n_single": 0,
            "n_multi": 0,
            "seq_len": len(seq),
            "MSA_Neff": r["MSA_N_eff"],
            "MSA_Neff_L_category": r["MSA_Neff_L_category"],
            "raw_DMS_directionality": r["raw_DMS_directionality"],
            "DMS_score_min": float(df["DMS_score"].min()),
            "DMS_score_max": float(df["DMS_score"].max()),
            "DMS_score_bin_unique": sorted(df["DMS_score_bin"].unique().tolist()),
            "position_map_failures": 0,
            "position_map_examples": [],
        }
        # Validate every mutant maps onto the target sequence
        ok_pos, bad_pos, multi = 0, 0, 0
        for m in df["mutant"]:
            subs = parse_mutant(m)
            if len(subs) > 1:
                multi += 1
            for pos, wt, _ in subs:
                if pos >= len(seq):
                    bad_pos += 1
                    continue
                if seq[pos] == wt:
                    ok_pos += 1
                else:
                    bad_pos += 1
                    if len(info["position_map_examples"]) < 3:
                        info["position_map_examples"].append(
                            f"{m}: pos{pos+1} target={seq[pos]} wt={wt}"
                        )
        info["n_single"] = len(df) - multi
        info["n_multi"] = multi
        info["position_map_ok"] = ok_pos
        info["position_map_bad"] = bad_pos
        summary[fid] = info
        n_target_aa = info["position_map_ok"]
        match_rate = ok_pos / max(1, ok_pos + bad_pos)
        print(f"\n=== {fid} ===")
        print(
            f"  variants={len(df):>6}  single={info['n_single']:>6}  multi={multi:>6}"
        )
        print(
            f"  position map ok={ok_pos} bad={bad_pos} match_rate={match_rate:.4f}"
        )
        print(f"  DMS_score range [{info['DMS_score_min']:.3f}, {info['DMS_score_max']:.3f}]")
        if info["position_map_examples"]:
            print("  example mismatches:", info["position_map_examples"])

    # Check DMS_score_bin consistency of direction
    for fid in ASSAYS:
        df = pd.read_csv(os.path.join(DATA, f"{fid}.csv"))
        mu_bin1 = df.loc[df["DMS_score_bin"] == 1, "DMS_score"].mean()
        mu_bin0 = df.loc[df["DMS_score_bin"] == 0, "DMS_score"].mean()
        print(
            f"{fid}: mean DMS_score bin1={mu_bin1:.3f} bin0={mu_bin0:.3f} "
            f"bin1>bin0={mu_bin1 > mu_bin0}"
        )

    out = os.path.join(ROOT, "results", "exploration_summary.json")
    with open(out, "w") as f:
        json.dump(summary, f, indent=2, default=_np_default)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()