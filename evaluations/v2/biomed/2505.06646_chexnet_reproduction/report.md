# EVAL REPORT v2: 2505.06646_chexnet_reproduction

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 68.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 30.0 | 60 | A1：复现版平均 AUC 报告为 0.6495，与锚值 0.79 相对差约 17.8%，落入 ≤25% 区间，得 10 分；A2：增强版平均 AUC 报告为 0.6558，与锚值 0.85 相对差约 22.8%，落入 ≤25% 区间，得 10 分；A3：复现版 F1 为 0.0507（绝对差 0.029，满足 ±0.15 满分带），增强版 F1 为 0.2155（绝对差 0.1745，落入 ±0.25 半满带），综合按半满带给分，得 10 分。所有数值均有 metrics.json 和 evidence_table 落盘支撑。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘扫描显示 metrics.json 与 evidence_table.csv 均存在，且包含多份训练日志与 checkpoint meta 文件。抽查 enhanced mean_auc (0.6558) 与 Pneumonia F1 (0.1227) 等关键数值，在报告、evidence_table 与 metrics.json 中严格一致。证据链完整，无抄袭或泄漏，属于“有证据文件且数值与报告严格一致、可核对”的最高档。 |

## A 核心结果达成度（30.0/60）

A1：复现版平均 AUC 报告为 0.6495，与锚值 0.79 相对差约 17.8%，落入 ≤25% 区间，得 10 分；A2：增强版平均 AUC 报告为 0.6558，与锚值 0.85 相对差约 22.8%，落入 ≤25% 区间，得 10 分；A3：复现版 F1 为 0.0507（绝对差 0.029，满足 ±0.15 满分带），增强版 F1 为 0.2155（绝对差 0.1745，落入 ±0.25 半满带），综合按半满带给分，得 10 分。所有数值均有 metrics.json 和 evidence_table 落盘支撑。

## B 证据真实性/实际复现（38.0/40）

磁盘扫描显示 metrics.json 与 evidence_table.csv 均存在，且包含多份训练日志与 checkpoint meta 文件。抽查 enhanced mean_auc (0.6558) 与 Pneumonia F1 (0.1227) 等关键数值，在报告、evidence_table 与 metrics.json 中严格一致。证据链完整，无抄袭或泄漏，属于“有证据文件且数值与报告严格一致、可核对”的最高档。

## 证据与重算说明

独立重算未执行。关键实测数：evidence_table 中 enhanced mean_auc=0.6558，repro mean_f1=0.0507；metrics.json 中 Pneumonia enhanced F1=0.1227。各文件间数值完全一致，证据链完整。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 实验设计严谨，防泄漏措施到位，采用多随机种子与快照集成有效降低了小样本方差，对数据规模差异导致的数值偏移分析透彻，证据文件极其详实。
- 不足: 受限于冻结子集极小的规模，增强版 AUC 未能体现出相对复现版的明显提升，绝对指标与全量数据论文锚点仍有一定差距。