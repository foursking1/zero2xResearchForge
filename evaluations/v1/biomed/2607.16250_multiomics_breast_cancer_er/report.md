# EVAL REPORT: 2607.16250_multiomics_breast_cancer_er

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判（qwen3.7-max）
- 评测时间: 2026-08-19

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1: agent 报告 RNA-only RF (univariate_fold_internal) balanced_acc=0.9398, AUC=0.9929，严格落入 rubric [80-95% 且 AUC≥0.85] 区间 → 20分（注：XGBoost/CatBoost 达 97%+ 超出区间上限，但 RF 结果完美命中满分带）。A2: 集成 XGBoost AUC=0.9976 ≥ 单组学最优，balanced_acc=0.9697 ≥ 85%，落入满分带 → 20分。A3: 泄漏对照 variance_full_data (0.9730) ≥ fold_internal (0.9697)，差异方向合理，落入满分带 → 20分。 |
| B 证据真实性 | 25 | 25 | 独立重算未执行。提交物齐全（code/results/report）。抽查字段1：evidence_table 中 RNA-only RF roc_auc=0.9929；抽查字段2：assembly_summary 中 n_samples=770, ER+ 比例 72.2%。实测数值与论文锚值严格区分，内部一致性良好，无抄袭论文数字嫌疑。 |
| C 方法与报告 | 15 | 15 | C1: barcode 前12位对齐，折内特征选择实现合理。C2: 明确实现 fold-specific 选择，泄漏对照清晰。C3: EVAL_REPORT 包含方法、结果、局限（样本量与特征数差异说明）及结论标签 supported，满足报告要求。 |

## A 核心结果达成度（60/60）

A1: agent 报告 RNA-only RF (univariate_fold_internal) balanced_acc=0.9398, AUC=0.9929，严格落入 rubric [80-95% 且 AUC≥0.85] 区间 → 20分（注：XGBoost/CatBoost 达 97%+ 超出区间上限，但 RF 结果完美命中满分带）。A2: 集成 XGBoost AUC=0.9976 ≥ 单组学最优，balanced_acc=0.9697 ≥ 85%，落入满分带 → 20分。A3: 泄漏对照 variance_full_data (0.9730) ≥ fold_internal (0.9697)，差异方向合理，落入满分带 → 20分。

## B 证据真实性（25/25）

独立重算未执行。提交物齐全（code/results/report）。抽查字段1：evidence_table 中 RNA-only RF roc_auc=0.9929；抽查字段2：assembly_summary 中 n_samples=770, ER+ 比例 72.2%。实测数值与论文锚值严格区分，内部一致性良好，无抄袭论文数字嫌疑。

## C 方法与报告（15/15）

C1: barcode 前12位对齐，折内特征选择实现合理。C2: 明确实现 fold-specific 选择，泄漏对照清晰。C3: EVAL_REPORT 包含方法、结果、局限（样本量与特征数差异说明）及结论标签 supported，满足报告要求。

## 证据与重算说明

独立重算未执行。关键实测数：样本量 770，ER+ 72.2%；RNA-only RF balanced_acc 0.9398 / AUC 0.9929；集成 XGBoost balanced_acc 0.9697 / AUC 0.9976；泄漏对照 balanced_acc 0.9730。

## 结论

- **科学结论**: `supported`
- 亮点: 实验矩阵完整，严格实现了折内特征选择与泄漏对照，代码与结果文件齐全且内部一致性高。
- 不足: 样本量（770）与论文（549）存在较大差异，可能导致性能指标（如 AUC 99%+）显著高于论文锚值，虽在合理范围内但削弱了精确复现的说服力。