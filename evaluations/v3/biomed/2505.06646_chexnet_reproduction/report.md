# EVAL REPORT v3: 2505.06646_chexnet_reproduction

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v3（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 68.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 30.0 | 60 | 逐项核对：A1复现AUC 0.6495与锚值0.79相对差17.8%，落入≤25%半满带得10分；A2增强AUC 0.6558与锚值0.85相对差22.8%，落入≤25%半满带得10分；A3复现F1 0.0507（绝对差0.029）与增强F1 0.2155（绝对差0.1745），综合落入±0.25半满带得10分。A维度共30分。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘扫描显示metrics.json与evidence_table.csv均存在，且包含多份训练日志与checkpoint meta文件。抽查enhanced mean_auc(0.6558)与Pneumonia F1(0.1227)等关键数值，在报告、evidence_table与metrics.json中严格一致，证据链完整，属于最高档[30,40]，给38分。 |

## A 核心结果达成度（30.0/60）

逐项核对：A1复现AUC 0.6495与锚值0.79相对差17.8%，落入≤25%半满带得10分；A2增强AUC 0.6558与锚值0.85相对差22.8%，落入≤25%半满带得10分；A3复现F1 0.0507（绝对差0.029）与增强F1 0.2155（绝对差0.1745），综合落入±0.25半满带得10分。A维度共30分。

## B 证据真实性/实际复现（38.0/40）

磁盘扫描显示metrics.json与evidence_table.csv均存在，且包含多份训练日志与checkpoint meta文件。抽查enhanced mean_auc(0.6558)与Pneumonia F1(0.1227)等关键数值，在报告、evidence_table与metrics.json中严格一致，证据链完整，属于最高档[30,40]，给38分。

## 证据与重算说明

独立重算未执行。关键实测数：evidence_table中enhanced mean_auc=0.6558，repro mean_f1=0.0507；metrics.json中Pneumonia enhanced F1=0.1227。各文件间数值完全一致，证据等级为2。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 实验设计严谨，防泄漏措施到位，采用多随机种子与快照集成有效降低了小样本方差，证据文件极其详实且内部高度自洽。
- 不足: 受限于冻结子集极小的规模，增强版AUC未能体现出相对复现版的明显提升，绝对指标与全量数据论文锚点仍有一定差距。