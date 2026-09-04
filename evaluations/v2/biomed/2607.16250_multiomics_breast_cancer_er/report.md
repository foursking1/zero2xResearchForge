# EVAL REPORT v2: 2607.16250_multiomics_breast_cancer_er

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 98.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1: agent 报告 RNA-only RF (univariate_fold_internal) balanced_acc=0.9398, AUC=0.9929，严格落入 rubric [80-95% 且 AUC≥0.85] 区间，且 evidence_table.csv 中有落盘证据，得 20 分。A2: 集成模型 XGBoost (RNA+CNV+RPPA) AUC=0.9976 ≥ 单组学最优 AUC(0.9971)，balanced_acc=0.9697 ≥ 85%，落入满分带，evidence_table.csv 证据齐全，得 20 分。A3: 泄漏对照 univariate_full_data (0.9730) ≥ fold_internal (0.9706)，差异方向合理，evidence_table.csv 包含完整对照数据，得 20 分。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘扫描显示 metrics.json 缺失，但 evidence_table.csv 与 assembly_summary.json 存在且包含了所有要求的实测指标与样本统计。抽查字段1（RNA-only RF roc_auc=0.9929）与抽查字段2（n_samples=770, ER+ 72.2%）在证据文件与报告中严格一致。虽未严格生成名为 metrics.json 的单一文件，但实质证据齐全且可核对，落入 [30,40] 档，给 38 分。 |

## A 核心结果达成度（60/60）

A1: agent 报告 RNA-only RF (univariate_fold_internal) balanced_acc=0.9398, AUC=0.9929，严格落入 rubric [80-95% 且 AUC≥0.85] 区间，且 evidence_table.csv 中有落盘证据，得 20 分。A2: 集成模型 XGBoost (RNA+CNV+RPPA) AUC=0.9976 ≥ 单组学最优 AUC(0.9971)，balanced_acc=0.9697 ≥ 85%，落入满分带，evidence_table.csv 证据齐全，得 20 分。A3: 泄漏对照 univariate_full_data (0.9730) ≥ fold_internal (0.9706)，差异方向合理，evidence_table.csv 包含完整对照数据，得 20 分。

## B 证据真实性/实际复现（38.0/40）

磁盘扫描显示 metrics.json 缺失，但 evidence_table.csv 与 assembly_summary.json 存在且包含了所有要求的实测指标与样本统计。抽查字段1（RNA-only RF roc_auc=0.9929）与抽查字段2（n_samples=770, ER+ 72.2%）在证据文件与报告中严格一致。虽未严格生成名为 metrics.json 的单一文件，但实质证据齐全且可核对，落入 [30,40] 档，给 38 分。

## 证据与重算说明

独立重算未执行。关键实测数：样本量 770，ER+ 72.2%；RNA-only RF balanced_acc 0.9398 / AUC 0.9929；集成 XGBoost balanced_acc 0.9697 / AUC 0.9976；泄漏对照 balanced_acc 0.9730。evidence_table.csv 与 assembly_summary.json 数据完整且与报告一致。

## 结论

- **科学结论**: `supported`
- 亮点: 实验矩阵完整，严格实现了折内特征选择与泄漏对照，代码与结果文件齐全且内部一致性高，核心论断均得到数据支撑。
- 不足: 样本量（770）与论文（549）存在较大差异，可能导致性能指标（如 AUC 99%+）显著高于论文锚值；未严格按照任务要求输出 metrics.json 单一文件，而是分散在多个 JSON/CSV 中。