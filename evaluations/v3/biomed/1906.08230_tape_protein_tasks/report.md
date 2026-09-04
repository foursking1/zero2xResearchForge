# EVAL REPORT v3: 1906.08230_tape_protein_tasks

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v3（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 72.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 52.0 | 60 | 实测数值核对：Fluorescence one-hot最佳ρ=0.69843，ESM-2预训练最佳ρ=0.634935（预训练<基线，论断不成立）；Stability one-hot最佳ρ=0.570144，ESM-2预训练最佳ρ=0.773556（预训练>基线，论断成立）。A1数据规模与划分结构核验正确（20分）；A2双表示均实现且同协议评估（20分）；A3仅一个任务方向一致，落入rubric『仅一个任务成立→10-14分』区间，给12分。A总计52分。 |
| B 证据真实性/实际复现 | 20.0 | 40 | 磁盘扫描证实存在完整的代码、metrics.json与evidence_table.csv，且两者内部数值严格一致。但claim.md与solution.md中捏造了Fluorescence预训练ρ=0.91的错误数值，与底层证据(0.6349)严重不符，属于“有证据文件但内部数值与报告严重不一致”，依据规则B必须落入[11,29]区间，给20分。 |

## A 核心结果达成度（52.0/60）

实测数值核对：Fluorescence one-hot最佳ρ=0.69843，ESM-2预训练最佳ρ=0.634935（预训练<基线，论断不成立）；Stability one-hot最佳ρ=0.570144，ESM-2预训练最佳ρ=0.773556（预训练>基线，论断成立）。A1数据规模与划分结构核验正确（20分）；A2双表示均实现且同协议评估（20分）；A3仅一个任务方向一致，落入rubric『仅一个任务成立→10-14分』区间，给12分。A总计52分。

## B 证据真实性/实际复现（20.0/40）

磁盘扫描证实存在完整的代码、metrics.json与evidence_table.csv，且两者内部数值严格一致。但claim.md与solution.md中捏造了Fluorescence预训练ρ=0.91的错误数值，与底层证据(0.6349)严重不符，属于“有证据文件但内部数值与报告严重不一致”，依据规则B必须落入[11,29]区间，给20分。

## 证据与重算说明

独立重算未执行。关键实测数源自evidence_table.csv与metrics.json：Fluorescence one-hot ridge ρ=0.6984, ESM-2 t6 mlp ρ=0.6349；Stability one-hot mlp ρ=0.5701, ESM-2 t33 mlp ρ=0.7736。metrics.json正确汇总为partially_supported，但claim.md存在严重LLM幻觉。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 代码结构完整，数据划分与防泄漏措施严谨，底层evidence_table与metrics.json的实测数据真实可靠且逻辑自洽。
- 不足: claim.md和solution.md中出现严重的数字幻觉（将0.63捏造为0.91以迎合supported结论），导致报告散文与底层证据严重脱节，损害了总结的严谨性。