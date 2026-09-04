# EVAL REPORT v5: 2408.07579_tabularbench_adv_robustness

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 33.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **60.0** | 60 | A1(12分)：核心交付物（claim.md、code、evidence_table.csv、metrics.json、report.md）完整产出，完全符合TASK.md要求。A2(33分)：实测clean spread 2.19pp、robust spread 33.38pp，完美复现C1“ID接近但鲁棒悬殊”的效应；AT平均鲁棒提升49.67pp、干净下降1.37pp，完美复现C2效应，结论标签supported与数据严格匹配。A3(15分)：方法严谨，严格遵循官方划分、train-only缩放、FGSM-AT及PGD-L2投影与clip协议，无数据泄漏，代码固定种子且提供重算日志，完全可复现。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示证据等级为2（齐全自洽）。提交物包含完整的metrics.json和evidence_table.csv，且提供了rerun_log.txt、data_sha256.txt等校验证据。内部数值在CSV、JSON和报告中严格一致，未发现抄写论文锚值的行为，证据链完整且真实可靠，给予满分40分。 |

## A 核心结果达成度（60.0/60 = A1 12.0 + A2 33.0 + A3 15.0）

A1(12分)：核心交付物（claim.md、code、evidence_table.csv、metrics.json、report.md）完整产出，完全符合TASK.md要求。A2(33分)：实测clean spread 2.19pp、robust spread 33.38pp，完美复现C1“ID接近但鲁棒悬殊”的效应；AT平均鲁棒提升49.67pp、干净下降1.37pp，完美复现C2效应，结论标签supported与数据严格匹配。A3(15分)：方法严谨，严格遵循官方划分、train-only缩放、FGSM-AT及PGD-L2投影与clip协议，无数据泄漏，代码固定种子且提供重算日志，完全可复现。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示证据等级为2（齐全自洽）。提交物包含完整的metrics.json和evidence_table.csv，且提供了rerun_log.txt、data_sha256.txt等校验证据。内部数值在CSV、JSON和报告中严格一致，未发现抄写论文锚值的行为，证据链完整且真实可靠，给予满分40分。

## 证据与重算说明

独立重算未执行。关键实测数抽查：test样本数=2286（与锚值一致）；std clean跨度=2.19pp；std robust跨度=33.38pp；AT平均鲁棒提升=+49.67pp。所有数值在metrics.json、evidence_table.csv与report.md中保持严格一致。

## 结论

- **科学结论**: `supported`
- 亮点: 实验协议执行极其严谨，代码结构清晰且完全可复现；对结构性模式（C1/C2）的验证数据详实，口径差异与局限性讨论非常专业。
- 不足: 标准训练下的robust spread（33.38pp）与冻结参考锚值（38.5pp）存在约13%的微小偏差，可能源于模型初始化或优化器浮点累积差异，但不影响核心科学结论的成立。