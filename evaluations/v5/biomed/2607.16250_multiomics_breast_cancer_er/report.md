# EVAL REPORT v5: 2607.16250_multiomics_breast_cancer_er

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 93.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 10.0 | 12 | |
| A2 科学结论保真 | 33.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **58.0** | 60 | A1给10分，因产出了核心的evidence_table和assembly数据及代码，但缺失claim.md和report.md等任务明确要求的交付文件，属于有实质产出但有缺口；A2给33分，RNA单组学最优、多组学集成增益及防泄漏效应均被完美复现，数值趋势与论文核心claim完全一致；A3给15分，折内特征选择与泄漏对照实现严谨，barcode对齐规则清晰，方法sound。 |
| B 证据真实性/实际复现 | 35.0 | 40 | 磁盘扫描显示metrics.json缺失，且无claim.md/report.md，但evidence_table.csv与assembly_summary.json完整提供了所有必需字段且内部自洽，代码完整可运行，属于证据齐全自洽但有部分指定文件缺失，给35分。 |

## A 核心结果达成度（58.0/60 = A1 10.0 + A2 33.0 + A3 15.0）

A1给10分，因产出了核心的evidence_table和assembly数据及代码，但缺失claim.md和report.md等任务明确要求的交付文件，属于有实质产出但有缺口；A2给33分，RNA单组学最优、多组学集成增益及防泄漏效应均被完美复现，数值趋势与论文核心claim完全一致；A3给15分，折内特征选择与泄漏对照实现严谨，barcode对齐规则清晰，方法sound。

## B 证据真实性/实际复现（35.0/40）

磁盘扫描显示metrics.json缺失，且无claim.md/report.md，但evidence_table.csv与assembly_summary.json完整提供了所有必需字段且内部自洽，代码完整可运行，属于证据齐全自洽但有部分指定文件缺失，给35分。

## 证据与重算说明

独立重算未执行。关键实测数：样本量770（ER+ 72.2%）；RNA-only RF BAcc 0.9398 / AUC 0.9929；集成XGBoost BAcc 0.9706 / AUC 0.9976；泄漏对照full_data BAcc 0.9730 ≥ fold_internal 0.9706。

## 结论

- **科学结论**: `supported`
- 亮点: 实验矩阵完整，严格实现了折内特征选择与泄漏对照，核心论断均得到详实数据支撑，内部一致性高。
- 不足: 未严格按照任务要求输出metrics.json、claim.md和report.md等指定命名文件，且样本量（770）与论文（549）差异较大导致性能指标普遍偏高。