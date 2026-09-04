# EVAL REPORT v2: 2205.13760_tranception_proteingym

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 98.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1（20/20）：agent 解析了 6 个冻结 assay，核验了 DMS_score 方向，并在 metrics.json 中正确记录了 MSA_Neff 等元数据，证据齐全。A2（20/20）：实现了 ESM-2 (650M/8M) 与 BLOSUM62 基线，evidence_table.csv 中包含了所有 assay 的双方法对比结果。A3（20/20）：ESM-2 650M 在 5/6 assay 上 Spearman ρ 优于 BLOSUM62（平均 0.463 vs 0.245），主论断方向一致，metrics.json 与 evidence_table.csv 提供了完整的实测数据支撑。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘扫描显示 metrics.json、evidence_table.csv 及大量中间打分结果（如 baseline_scores、lm_scores）均存在。evidence_table 中的数值（如 BRCA1 0.5198，GFP 0.1079）与 report.md 和 claim.md 中的报告严格一致，证明为真实复现而非抄写论文。代码文件与中间产物完整，证据链闭环。 |

## A 核心结果达成度（60/60）

A1（20/20）：agent 解析了 6 个冻结 assay，核验了 DMS_score 方向，并在 metrics.json 中正确记录了 MSA_Neff 等元数据，证据齐全。A2（20/20）：实现了 ESM-2 (650M/8M) 与 BLOSUM62 基线，evidence_table.csv 中包含了所有 assay 的双方法对比结果。A3（20/20）：ESM-2 650M 在 5/6 assay 上 Spearman ρ 优于 BLOSUM62（平均 0.463 vs 0.245），主论断方向一致，metrics.json 与 evidence_table.csv 提供了完整的实测数据支撑。

## B 证据真实性/实际复现（38.0/40）

磁盘扫描显示 metrics.json、evidence_table.csv 及大量中间打分结果（如 baseline_scores、lm_scores）均存在。evidence_table 中的数值（如 BRCA1 0.5198，GFP 0.1079）与 report.md 和 claim.md 中的报告严格一致，证明为真实复现而非抄写论文。代码文件与中间产物完整，证据链闭环。

## 证据与重算说明

独立重算未执行。关键实测数：evidence_table.csv 中 BRCA1_HUMAN LM_esm2_650M ρ=0.5198，GFP_AEQVI ρ=0.1079；metrics.json 中对应值为 0.5198288 和 0.107947，内部高度一致。中间结果 CSV 文件（如 baseline_blosum62_norm__GAL4_YEAST_Kitzman_2015.csv）证实了实际推理与打分过程。

## 结论

- **科学结论**: `supported`
- 亮点: 实验设计严谨，对 GFP 反例进行了深入的归因分析（多重突变+浅比对），并额外进行了 joint masked-marginal 校验，科学态度诚实且证据链完整。
- 不足: 受限于冻结数据包仅包含 6 个 assay，未能覆盖论文中 87 个 assay 的全貌，且未实现带检索的 Tranception 模型（受限于 MSA 数据与权重），但已在报告中充分声明。