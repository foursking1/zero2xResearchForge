# EVAL REPORT v3: 2604.08131_gnn_misinfo

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 50.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 10.0 | 60 | A1(GraphSAGE)报告92.10%，与锚值91.9%偏差0.22%，落入≤5%满分带；A2(MLP)报告92.87%，与锚值66.8%绝对差26.07pp，落入>25pp带。方向性校验显示GraphSAGE(92.10%) < MLP(92.87%)，与论文GNN>MLP方向相反，触发Rubric硬规则A≤20及系统提示A≤15。因conclusion=contradicted总分硬上限50，在B=40情况下A给10分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示证据等级为2（齐全自洽）。提交了完整的evidence_table、metrics_aggregate、metrics_perseed及逐epoch训练历史，证据链完整且内部高度自洽，提供verify_evidence.py校验脚本，无抄袭或泄漏迹象，符合最高档标准。 |

## A 核心结果达成度（10.0/60）

A1(GraphSAGE)报告92.10%，与锚值91.9%偏差0.22%，落入≤5%满分带；A2(MLP)报告92.87%，与锚值66.8%绝对差26.07pp，落入>25pp带。方向性校验显示GraphSAGE(92.10%) < MLP(92.87%)，与论文GNN>MLP方向相反，触发Rubric硬规则A≤20及系统提示A≤15。因conclusion=contradicted总分硬上限50，在B=40情况下A给10分。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示证据等级为2（齐全自洽）。提交了完整的evidence_table、metrics_aggregate、metrics_perseed及逐epoch训练历史，证据链完整且内部高度自洽，提供verify_evidence.py校验脚本，无抄袭或泄漏迹象，符合最高档标准。

## 证据与重算说明

独立重算未执行。关键实测数：GraphSAGE F1=92.10% (evidence_table.csv), MLP F1=92.87% (evidence_table.csv), f1_gap_pp=-0.77。多份文件数值高度自洽，证据真实可信。

## 结论

- **科学结论**: `contradicted`
- 亮点: 完美复现了GraphSAGE锚值，并通过严密的探针实验和防泄漏设计揭示了原论文MLP基线严重欠训练的问题，科学证伪了原claim，展现了卓越的批判性思维。
- 不足: 受限于评分Rubric对方向相反的机械惩罚规则及conclusion=contradicted总分≤50的硬约束，尽管科学发现深刻，总分仍被强制截断。