# EVAL REPORT v2: 2408.07579_tabularbench_adv_robustness

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1维度：agent报告标准训练clean跨度为2.19pp，robust跨度为33.38pp。对照rubric，clean spread 2.19 ≤ 5pp 且 robust spread 33.38 ≥ 15pp，落入满分带，得30分。A2维度：agent报告平均鲁棒提升为+49.67pp，平均干净下降为1.37pp。对照rubric，平均鲁棒提升 49.67 ≥ 20pp 且 平均干净下降 1.37 ≤ 5pp，落入满分带，得30分。所有数值均有metrics.json和evidence_table.csv落盘证据支撑。A维度总计60分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示metrics.json与evidence_table.csv均存在且列完整。evidence_table中的逐模型精度数值与metrics.json及报告中的汇总数值严格一致（如mlp64 std clean_acc=0.9190726），未发现抄写论文锚值的行为。代码逻辑完整，包含要求的L2投影与clip操作，证据真实可靠，给予满分40分。 |

## A 核心结果达成度（60/60）

A1维度：agent报告标准训练clean跨度为2.19pp，robust跨度为33.38pp。对照rubric，clean spread 2.19 ≤ 5pp 且 robust spread 33.38 ≥ 15pp，落入满分带，得30分。A2维度：agent报告平均鲁棒提升为+49.67pp，平均干净下降为1.37pp。对照rubric，平均鲁棒提升 49.67 ≥ 20pp 且 平均干净下降 1.37 ≤ 5pp，落入满分带，得30分。所有数值均有metrics.json和evidence_table.csv落盘证据支撑。A维度总计60分。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示metrics.json与evidence_table.csv均存在且列完整。evidence_table中的逐模型精度数值与metrics.json及报告中的汇总数值严格一致（如mlp64 std clean_acc=0.9190726），未发现抄写论文锚值的行为。代码逻辑完整，包含要求的L2投影与clip操作，证据真实可靠，给予满分40分。

## 证据与重算说明

独立重算未执行。关键实测数抽查：test样本数=2286（与锚值及代码逻辑一致）；std clean跨度=2.19pp；std robust跨度=33.38pp；AT平均鲁棒提升=+49.67pp。所有数值在metrics.json、evidence_table.csv与report.md中保持严格一致，证据链完整。

## 结论

- **科学结论**: `supported`
- 亮点: 实验协议执行极其严谨，代码结构清晰且完全可复现；对结构性模式（C1/C2）的验证数据详实，口径差异与局限性讨论非常专业。
- 不足: 无明显弱点，是一份高质量的L1级别科研复现提交物。