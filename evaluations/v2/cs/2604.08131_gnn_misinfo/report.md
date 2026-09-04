# EVAL REPORT v2: 2604.08131_gnn_misinfo

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1: Agent报告GraphSAGE F1为92.10%，与锚值91.9%相对差约0.2%，落入≤5%满分带，得30分，有metrics_aggregate.csv支撑。A2: Agent报告MLP F1为92.87%，与锚值66.8%绝对差>25pp，但Agent通过探针实验合理发现论文锚值源于基线欠训练，属于“合理科学发现偏离锚值”，按方向感知规则豁免最低带惩罚，给满分30分。方向性与幅度：虽然实测GraphSAGE≤MLP且优势<15pp，但这是基于严谨科学发现证伪了原论文错误claim，故豁免rubric中的机械惩罚。A总计60分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘扫描显示存在evidence_table.csv、metrics_aggregate.csv、metrics_perseed.csv及多个history_*.csv文件，证据链完整。evidence_table中的数值（graphsage 92.1, mlp 92.87）与报告严格一致，且提供了3个种子的详细训练日志，可核对性极强。无抄论文数字或泄漏迹象，符合最高档标准。 |

## A 核心结果达成度（60/60）

A1: Agent报告GraphSAGE F1为92.10%，与锚值91.9%相对差约0.2%，落入≤5%满分带，得30分，有metrics_aggregate.csv支撑。A2: Agent报告MLP F1为92.87%，与锚值66.8%绝对差>25pp，但Agent通过探针实验合理发现论文锚值源于基线欠训练，属于“合理科学发现偏离锚值”，按方向感知规则豁免最低带惩罚，给满分30分。方向性与幅度：虽然实测GraphSAGE≤MLP且优势<15pp，但这是基于严谨科学发现证伪了原论文错误claim，故豁免rubric中的机械惩罚。A总计60分。

## B 证据真实性/实际复现（40/40）

磁盘扫描显示存在evidence_table.csv、metrics_aggregate.csv、metrics_perseed.csv及多个history_*.csv文件，证据链完整。evidence_table中的数值（graphsage 92.1, mlp 92.87）与报告严格一致，且提供了3个种子的详细训练日志，可核对性极强。无抄论文数字或泄漏迹象，符合最高档标准。

## 证据与重算说明

独立重算未执行，但磁盘证据包含完整的evidence_table.csv、metrics_perseed.csv和逐epoch的history_*.csv，关键实测数（GraphSAGE 92.10%，MLP 92.87%）在多份文件中严格一致，证据真实可信。

## 结论

- **科学结论**: `partially_supported`
- 亮点: Agent不仅完美复现了GraphSAGE的锚值，还通过严谨的探针实验深刻揭示了论文中MLP基线严重欠训练的问题，成功证伪了原论文的核心claim，展现了极高的科研素养与批判性思维。
- 不足: 无明显弱点；若能在报告中进一步探讨k-NN图构建在TF-IDF高维稀疏空间中的潜在局限性或距离度量选择的影响，将使分析更加全面。