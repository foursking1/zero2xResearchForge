"""Build results/evidence_table.csv and results/metrics.json.

The evidence table aggregates:
  * claim numbers transcribed from the paper tables (marked 口径=paper citation),
  * values computed from the frozen data (marked 口径=frozen-data computation),
  * arithmetic / ordering consistency checks (marked 口径=paper verification).

All numbers in this file either come from the frozen data analysis
(frozen_data_analysis.json, paper_table_verification.json) or are explicitly
quoted as paper citations.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "results"
FDA = json.loads((OUT_DIR / "frozen_data_analysis.json").read_text(encoding="utf-8"))
PTV = json.loads((OUT_DIR / "paper_table_verification.json").read_text(encoding="utf-8"))
FEBC = json.loads((OUT_DIR / "fe_by_command.json").read_text(encoding="utf-8"))

# ---------------------------------------------------------------------------
# evidence rows: (metric, value, 口径/scope, source/notes)
# 口径 values: "paper_citation" | "frozen_data_computation" | "paper_verification"
rows: list[dict] = []


def add(metric: str, value, scope: str, notes: str = ""):
    if isinstance(value, float):
        value = round(value, 6)
    rows.append({"指标名": metric, "数值": value, "口径": scope, "说明": notes})


# ---------------- C01: SpatialEdit-Bench ----------------------------------
c1 = PTV["claim_C01_numbers"]
add("C01_SpatialEdit_Moving_Score", c1["moving_score"], "paper_citation", "论文 Table 2 (SpatialEdit 行)")
add("C01_SpatialEdit_Rotation_Score", c1["rotation_score"], "paper_citation", "论文 Table 2 (SpatialEdit 行)")
add("C01_SpatialEdit_Viewpoint_Error", c1["viewpoint_error"], "paper_citation", "论文 Table 2 (SpatialEdit 行)")
add("C01_SpatialEdit_Framing_Error", c1["framing_error"], "paper_citation", "论文 Table 2 (SpatialEdit 行)")
add("C01_SpatialEdit_Object_Overall", c1["object_overall"], "paper_citation", "论文 Table 2 (SpatialEdit 行)")
add("C01_SpatialEdit_Camera_Overall_Error", c1["camera_overall_error"], "paper_citation", "论文 Table 2 (SpatialEdit 行)")
for col, best in PTV["claim_C01_best_in_table2"].items():
    add(f"C01_Table2_{col}_best_is_SpatialEdit", best["method"] == "SpatialEdit", "paper_verification",
        f"Table 2 该列最优值 {best['value']} 由 {best['method']} 取得")
for name, chk in PTV["overall_arithmetic_checks"].items():
    if chk["object_overall_calculated"] is not None:
        add(f"C01_{name}_ObjectOverall=(MS+RS)/2_match", chk["object_overall_match"], "paper_verification",
            f"计算={chk['object_overall_calculated']} vs 报告={chk['object_overall_reported']}")
    if chk["camera_overall_calculated"] is not None:
        add(f"C01_{name}_CameraOverall=(VE+FE)/2_match", chk["camera_overall_match"], "paper_verification",
            f"计算={chk['camera_overall_calculated']} vs 报告={chk['camera_overall_reported']}")

# frozen-data benchmark structure
meta = FDA["meta"]
add("Benchmark_meta_total_tasks", meta["total_tasks"], "frozen_data_computation", "SpatialEdit_Bench_Meta_File.json")
add("Benchmark_meta_camera_tasks", meta["camera_task_count"], "frozen_data_computation", "meta 文件 camera 类型条目")
add("Benchmark_meta_rotate_tasks", meta["rotate_task_count"], "frozen_data_computation", "meta 文件 rotate 类型条目")
add("Benchmark_meta_move_tasks", meta["move_task_count"], "frozen_data_computation", "meta 文件 move 类型条目")
add("Benchmark_camera_complete_triplets", FDA["camera_triplets"]["n_complete_triplets_on_disk"], "frozen_data_computation",
    "相机子集含完整 src/gt/pred/json/prompt 五件套的样本数")
add("Benchmark_camera_scene_dirs", FDA["camera_triplets"]["n_scene_dirs"], "frozen_data_computation", "相机结果子集场景目录数")
add("Benchmark_image_readable_fraction", FDA["image_sanity"]["readable_fraction"], "frozen_data_computation", "src/gt/pred 图像可读比例")
add("Benchmark_image_size", list(FDA["image_sanity"]["size_counter"].keys())[0], "frozen_data_computation", "所有图像尺寸")

# frozen-data camera command geometry
cc = FDA["camera_commands"]
add("Benchmark_yaw_multiples_of_45_frac", cc["yaw_multiples_of_45_frac"], "frozen_data_computation", "论文称 yaw 按 45° 离散")
add("Benchmark_pitch_multiples_of_15_frac", cc["pitch_multiples_of_15_frac"], "frozen_data_computation", "论文称 pitch 按 15° 离散")
add("Benchmark_prompt_json_consistent_frac", cc["prompt_json_consistent_frac"], "frozen_data_computation", "prompt 文本与 JSON edit_ypd 一致比例")
add("Benchmark_camera_zoom_in_tasks", cc["n_zoom_in"], "frozen_data_computation", "distance<0 (zoom in) 任务数")
add("Benchmark_camera_zoom_out_tasks", cc["n_zoom_out"], "frozen_data_computation", "distance>0 (zoom out) 任务数")

# frozen-data FE / VE reproduction
fe = FDA["framing_error_repro"]
add("C01_FE_repro_overall_FE", fe["overall_FE_error"], "frozen_data_computation",
    "387 样本 yolo11n 替代检测器；angle 归一化 /20°; zoom NaN 按 1.0 填充")
add("C01_FE_repro_angle_error_deg", fe["angle_error_deg"], "frozen_data_computation", "平均射线夹角误差(度)，det_fail 按 20° 填充")
add("C01_FE_repro_zoom_error", fe["zoom_error"], "frozen_data_computation", "缩放方向误差，非 zoom 命令 NaN 按 1.0 填充")
add("C01_FE_repro_angle_success", fe["angle_success"], "frozen_data_computation", "angle 分量有效样本数 (226/387)")
add("C01_FE_repro_paper_gap", fe["paper_gap"], "frozen_data_computation", "0.6902 - 论文 0.527")
add("C01_FE_paper_consistent", abs(fe["overall_FE_error"] - 0.527) < 0.01, "paper_verification",
    "复现 FE 是否等于论文 0.527（否：0.6902）")

# FE decomposition by command type + zoom-handling sensitivity
for cmd, info in FEBC["per_command_type"].items():
    add(f"C01_FE_by_cmd_{cmd}_FE", info["FE"], "frozen_data_computation",
        f"命令类型 {cmd} (n={info['n']}); angle_err={info['angle_error_deg']}°, zoom_err={info['zoom_error']}")
zs = FEBC["zoom_handling_sensitivity"]
add("C01_FE_repro_zoom_handling_variantA_FE", zs["variantA_nonzoom_zoom0_FE"], "frozen_data_computation",
    "非 zoom 命令 zoom 误差按 0 计（对应论文 Eq.9 在 ddist==0 时指示为 0）")
add("C01_FE_repro_zoom_only_FE", zs["zoom_commands_only_FE"], "frozen_data_computation",
    f"仅 106 个 zoom 命令样本")
add("C01_FE_repro_nonzoom_only_FE", zs["non_zoom_commands_only_FE"], "frozen_data_computation",
    f"仅 {FEBC['n_non_zoom']} 个非 zoom 命令样本（zoom 误差按 1.0 填充）")

ve = FDA["viewpoint_error_repro"]
add("C01_VE_repro_overall_VE", ve["overall_VE_error"], "frozen_data_computation",
    "8 样本 VGGT-1B 公开权重 smoke 测试，平移误差不稳定")
add("C01_VE_repro_gt_xyz_err", ve["gt_xyz_err"], "frozen_data_computation", "baseline 归一化平移误差均值（数值巨大）")
add("C01_VE_repro_gt_ypr_err", ve["gt_ypr_err"], "frozen_data_computation", "旋转测地误差/90° 均值")
add("C01_VE_repro_paper_gap", ve["paper_gap"], "frozen_data_computation", "2295.46 - 论文 0.243")
add("C01_VE_paper_consistent", abs(ve["overall_VE_error"] - 0.243) < 0.01, "paper_verification",
    "复现 VE 是否等于论文 0.243（否：2295.46）")
cam_overall = FDA.get("camera_overall_repro", {})
if cam_overall:
    add("C01_CameraOverall_repro", cam_overall["camera_overall_error"], "frozen_data_computation",
        "(VE_repro+FE_repro)/2，受 VE 不稳定主导")

# ---------------- C02: GEdit-Bench-EN -------------------------------------
c2 = PTV["claim_C02_numbers"]
add("C02_GEdit_SC", c2["SC"], "paper_citation", "论文 Table 5 (SpatialEdit 行)")
add("C02_GEdit_PQ", c2["PQ"], "paper_citation", "论文 Table 5 (SpatialEdit 行)")
add("C02_GEdit_Overall", c2["Overall"], "paper_citation", "论文 Table 5 (SpatialEdit 行)")
ctx = PTV["claim_C02_context"]
add("C02_open_source_rank_by_overall", ctx["open_source_rank_by_overall"], "paper_verification",
    f"在 {ctx['n_open_source_models']} 个开源模型中以 Overall 排名第 {ctx['open_source_rank_by_overall']}（高于多数开源模型）")
add("C02_data_available_in_frozen_set", False, "frozen_data_computation",
    "冻结数据中无 GEdit-Bench 评测数据，无法独立复现")

# ---------------- C03: multi-task trade-off --------------------------------
c3 = PTV["claim_C03_table3"]
add("C03_full_model_MovScore", c3["full_model_mov"], "paper_citation", "论文 Table 3 (Mov+Rot+Cam)")
add("C03_full_model_RotScore", c3["full_model_rot"], "paper_citation", "论文 Table 3 (Mov+Rot+Cam)")
add("C03_full_model_CamError", c3["full_model_cam"], "paper_citation", "论文 Table 3 (Mov+Rot+Cam)")
add("C03_full_is_best_Mov", c3["full_is_best_mov"], "paper_verification", f"Mov 最优 = {c3['best_mov_over_all_rows']}")
add("C03_full_is_best_Rot", c3["full_is_best_rot"], "paper_verification", f"Rot 最优 = {c3['best_rot_over_all_rows']}")
add("C03_full_is_best_Cam", c3["full_is_best_cam"], "paper_verification", f"Cam 最优(最低) = {c3['best_cam_over_all_rows']}")
add("C03_data_available_in_frozen_set", False, "frozen_data_computation",
    "冻结数据中无训练消融数据，无法独立复现")

# ---------------- C04: Spearman reliability --------------------------------
c4 = PTV["claim_C04_table4"]
add("C04_Spearman_FE", c4["FE"], "paper_citation", "论文 Table 4")
add("C04_Spearman_VE", c4["VE"], "paper_citation", "论文 Table 4")
add("C04_Spearman_GPT4.1", c4["GPT4.1"], "paper_citation", "论文 Table 4")
add("C04_VE_highest", c4["VE_highest"], "paper_verification", "VE > FE > GPT4.1")
add("C04_FE_above_GPT4.1", c4["FE_above_GPT4.1"], "paper_verification", "FE > GPT4.1")
add("C04_data_available_in_frozen_set", False, "frozen_data_computation",
    "冻结数据中无受控验证(细粒度视角渲染+排序)数据，无法独立复现")


# ---------------------------------------------------------------------------
def write_outputs() -> None:
    # evidence_table.csv
    fieldnames = ["指标名", "数值", "口径", "说明"]
    with open(OUT_DIR / "evidence_table.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # metrics.json (machine readable; keys align with 指标名)
    metrics = {}
    for r in rows:
        key = r["指标名"]
        metrics[key] = {
            "value": r["数值"],
            "scope": r["口径"],
            "notes": r["说明"],
        }
    (OUT_DIR / "metrics.json").write_text(
        json.dumps({"paper_id": "2604.04911v1", "metrics": metrics}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"evidence_table.csv: {len(rows)} rows")
    print(f"metrics.json: {len(metrics)} metrics")


if __name__ == "__main__":
    write_outputs()
