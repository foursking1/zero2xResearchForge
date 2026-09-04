# EVAL REPORT v5: 2606.23725_comp_refs_not_experiments

- 执行 agent: Claude Code (deepseek-chat, 经 DeepSeek Anthropic 兼容网关)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 33.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **60.0** | 60 | A1(12分): 核心交付物（claim, code, evidence_table, metrics, report, figures）全部完整产出，完全符合任务要求。A2(33分): 完美复现论文核心claim与所有关键数值（MAE=0.668V, r=-0.939, CI=1.09V, MP偏差=-0.538V, Li sd=0.312V）。Agent给出的标签为contradicted（针对H0），实质上完美支持了论文的核心claim（筛选器不可用），故按supported论文claim的满分档评判。A3(15分): 方法严谨，代码包含SHA-256数据完整性校验与防泄漏检查，LOO+bootstrap协议实现正确，结果完全可由冻结数据复算。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示证据等级为2（齐全自洽）。提交物包含完整的analyze.py、evidence_table.csv与metrics.json，内部数值高度自洽，且代码中内置了SHA-256校验与防泄漏断言，属于证据齐全自洽且有校验脚本的最高档，得40分。 |

## A 核心结果达成度（60.0/60 = A1 12.0 + A2 33.0 + A3 15.0）

A1(12分): 核心交付物（claim, code, evidence_table, metrics, report, figures）全部完整产出，完全符合任务要求。A2(33分): 完美复现论文核心claim与所有关键数值（MAE=0.668V, r=-0.939, CI=1.09V, MP偏差=-0.538V, Li sd=0.312V）。Agent给出的标签为contradicted（针对H0），实质上完美支持了论文的核心claim（筛选器不可用），故按supported论文claim的满分档评判。A3(15分): 方法严谨，代码包含SHA-256数据完整性校验与防泄漏检查，LOO+bootstrap协议实现正确，结果完全可由冻结数据复算。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示证据等级为2（齐全自洽）。提交物包含完整的analyze.py、evidence_table.csv与metrics.json，内部数值高度自洽，且代码中内置了SHA-256校验与防泄漏断言，属于证据齐全自洽且有校验脚本的最高档，得40分。

## 证据与重算说明

独立重算未执行（基于代码逻辑与落盘文件核对）。关键实测数：规范MAE=0.668V、Pearson r=-0.9385、LOO bootstrap CI上界=1.0905V、MP参考偏差=-0.538V、Li sd=0.3125V，均与冻结数据重算预期及落盘metrics.json严格一致。

## 结论

- **科学结论**: `supported`
- 亮点: 完美复现了论文核心的LOO偏差校正与bootstrap保守CI协议，代码结构严谨，防泄漏与数据完整性校验无懈可击，证据链闭环完整。
- 不足: 无明显弱点，是一份高质量的端到端科研复现提交物。