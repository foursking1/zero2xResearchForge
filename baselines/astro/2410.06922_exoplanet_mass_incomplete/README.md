# 2410.06922 — Exoplanet mass imputation reproduction (L1)

> 复现 Lalande, Tasker & Doya (2024, arXiv:2410.06922)《Estimating Exoplanet Mass
> using Machine Learning on Incomplete Datasets》的核心结果于冻结快照
> `../data/pscomppars_2026-08-13.csv`（NASA Exoplanet Archive PSCompPars, 2026-08-13,
> 6,336 颗行星）。所有数字由代码从冻结数据重算；不依赖任何外部网络/权重。

## 快速开始（默认 = 论文级完整跑，约 20 分钟，纯 CPU）

```bash
cd code
python run_experiments.py     # 产出 results/evidence_table.csv, metrics.json,
                              # imputed_*.csv, distribution_*.csv, distributions_stats.csv
python figures.py             # 产出 figure_*.{png,svg}
```

开发冒烟测试（缩短评估集，结果与报告数值不同，仅供联调）：

```bash
EXO_QUICK=1 python run_experiments.py
python figures.py
```

依赖：`python>=3.10`, `numpy`, `pandas`, `scipy`, `scikit-learn`, `torch`(CPU),
`matplotlib`。离线环境已具备。

## 关键文件

| 文件 | 说明 |
|---|---|
| `claim.md` | 可证伪声称 + 失败条件 + 四档结论（`partially_supported`） |
| `solution.md` | 方法说明与结果摘要 |
| `report.md` | 完整报告（协议、算法、结果、鲁棒性、边界，≤2 页） |
| `code/config.py` | 数据集/超参/路径配置（全部出自论文 §3） |
| `code/data_utils.py` | 数据加载、SHA-256 校验、三个数据集构造、150 测试划分 |
| `code/imputers.py` | 五种算法 + 基线实现（含 GAIN 的 torch 实现、kNN×KDE 分布） |
| `code/baselines.py` | mBM-class 基线（完整数据回归）与 PS-CP (Chen & Kipping 2017) |
| `code/run_experiments.py` | 三个数据集 + distribution/RV + 鲁棒性 + 表格/JSON 输出 |
| `code/figures.py` | 关键图（散点、误差条、分布） |
| `results/evidence_table.csv` | 逐算法逐数据集证据表（数据集/算法/协议/n_test/ϵ/ϵ_150） |
| `results/metrics.json` | 总体指标：排名、方向、GAIN 差距、RV、分布、鲁棒性 |

## 裁判抽查复核（B 部分）

以下两个关键数的重算路径（默认模式、种子固定）：

1. **完整子集 kNN×KDE 的 ϵ**：`run_experiments.run_complete` → `imputers.KNNKDE`，
   `results/metrics.json["complete_subset"]["eps"]["knnkde"]` = **0.913903**。
2. **全档案 GAIN 的 ϵ**：`run_full` 的 batch-LOO（41 批 × 60 颗，种子 = 42+批次×7919），
   `results/metrics.json["full_archive"]["GAIN"]["eps_full"]` = **4.540158**

依赖 CPU/BLAS 的浮点顺序，1e-4 量级内的逐位差异属正常；结构性结论稳定。

## 数据口径提示

论文快照 2023-02-02（5,251 颗、质量缺失率 72.8%、完整子集 550 颗）与本包 2026-08-13
（6,336 颗、61.7%、完整子集 2,009 颗）不同——绝对 ϵ 不可对账，判分以结构与方向为主（详见 report.md
§3/§6 与 claim.md）。

## 结论要点

- 支持：完整子集最优组排名（kNN×KDE≈0.914 最优、kNN-Imputer/MissForest≈0.96）、GAIN 一贯最差、
  全档案使 kNN-Imputer/GAIN 显著变差、kNN×KDE 概率分布指示置信度。
- 未复现（快照翻转）：全档案对 kNN×KDE/MissForest/MICE 的"改善"；八属性"小幅提升"。→ `partially_supported`。