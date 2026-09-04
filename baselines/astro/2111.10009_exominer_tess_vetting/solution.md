# solution.md — ExoMiner TESS vetting score-behaviour analysis (2111.10009)

**Verdict: `supported`** — 复现论文「ExoMiner 评分对 TESS 候选高判别力、低 MES 保守」论断在冻结目录口径下成立。

## 数据
NASA/ExoMiner 官方仓库发布的 TESS SPOC 2-min vetting 表（S1–67，`score>0.1` 展示子集）：11,289 行 × 16 列，SHA-256 `6B4F2491…E862` 校验通过。全部统计确定性、可重算；无合成数据、无金标重训练。

## 方法与流水线
`code/data_loader.py`（冻结文件定位 + 形状/SHA 校验）→ `code/run_analysis.py`（解析、阈值、分箱、秩相关、图、证据导出）→ `results/metrics.json` / `results/evidence_table.csv` / `results/check3.txt` / `results/figures/*.png` / `evidence/*.csv`。抽查脚本 `code/verify_check3.py` 独立重算三个关键数。
运行：`cd code && python3 run_analysis.py`；`python3 verify_check3.py`。

## 结果摘要

| 项 | 数值 |
|---|---|
| 分数分布 | min 0.101 / 中位 0.755 / max 0.999；score≥0.5 = **7,229（64.0%）**；score>0.99 = **1,070（9.5%）** |
| 低 MES 保守性 | MES<10.5：3,242 中 **30 个（0.93%）** >0.99；MES≥10.5：8,047 中 1,040（12.92%） |
| MES 分箱 >0.99 占比 | 0–5→0%（空箱）· 5–10→0.69% · 10–15→5.80% · 15–20→11.14% · 20–30→15.49% · ≥30→19.13%（单调上升 ✓） |
| 高分候选人口 | score>0.99 & MES>10.5 = **1,040**；半径中位 6.79 R⊕（0.59–20.84）；周期中位 3.92 d（0.28–124.7） |
| 分数-信号强度 | Spearman(score, MES)=**+0.183**；Spearman(score, SNR)=**+0.197**（正相关、中等强度）；Mann-Whitney p≈3.7e-84 |
| 四档结论 | **supported** |

## 与论文锚对照（论文数字仅作对照，不作实测）
- **保守性**：TESS 0.93%（30/3,242） vs 论文 Kepler 2.1%（20/943）——方向一致、量级相当、TESS 更保守。归因：score>0.1 展示子集使 >0.99 占比为全量上界；TESS SPOC vs Kepler PDC 管道/样本差异；MES 报告下限（本导出 ~7.1）+ 版本差异。
- **高分人口**：1,040 vs 论文 301（Kepler）同构（score>0.99 且 MES>10.5）；TESS 周期上限 ~125 d vs Kepler 280 d 属 TESS 扇区观测窗口的构造性差异，半径上界更宽（稀释双星/食双星污染）。
- **不可重算项**：precision/recall（0.936/0.88–0.73）与 301 颗「验证」状态需 TFOPWG 金标，冻结包不含 → 判定范围限评分行为，已在 report/claim 明示。

## 局限
1) 目录为 score>0.1 展示子集（>0.99 计数为界内计数、占比为上界）；2) TESS vs Kepler 属跨任务对比；3) 无金标 → 未重算精度/召回。三点均在报告与 claim 中显式声明。

## 提交物
`claim.md`（四档判定+逐项对比+归因）、`code/`（3 脚本+requirements+README）、`results/evidence_table.csv`（MES 分箱表+分数分布行）、`results/metrics.json`（全部指标）、`results/figures/`（5 图）、`evidence/`（高分人口与低 MES>0.99 子集导出）、`report.md`（方法/结果/局限）。