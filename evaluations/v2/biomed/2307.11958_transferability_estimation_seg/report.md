# EVAL REPORT v2: 2307.11958_transferability_estimation_seg

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 78.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 40.0 | 60 | A1: agent 报告 CC-FV Pearson=0.3827, τ=0.4000。根据 rubric 'Pearson ≥0.5 或 τ ≥0.3 → 满分'，τ=0.4 满足 ≥0.3 条件，落入满分带，且 metrics.json 有落盘证据，得 20 分。A2: agent 报告 CC-FV Pearson=0.3827，优于基线 LogME(0.2728)、LEEP(0.2042)、GBC(0.1707)，满足'优于至少一个基线'的满分条件，得 20 分。A3: agent 明确报告 top-1 未命中（选出 l08_s1，实际最优 l16_short），不满足命中条件，得 0 分。A 总分 40。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘扫描显示 metrics.json 与 evidence_table.csv 均存在，且包含完整的实测数据。抽查 metrics.json 中 CC-FV Pearson=0.3827、evidence_table.csv 中 liver_l16_short ft_dice=0.85857，与 report.md 和 claim.md 中的散文描述严格一致。未发现抄袭论文锚值现象（锚值在 paper_anchor 字段独立存放）。证据真实可靠，落入 [30,40] 区间，得 38 分。 |

## A 核心结果达成度（40.0/60）

A1: agent 报告 CC-FV Pearson=0.3827, τ=0.4000。根据 rubric 'Pearson ≥0.5 或 τ ≥0.3 → 满分'，τ=0.4 满足 ≥0.3 条件，落入满分带，且 metrics.json 有落盘证据，得 20 分。A2: agent 报告 CC-FV Pearson=0.3827，优于基线 LogME(0.2728)、LEEP(0.2042)、GBC(0.1707)，满足'优于至少一个基线'的满分条件，得 20 分。A3: agent 明确报告 top-1 未命中（选出 l08_s1，实际最优 l16_short），不满足命中条件，得 0 分。A 总分 40。

## B 证据真实性/实际复现（38.0/40）

磁盘扫描显示 metrics.json 与 evidence_table.csv 均存在，且包含完整的实测数据。抽查 metrics.json 中 CC-FV Pearson=0.3827、evidence_table.csv 中 liver_l16_short ft_dice=0.85857，与 report.md 和 claim.md 中的散文描述严格一致。未发现抄袭论文锚值现象（锚值在 paper_anchor 字段独立存放）。证据真实可靠，落入 [30,40] 区间，得 38 分。

## 证据与重算说明

独立重算未执行。关键实测数：CC-FV Pearson=0.3827，τ=0.4000（metrics.json）；liver_l16_short ft_dice=0.85857（evidence_table.csv）。数据截断问题有 data_check.json 详细审计记录，证据链完整。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 诚实且详尽地记录了冻结数据的 gzip 截断缺陷，TE 方法的 source-free 伪标签实现逻辑严密，基线对比完整且证据链高度一致。
- 不足: 受限于数据缺陷导致源池退化，top-1 选择未命中，且相关系数绝对值未能复现论文锚值的量级。