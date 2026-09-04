# EVAL REPORT v5: 2307.11958_transferability_estimation_seg

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 69.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **41.0** | 60 | A1交付实质完整，包含代码、结果表和报告等核心产物，得12分；A2科学结论保真方面，实测CC-FV Pearson=0.3827，虽优于部分基线但绝对数值偏离论文锚值较大且Top-1未命中，定性上部分支持，受partially_supported硬上限约束得14分；A3方法严谨，诚实处理数据截断缺陷并实现source-free评估，协议防泄漏，得15分。 |
| B 证据真实性/实际复现 | 28.0 | 40 | 磁盘证据齐全自洽（tier 2），metrics.json与evidence_table.csv等文件完整且内部一致，包含详尽的数据审计记录。受partially_supported结论硬上限约束，B维度最高给28分。 |

## A 核心结果达成度（41.0/60 = A1 12.0 + A2 14.0 + A3 15.0）

A1交付实质完整，包含代码、结果表和报告等核心产物，得12分；A2科学结论保真方面，实测CC-FV Pearson=0.3827，虽优于部分基线但绝对数值偏离论文锚值较大且Top-1未命中，定性上部分支持，受partially_supported硬上限约束得14分；A3方法严谨，诚实处理数据截断缺陷并实现source-free评估，协议防泄漏，得15分。

## B 证据真实性/实际复现（28.0/40）

磁盘证据齐全自洽（tier 2），metrics.json与evidence_table.csv等文件完整且内部一致，包含详尽的数据审计记录。受partially_supported结论硬上限约束，B维度最高给28分。

## 证据与重算说明

独立重算未执行。关键实测数：CC-FV Pearson=0.3827、τ=0.4000（metrics.json）；liver_l16_short ft_dice=0.85857（evidence_table.csv）。数据截断问题有data_check.json详细审计记录，证据链完整。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 诚实且详尽地记录了冻结数据的gzip截断缺陷，TE方法的source-free伪标签实现逻辑严密，基线对比完整且证据链高度一致。
- 不足: 受限于数据缺陷导致源池退化，top-1选择未命中，且相关系数绝对值未能复现论文锚值的量级。