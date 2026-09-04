# EVAL REPORT v3: 2607.16250_multiomics_breast_cancer_er

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v3（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 98.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | 逐项核对Rubric：A1 RNA-only RF balanced_acc=0.9398落入80-95%区间且AUC=0.9929≥0.85，得20分；A2 集成XGBoost AUC=0.9975≥单组学最优且balanced_acc=0.9706≥85%，得20分；A3 泄漏对照full_data(0.9730)≥fold_internal(0.9706)，差异方向合理，得20分。A总计60分。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘扫描显示metrics.json缺失，但assembly_summary.json与evidence_table.csv完整提供了所有必需字段。抽查RNA-only RF AUC=0.9929与样本量770/ER+72.2%均在证据文件与报告中严格一致，无抄袭论文锚值（549例/75.4%）嫌疑，实质证据齐全自洽，给38分。 |

## A 核心结果达成度（60/60）

逐项核对Rubric：A1 RNA-only RF balanced_acc=0.9398落入80-95%区间且AUC=0.9929≥0.85，得20分；A2 集成XGBoost AUC=0.9975≥单组学最优且balanced_acc=0.9706≥85%，得20分；A3 泄漏对照full_data(0.9730)≥fold_internal(0.9706)，差异方向合理，得20分。A总计60分。

## B 证据真实性/实际复现（38.0/40）

磁盘扫描显示metrics.json缺失，但assembly_summary.json与evidence_table.csv完整提供了所有必需字段。抽查RNA-only RF AUC=0.9929与样本量770/ER+72.2%均在证据文件与报告中严格一致，无抄袭论文锚值（549例/75.4%）嫌疑，实质证据齐全自洽，给38分。

## 证据与重算说明

独立重算未执行。关键实测数：样本量770，ER+ 72.2%；RNA-only RF balanced_acc 0.9398 / AUC 0.9929；集成 XGBoost balanced_acc 0.9706 / AUC 0.9975；泄漏对照 balanced_acc 0.9730。

## 结论

- **科学结论**: `supported`
- 亮点: 实验矩阵完整，严格实现了折内特征选择与泄漏对照，代码与结果文件齐全且内部一致性高，核心论断均得到数据支撑。
- 不足: 样本量（770）与论文（549）存在较大差异，可能导致性能指标显著高于论文锚值；未严格按照任务要求输出metrics.json单一文件，而是使用了assembly_summary.json替代。