# EVAL REPORT: 2408.07579_tabularbench_adv_robustness

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判（qwen3.7-max）
- 评测时间: 2026-08-19

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1维度：agent报告标准训练clean跨度为2.19pp，robust跨度为33.38pp。对照rubric，clean spread 2.19 ≤ 5pp 且 robust spread 33.38 ≥ 15pp，唯一落入满分带，得30分。A2维度：agent报告平均鲁棒提升为+49.67pp，平均干净下降为1.37pp。对照rubric，平均鲁棒提升 49.67 ≥ 20pp 且 平均干净下降 1.37 ≤ 5pp，唯一落入满分带，得30分。A维度总计60分。 |
| B 证据真实性 | 25 | 25 | 提交物齐全（包含claim.md、code、evidence_table.csv、metrics.json、report.md）。代码逻辑清晰，划分、缩放、训练与攻击实现均与TASK.md协议严格对齐。evidence_table与metrics.json及报告中的数值高度一致，未发现将论文数值当作实测结果的抄数行为。test样本数报告为2286，与锚值及代码逻辑（11430*0.2）完全吻合。 |
| C 方法与报告 | 15 | 15 | C1方法合理性（5/5）：严格遵循官方DefaultSplitter、train-only min-max缩放、4个MLP架构、FGSM-AT及PGD-L2攻击协议，包含L2球投影与[0,1]clip，种子固定。C2口径与偏差讨论（6/6）：清晰说明了PGD-L2 ε=0.25与论文CAA ε=0.5的口径差异，并深入分析了容量-鲁棒性反相关及AT抹平架构差异的现象。C3结论与边界（4/4）：四档标签'supported'与实测数据完美匹配，局限性分析客观全面。 |

## A 核心结果达成度（60/60）

A1维度：agent报告标准训练clean跨度为2.19pp，robust跨度为33.38pp。对照rubric，clean spread 2.19 ≤ 5pp 且 robust spread 33.38 ≥ 15pp，唯一落入满分带，得30分。A2维度：agent报告平均鲁棒提升为+49.67pp，平均干净下降为1.37pp。对照rubric，平均鲁棒提升 49.67 ≥ 20pp 且 平均干净下降 1.37 ≤ 5pp，唯一落入满分带，得30分。A维度总计60分。

## B 证据真实性（25/25）

提交物齐全（包含claim.md、code、evidence_table.csv、metrics.json、report.md）。代码逻辑清晰，划分、缩放、训练与攻击实现均与TASK.md协议严格对齐。evidence_table与metrics.json及报告中的数值高度一致，未发现将论文数值当作实测结果的抄数行为。test样本数报告为2286，与锚值及代码逻辑（11430*0.2）完全吻合。

## C 方法与报告（15/15）

C1方法合理性（5/5）：严格遵循官方DefaultSplitter、train-only min-max缩放、4个MLP架构、FGSM-AT及PGD-L2攻击协议，包含L2球投影与[0,1]clip，种子固定。C2口径与偏差讨论（6/6）：清晰说明了PGD-L2 ε=0.25与论文CAA ε=0.5的口径差异，并深入分析了容量-鲁棒性反相关及AT抹平架构差异的现象。C3结论与边界（4/4）：四档标签'supported'与实测数据完美匹配，局限性分析客观全面。

## 证据与重算说明

独立重算未执行。关键实测数值抽查：test样本数=2286（与锚值一致）；std clean跨度=2.19pp；std robust跨度=33.38pp；AT平均鲁棒提升=+49.67pp；AT平均干净下降=1.37pp。所有数值在metrics.json、evidence_table.csv与report.md中保持严格一致。

## 结论

- **科学结论**: `supported`
- 亮点: 实验协议执行极其严谨，代码结构清晰且完全可复现；对结构性模式（C1/C2）的验证数据详实，口径差异与局限性讨论非常专业。
- 不足: 无明显弱点，是一份高质量的L1级别科研复现提交物。