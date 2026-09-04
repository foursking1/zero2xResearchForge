# EVAL REPORT v5: 2110.14795_medmnist_v2

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 33.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **60.0** | 60 | A1(12分)：核心交付物完整，包含claim.md、report.md、code/目录及results/下的evidence_table.csv和metrics.json等所有必需文件。A2(33分)：5个数据集的实测AUC全部落入论文锚值的合理容差区间，且难度排序与论文完全一致，完美复现了核心科学论断。A3(15分)：方法严谨，代码明确区分train/val/test，归一化仅用train，早停仅用val，test仅评估一次，无数据泄漏风险，评估口径符合官方标准。 |
| B 证据真实性/实际复现 | 40 | 40 | 证据等级为2（齐全自洽）。提交物包含完整的可运行代码、metrics.json、evidence_table.csv以及详细的class_counts和split_sizes校验文件。各文件间的实测数值严格一致，证据链完整且自洽，明确区分了论文锚值与实测值，无抄数嫌疑，授予满分40分。 |

## A 核心结果达成度（60.0/60 = A1 12.0 + A2 33.0 + A3 15.0）

A1(12分)：核心交付物完整，包含claim.md、report.md、code/目录及results/下的evidence_table.csv和metrics.json等所有必需文件。A2(33分)：5个数据集的实测AUC全部落入论文锚值的合理容差区间，且难度排序与论文完全一致，完美复现了核心科学论断。A3(15分)：方法严谨，代码明确区分train/val/test，归一化仅用train，早停仅用val，test仅评估一次，无数据泄漏风险，评估口径符合官方标准。

## B 证据真实性/实际复现（40/40）

证据等级为2（齐全自洽）。提交物包含完整的可运行代码、metrics.json、evidence_table.csv以及详细的class_counts和split_sizes校验文件。各文件间的实测数值严格一致，证据链完整且自洽，明确区分了论文锚值与实测值，无抄数嫌疑，授予满分40分。

## 证据与重算说明

独立重算未执行。关键实测数：BloodMNIST test AUC=0.9978, ACC=0.9640；RetinaMNIST test AUC=0.7011, ACC=0.4625。各数据集规模与冻结数据说明一致，所有实测数值在evidence_table.csv、metrics.json、report.md中完全对应。

## 结论

- **科学结论**: `supported`
- 亮点: 复现工作极其严谨，代码结构清晰，防泄漏设计完善，证据文件详实且内部数值严格一致，难度排序完美复现。
- 不足: 单一种子运行未提供方差估计，RetinaMNIST的ACC与论文存在一定偏差（但在AUC容差内且已做合理解释）。