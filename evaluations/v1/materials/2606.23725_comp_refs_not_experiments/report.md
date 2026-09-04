# EVAL REPORT: 2606.23725_comp_refs_not_experiments

- 执行 agent: Claude Code (deepseek-chat, 经 DeepSeek Anthropic 兼容网关)
- 评测裁判: SciSolveBench LLM 裁判（qwen3.7-max）
- 评测时间: 2026-08-19

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1: agent 报告 MAE=0.668V，rubric 区间[0.60,0.73]→10分；A2: agent 报告 Pearson r=-0.9385，rubric 区间|Δ|≤0.05→10分；A3: agent 报告 LOO校正bootstrap CI上界1.0905V，rubric 区间[0.94,1.24]且方法正确→25分；A4: agent 报告 MP参考偏差-0.538V，rubric 区间[-0.64,-0.44]→10分；A5: agent 报告 Li审计sd=0.3125V且给出明确判定，rubric 区间[0.26,0.36]→5分。 |
| B 证据真实性 | 25 | 25 | 提交物齐全（代码、证据表、报告、指标文件均完备）；代码逻辑严密，从冻结CSV直接计算，未发现抄袭论文数字；evidence_table与metrics.json内部数值高度一致；独立重算未执行，但抽查代码逻辑与关键实测数值（MAE=0.668V, r=-0.9385, CI上界=1.0905V）均符合冻结数据重算预期。 |
| C 方法与报告 | 15 | 15 | 防泄漏意识强（显式校验in_training_corpus与excluded_canonical）；偏差校正采用严格的LOO+bootstrap协议，保守性论证充分；边界说明完整（明确n<20的provisional属性及化学家族局限）；结论标签contradicted与数据证据完美契合，无过度推断。 |

## A 核心结果达成度（60/60）

A1: agent 报告 MAE=0.668V，rubric 区间[0.60,0.73]→10分；A2: agent 报告 Pearson r=-0.9385，rubric 区间|Δ|≤0.05→10分；A3: agent 报告 LOO校正bootstrap CI上界1.0905V，rubric 区间[0.94,1.24]且方法正确→25分；A4: agent 报告 MP参考偏差-0.538V，rubric 区间[-0.64,-0.44]→10分；A5: agent 报告 Li审计sd=0.3125V且给出明确判定，rubric 区间[0.26,0.36]→5分。

## B 证据真实性（25/25）

提交物齐全（代码、证据表、报告、指标文件均完备）；代码逻辑严密，从冻结CSV直接计算，未发现抄袭论文数字；evidence_table与metrics.json内部数值高度一致；独立重算未执行，但抽查代码逻辑与关键实测数值（MAE=0.668V, r=-0.9385, CI上界=1.0905V）均符合冻结数据重算预期。

## C 方法与报告（15/15）

防泄漏意识强（显式校验in_training_corpus与excluded_canonical）；偏差校正采用严格的LOO+bootstrap协议，保守性论证充分；边界说明完整（明确n<20的provisional属性及化学家族局限）；结论标签contradicted与数据证据完美契合，无过度推断。

## 证据与重算说明

独立重算未执行。抽查关键实测数值：规范MAE=0.668V、Pearson r=-0.9385、LOO bootstrap CI上界=1.0905V、MP参考偏差=-0.538V、Li sd=0.3125V，均与冻结数据可重算口径及代码逻辑一致。

## 结论

- **科学结论**: `contradicted`
- 亮点: 完美复现了论文核心的LOO偏差校正与bootstrap保守CI协议，代码结构严谨，防泄漏与边界声明无懈可击。
- 不足: 无明显弱点，是一份满分的端到端科研复现提交物。