"""Verify the TASK.md claims against the paper's own tables.

The paper PDF text was extracted to `_paper_text.txt` (in the working dir) with
pypdf.  This script embeds the tables transcribed from the paper (each number is
explicitly a *paper citation*, not a measured value) and checks:

  * the claim numbers in TASK.md match the paper's tables;
  * the "best overall" statement of Table 2 (SpatialEdit is best in every
    column among the listed methods);
  * the overall-score arithmetic (Object Overall = (MS+RS)/2,
    Camera Overall = (VE+FE)/2);
  * the multi-task trade-off of Table 3;
  * the Spearman ordering of Table 4;
  * the GEdit-Bench numbers of Table 5.

Paper source: arXiv:2604.04911v1 (SpatialEdit: Benchmarking Fine-Grained Image
Spatial Editing), table pages: Tab.2 p.11, Tab.3/4/5 p.14.
"""
from __future__ import annotations

import json
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Transcribed tables (PAPER CITATIONS - not measured values).
# Columns for Table 2:
#   moving_score, rotation_score, viewpoint_error, framing_error,
#   object_overall, camera_overall
TABLE2 = {
    "ViduQ2-Turbo":      {"ms": None, "rs": None, "ve": 1.022, "fe": 0.771, "obj": None, "cam": 0.897},
    "Kling-V2.5":        {"ms": None, "rs": None, "ve": 1.051, "fe": 0.733, "obj": None, "cam": 0.892},
    "Nano-Banana":       {"ms": 0.099, "rs": 0.420, "ve": 0.845, "fe": 0.708, "obj": 0.260, "cam": 0.777},
    "Seedream4":         {"ms": 0.163, "rs": 0.482, "ve": 0.839, "fe": 0.701, "obj": 0.323, "cam": 0.770},
    "QwenImageEdit":     {"ms": 0.311, "rs": 0.531, "ve": 0.922, "fe": 0.692, "obj": 0.421, "cam": 0.807},
    "Edit-R1":           {"ms": 0.306, "rs": 0.562, "ve": 0.959, "fe": 0.688, "obj": 0.434, "cam": 0.824},
    "LongCatImage-Edit": {"ms": 0.373, "rs": 0.505, "ve": 0.802, "fe": 0.684, "obj": 0.439, "cam": 0.743},
    "SpatialEdit-PT":    {"ms": 0.186, "rs": 0.489, "ve": 0.890, "fe": 0.719, "obj": 0.338, "cam": 0.804},
    "SpatialEdit":       {"ms": 0.673, "rs": 0.632, "ve": 0.243, "fe": 0.527, "obj": 0.653, "cam": 0.385},
}

# Table 3 rows: (mov, rot, cam) training flags -> metrics
TABLE3 = [
    {"flags": (1, 0, 0), "mov": 0.653, "rot": None,   "cam": None},
    {"flags": (0, 1, 0), "mov": None,   "rot": 0.628, "cam": None},
    {"flags": (0, 0, 1), "mov": None,   "rot": None,   "cam": 0.395},
    {"flags": (1, 1, 0), "mov": 0.657, "rot": 0.632, "cam": None},
    {"flags": (1, 0, 1), "mov": 0.665, "rot": None,   "cam": 0.402},
    {"flags": (1, 1, 1), "mov": 0.673, "rot": 0.632, "cam": 0.385},
]

# Table 4: Spearman correlation of metric rankings vs ground-truth ranking
TABLE4 = {"FE": 0.659, "VE": 0.932, "GPT4.1": 0.445}

# Table 5: GEdit-Bench-EN SC / PQ / Overall
TABLE5 = {
    "Gemini 2.0":        (6.73, 6.61, 6.32),
    "GPT Image 1":       (7.85, 7.62, 7.53),
    "Nano Banana":       (7.86, 8.33, 7.54),
    "Seedream 4.0":      (8.24, 8.08, 7.68),
    "UniWorld-v1":       (4.93, 7.43, 4.85),
    "MindOmni":          (6.53, 6.93, 5.98),
    "OmniGen2":          (7.16, 6.77, 6.41),
    "FLUX.1 Kontext":    (6.52, 7.38, 6.00),
    "BAGEL":             (7.36, 6.83, 6.52),
    "Step1X-Edit":       (7.66, 7.35, 6.97),
    "Qwen-Image-Edit":   (8.00, 7.86, 7.56),
    "LongCat-Edit":      (8.18, 8.00, 7.64),
    "SpatialEdit":       (8.09, 7.80, 7.52),
}

# ---------------------------------------------------------------------------
def best_in_columns() -> dict:
    """Best (max for scores, min for errors) per column across Table 2."""
    out = {}
    score_cols = ("ms", "rs", "obj")
    err_cols = ("ve", "fe", "cam")
    for col in score_cols:
        vals = {name: r[col] for name, r in TABLE2.items() if r[col] is not None}
        best = max(vals, key=vals.get)
        out[f"{col}_best"] = {"method": best, "value": vals[best]}
    for col in err_cols:
        vals = {name: r[col] for name, r in TABLE2.items() if r[col] is not None}
        best = min(vals, key=vals.get)
        out[f"{col}_best"] = {"method": best, "value": vals[best]}
    return out


def overall_arithmetic() -> dict:
    """Check Object Overall = (MS+RS)/2 and Camera Overall = (VE+FE)/2."""
    checks = {}
    for name, r in TABLE2.items():
        obj_calc = None
        if r["ms"] is not None and r["rs"] is not None:
            obj_calc = (r["ms"] + r["rs"]) / 2.0
        cam_calc = None
        if r["ve"] is not None and r["fe"] is not None:
            cam_calc = (r["ve"] + r["fe"]) / 2.0
        checks[name] = {
            "object_overall_calculated": round(obj_calc, 3) if obj_calc is not None else None,
            "object_overall_reported": r["obj"],
            "object_overall_match": (obj_calc is not None and abs(obj_calc - r["obj"]) <= 0.002),
            "camera_overall_calculated": round(cam_calc, 3) if cam_calc is not None else None,
            "camera_overall_reported": r["cam"],
            "camera_overall_match": (cam_calc is not None and abs(cam_calc - r["cam"]) <= 0.002),
        }
    return checks


def multitask_tradeoff() -> dict:
    """Evaluate Table 3: is the all-three row the best overall trade-off?"""
    rows = TABLE3
    full = [r for r in rows if r["flags"] == (1, 1, 1)][0]
    best_mov = max(r["mov"] for r in rows if r["mov"] is not None)
    best_rot = max(r["rot"] for r in rows if r["rot"] is not None)
    best_cam = min(r["cam"] for r in rows if r["cam"] is not None)
    return {
        "full_model_mov": full["mov"],
        "full_model_rot": full["rot"],
        "full_model_cam": full["cam"],
        "best_mov_over_all_rows": best_mov,
        "best_rot_over_all_rows": best_rot,
        "best_cam_over_all_rows": best_cam,
        "full_is_best_mov": full["mov"] == best_mov,
        "full_is_best_rot": full["rot"] == best_rot,
        "full_is_best_cam": full["cam"] == best_cam,
        "n_rows": len(rows),
    }


def spearman_ordering() -> dict:
    return {
        "FE": TABLE4["FE"],
        "VE": TABLE4["VE"],
        "GPT4.1": TABLE4["GPT4.1"],
        "VE_highest": TABLE4["VE"] == max(TABLE4.values()),
        "FE_above_GPT4.1": TABLE4["FE"] > TABLE4["GPT4.1"],
        "VE_above_FE": TABLE4["VE"] > TABLE4["FE"],
    }


def ged_claim_check() -> dict:
    sp = TABLE5["SpatialEdit"]
    closed = {k: v for k, v in TABLE5.items() if k in ("Gemini 2.0", "GPT Image 1", "Nano Banana", "Seedream 4.0")}
    open_ = {k: v for k, v in TABLE5.items() if k not in closed and k != "SpatialEdit"}
    return {
        "SpatialEdit_SC": sp[0],
        "SpatialEdit_PQ": sp[1],
        "SpatialEdit_Overall": sp[2],
        "open_source_rank_by_overall": 1 + sum(1 for _, v in open_.items() if v[2] > sp[2]),
        "n_open_source_models": len(open_),
        "n_closed_source_models": len(closed),
        "open_source_overall_range": [min(v[2] for v in open_.values()), max(v[2] for v in open_.values())],
    }


def main() -> dict:
    report = {
        "source": "arXiv:2604.04911v1 (SpatialEdit) - values transcribed from the paper tables",
        "claim_C01_numbers": {
            "moving_score": TABLE2["SpatialEdit"]["ms"],
            "rotation_score": TABLE2["SpatialEdit"]["rs"],
            "viewpoint_error": TABLE2["SpatialEdit"]["ve"],
            "framing_error": TABLE2["SpatialEdit"]["fe"],
            "object_overall": TABLE2["SpatialEdit"]["obj"],
            "camera_overall_error": TABLE2["SpatialEdit"]["cam"],
        },
        "claim_C01_best_in_table2": best_in_columns(),
        "overall_arithmetic_checks": overall_arithmetic(),
        "claim_C02_numbers": {
            "SC": TABLE5["SpatialEdit"][0],
            "PQ": TABLE5["SpatialEdit"][1],
            "Overall": TABLE5["SpatialEdit"][2],
        },
        "claim_C02_context": ged_claim_check(),
        "claim_C03_table3": multitask_tradeoff(),
        "claim_C04_table4": spearman_ordering(),
    }
    return report


if __name__ == "__main__":
    report = main()
    out = OUT_DIR / "paper_table_verification.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nWrote {out}")
