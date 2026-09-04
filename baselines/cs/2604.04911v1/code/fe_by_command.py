"""Framing Error (FE) decomposition by camera command type.

Uses the frozen per-sample framing-error CSV produced by the reproduction run
(yolo11n substitute detector on the 387 real SpatialEdit-Bench camera
triplets).  Also reports a sensitivity analysis of the zoom-error handling:

  * original reproduction aggregation: NaN zoom error (non-zoom commands) is
    filled with 1.0, which penalizes every non-zoom task as a full zoom failure;
  * variant A: for commands with no zoom (ddist == 0) the zoom-direction error
    is set to 0, which matches the paper's Eq.(9) (the indicator is 0 when
    ddist == 0).

This shows that a large part of the gap between the reproduction FE (0.690)
and the paper FE (0.527) is explained by the aggregation of non-zoom commands,
not only by the detector substitution.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"F:\dataset\2604.04911v1")
FE_CSV = ROOT / "results" / "fe_yolo11n_full" / "camera_framing_error_per_sample.csv"
OUT_DIR = Path(__file__).resolve().parent.parent / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def cmd_type(r) -> str:
    parts = []
    if abs(r["cmd_dyaw"]) > 1e-6:
        parts.append("Y")
    if abs(r["cmd_dpitch"]) > 1e-6:
        parts.append("P")
    if abs(r["cmd_ddist"]) > 1e-6:
        parts.append("D")
    return "+".join(parts) if parts else "none"


def fe_of(angle_err: float, zoom_err: float) -> float:
    return (min(1.0, angle_err / 20.0) + min(1.0, zoom_err)) / 2.0


def main() -> None:
    fe = pd.read_csv(FE_CSV)
    fe["cmd"] = fe.apply(cmd_type, axis=1)

    per_type: dict[str, dict] = {}
    for cmd, g in fe.groupby("cmd"):
        angle_err = float(g["gt_ray_diff_deg"].fillna(20.0).mean())
        zoom_err = float(g["zoom_dir_err"].fillna(1.0).mean())
        per_type[cmd] = {
            "n": int(len(g)),
            "angle_error_deg": round(angle_err, 4),
            "zoom_error": round(zoom_err, 4),
            "FE": round(fe_of(angle_err, zoom_err), 4),
            "angle_success": int(g["gt_ray_diff_deg"].notna().sum()),
            "zoom_success": int(g["log_scale"].notna().sum()),
        }

    # zoom-handling sensitivity
    n = len(fe)
    orig_angle = float(fe["gt_ray_diff_deg"].fillna(20.0).mean())
    orig_zoom = float(fe["zoom_dir_err"].fillna(1.0).mean())

    fe2 = fe.copy()
    fe2["zadj"] = np.where(fe2["cmd_ddist"].abs() < 1e-6, 0.0, fe2["zoom_dir_err"].fillna(1.0))
    va_angle = float(fe2["gt_ray_diff_deg"].fillna(20.0).mean())
    va_zoom = float(fe2["zadj"].mean())

    zoom_only = fe[fe["cmd_ddist"].abs() > 1e-6]
    zo_angle = float(zoom_only["gt_ray_diff_deg"].fillna(20.0).mean())
    zo_zoom = float(zoom_only["zoom_dir_err"].fillna(1.0).mean())

    nz = fe[fe["cmd_ddist"].abs() < 1e-6]
    nz_angle = float(nz["gt_ray_diff_deg"].fillna(20.0).mean())
    nz_zoom = float(nz["zoom_dir_err"].fillna(1.0).mean())

    report = {
        "n_total": n,
        "n_zoom": int(len(zoom_only)),
        "n_non_zoom": int(len(nz)),
        "per_command_type": per_type,
        "zoom_handling_sensitivity": {
            "original_repro_FE": round(fe_of(orig_angle, orig_zoom), 4),
            "original_repro_angle_err": round(orig_angle, 4),
            "original_repro_zoom_err": round(orig_zoom, 4),
            "variantA_nonzoom_zoom0_FE": round(fe_of(va_angle, va_zoom), 4),
            "variantA_zoom_err": round(va_zoom, 4),
            "zoom_commands_only_FE": round(fe_of(zo_angle, zo_zoom), 4),
            "zoom_commands_only_angle_err": round(zo_angle, 4),
            "zoom_commands_only_zoom_err": round(zo_zoom, 4),
            "non_zoom_commands_only_FE": round(fe_of(nz_angle, nz_zoom), 4),
            "non_zoom_commands_only_angle_err": round(nz_angle, 4),
            "non_zoom_commands_only_zoom_err": round(nz_zoom, 4),
            "paper_FE": 0.527,
            "explanation": (
                "original repro fills NaN zoom-error (non-zoom commands) with 1.0, "
                "inflating FE; paper Eq.(9) indicator is 0 when ddist==0 (variant A)"
            ),
        },
    }
    out = OUT_DIR / "fe_by_command.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
