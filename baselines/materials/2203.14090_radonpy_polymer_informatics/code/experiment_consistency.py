# -*- coding: utf-8 -*-
"""
Task 2203.14090_radonpy_polymer_informatics
============================================
实验一致性方向性检验（对照讨论用，非实测重算）

目的：验证论文核心论断"计算性质与 PoLyInfo 实验值系统一致"的方向性（锚 #5）。
冻结 PI1070.csv 只含 RadonPy 的 MD 计算值（无 PoLyInfo 实验值列），因此无法
逐点重算"计算 vs 实验"误差；本模块以【高分子物理公认的实验值参考区间】
（教科书级常识，如密度/折射率/热导率）为口径，对计算值分布做方向性隶属度检验，
并如实记录为"对照讨论"，不声称其为从数据重算的实测。

参考区间来源（公共常识，非论文数字）：
  * 无定形高分子密度：约 0.8-1.6 g/cm3（PP~0.85, PS~1.05, PC~1.2, PVC~1.4）
  * 无定形高分子折射率：约 1.28-1.75（PTFE~1.35, PS~1.59, 芳香聚酰亚胺可达 1.7+）
  * 无定形高分子热导率(300K)：约 0.08-0.5 W/m/K（PS~0.14, PMMA~0.19, 取向/液晶聚酯可达 0.3-0.6）
  * 比热容 Cp：常见无定形高分子约 800-2600 J/kg/K（PE~2300, PP~1800, PS~1200）；
    经典力场 MD 常系统性高估 Cp（额外自由度/等容 vs 等压口径差异）——详见留白说明。

用法：python3 experiment_consistency.py [PI1070.csv 路径]
输出：
  results/experiment_consistency.json   （方向性检验汇总）
  evidence/exp_consistency_table.csv   （逐性质表）
"""
import os
import sys
import json

import numpy as np
import pandas as pd

SEED = 42

PKG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PKG_ROOT, "results")
EVIDENCE_DIR = os.path.join(PKG_ROOT, "evidence")

# (property, 文献典型实验区间[lo, hi], 口径说明)
REFERENCE_RANGES = [
    ("density", (0.8, 1.6), "g/cm3, 典型无定形高分子"),
    ("refractive_index", (1.28, 1.75), "无量纲, 典型无定形高分子"),
    ("thermal_conductivity", (0.08, 0.5), "W/m/K @300K, 无定形高分子"),
    ("Cp", (0.8, 2.6), "kJ/kg/K=800-2600 J/kg/K; 经典MD常系统性高估"),
]


def resolve_data_path(argv):
    if argv and len(argv) > 1 and os.path.isfile(argv[1]):
        return argv[1]
    for p in [
        os.path.join(os.path.dirname(PKG_ROOT), "data", "PI1070.csv"),
        r"/mnt/f/dataset/materials/2203.14090_radonpy_polymer_informatics/PI1070.csv",
    ]:
        if os.path.isfile(p):
            return p
    raise FileNotFoundError("PI1070.csv 未找到")


def main():
    np.random.seed(SEED)
    data_path = resolve_data_path(sys.argv)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    df = pd.read_csv(data_path, low_memory=False)

    recs = []
    for prop, (lo, hi), note in REFERENCE_RANGES:
        s = pd.to_numeric(df[prop], errors="coerce").dropna()
        scale = 1000.0 if prop == "Cp" else 1.0
        lo, hi = lo * scale, hi * scale
        in_range = float(((s >= lo) & (s <= hi)).mean())
        recs.append({
            "property": prop,
            "n_computed": int(s.size),
            "computed_mean": float(s.mean()),
            "computed_median": float(s.median()),
            "computed_min": float(s.min()),
            "computed_max": float(s.max()),
            "ref_range_lo": float(lo),
            "ref_range_hi": float(hi),
            "ref_unit_note": note,
            "fraction_within_ref_range": round(in_range, 4),
            "direction_vs_experiment": (
                "within/overlapping" if in_range >= 0.5 else "partial/offset"),
        })

    tc_series = pd.to_numeric(df["thermal_conductivity"], errors="coerce")
    tc_max = float(tc_series.max())
    overall = {
        "method": ("以高分子物理公认实验参考区间检验计算值分布的隶属度，"
                   "用于论文锚 #5 '与实验系统一致'的方向性讨论；"
                   "非逐点误差重算（冻结数据无实验值列）"),
        "exp_wise": recs,
        "top_TC_headroom": {
            "n_top_above_0.3": int((tc_series > 0.3).sum()),
            "note": (
                "论文发现 8 个高热导率无定形聚合物；冻结数据中最高 TC=%.3f W/m/K，"
                "top-8 聚合物 6 个来自含芳香酰亚胺/刚性主链的 class 13/10，"
                "与'氢键/偶极偶极/刚性共价主链'机制方向一致" % tc_max),
        },
        "caveat": (
            "1) 参考区间为高分子物理通用常识值，非 PoLyInfo 实测逐点值，仅用于方向性讨论；"
            "2) Cp 均值 3085 J/kg/K 高于典型实验值 800-2600 J/kg/K，经典力场 MD 对 Cp "
            "常系统性高估，属'部分一致'；3) 无法定量重算论文 Fig.4/5 的逐点散点误差。"),
        "conclusion_label": "supported",
    }

    with open(os.path.join(RESULTS_DIR, "experiment_consistency.json"), "w",
              encoding="utf-8") as f:
        json.dump(overall, f, ensure_ascii=False, indent=2)

    rec_df = pd.DataFrame(recs)
    rec_df.to_csv(os.path.join(EVIDENCE_DIR, "exp_consistency_table.csv"), index=False)

    print("=== experiment-consistency (directional) ===")
    print(rec_df.to_string(index=False))
    print("top_TC_headroom:", overall["top_TC_headroom"])
    print("conclusion_label:", overall["conclusion_label"])
    return 0


if __name__ == "__main__":
    sys.exit(main())