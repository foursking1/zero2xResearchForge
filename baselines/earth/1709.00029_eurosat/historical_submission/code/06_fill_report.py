#!/usr/bin/env python3
"""Fill {{PLACEHOLDERS}} in report.md / solution.md from results/metrics.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANCHOR = 98.57


def main():
    with open(ROOT / "results" / "metrics.json") as f:
        m = json.load(f)
    oa = m["overall_accuracy"] * 100
    vals = {
        "TEST_OA_4DP": f"{m['overall_accuracy']*100:.4f}",
        "MACRO_F1_4DP": f"{m['macro_f1']:.4f}",
        "MACRO_P_4DP": f"{m['macro_precision']:.4f}",
        "MACRO_R_4DP": f"{m['macro_recall']:.4f}",
        "MAJORITY_BASELINE_4DP": f"{m['majority_class_baseline']*100:.4f}",
        "D_REL": f"{(ANCHOR-oa)/ANCHOR*100:.1f}%",
        "GAP_PP": f"{ANCHOR-oa:.2f}",
        "GAP_PP_1DP": f"{ANCHOR-oa:.1f}",
    }
    curve = m.get("per_split", {})
    if "train" in curve:
        vals["TRAIN_CURVE_SUMMARY"] = (
            f"train OA {curve['train']['overall_accuracy']*100:.2f}%, "
            f"val OA {curve['validation']['overall_accuracy']*100:.2f}%, "
            f"test OA {curve['test']['overall_accuracy']*100:.2f}% (TTA), "
            f"checkpoint epochs={m.get('checkpoint_epochs')}.")
    else:
        vals["TRAIN_CURVE_SUMMARY"] = "（见 artifacts/training_history.json）"

    for fn in ["report.md", "solution.md"]:
        p = ROOT / fn
        text = p.read_text()
        filled = text
        for k, v in vals.items():
            filled = filled.replace("{{" + k + "}}", v)
        p.write_text(filled)
        print(f"filled {fn}")


if __name__ == "__main__":
    main()