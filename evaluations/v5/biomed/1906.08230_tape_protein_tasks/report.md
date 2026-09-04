# EVAL REPORT v5: 1906.08230_tape_protein_tasks

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 64.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 12.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **39.0** | 60 | A1(12分)：核心交付物（代码、evidence_table、metrics.json、dataset_stats等）完整产出，符合任务明确要求。A2(12分)：真实证据表明Stability任务复现了预训练优于one-hot的效应（0.77 vs 0.57），但Fluorescence任务未能复现（0.63 vs 0.69，one-hot反而更好），属于部分不支持；受partially_supported结论硬上限约束（A2≤15），给12分。A3(15分)：方法sound，正确划分train/valid/test，使用验证集早停和超参选择，无数据泄漏，结果可由提交代码复算。 |
| B 证据真实性/实际复现 | 25.0 | 40 | 磁盘扫描证实metrics.json与evidence_table.csv存在且内部数值自洽（证据等级2）。但claim.md和solution.md中存在严重的数字幻觉（捏造Fluorescence预训练ρ=0.91），导致报告散文与底层证据严重脱节。受partially_supported结论硬上限约束（B≤28），给25分。 |

## A 核心结果达成度（39.0/60 = A1 12.0 + A2 12.0 + A3 15.0）

A1(12分)：核心交付物（代码、evidence_table、metrics.json、dataset_stats等）完整产出，符合任务明确要求。A2(12分)：真实证据表明Stability任务复现了预训练优于one-hot的效应（0.77 vs 0.57），但Fluorescence任务未能复现（0.63 vs 0.69，one-hot反而更好），属于部分不支持；受partially_supported结论硬上限约束（A2≤15），给12分。A3(15分)：方法sound，正确划分train/valid/test，使用验证集早停和超参选择，无数据泄漏，结果可由提交代码复算。

## B 证据真实性/实际复现（25.0/40）

磁盘扫描证实metrics.json与evidence_table.csv存在且内部数值自洽（证据等级2）。但claim.md和solution.md中存在严重的数字幻觉（捏造Fluorescence预训练ρ=0.91），导致报告散文与底层证据严重脱节。受partially_supported结论硬上限约束（B≤28），给25分。

## 证据与重算说明

独立重算未执行。关键实测数源自evidence_table.csv与metrics.json：Fluorescence one-hot最佳ρ=0.698，ESM-2预训练最佳ρ=0.635（论断不成立）；Stability one-hot最佳ρ=0.570，ESM-2预训练最佳ρ=0.774（论断成立）。metrics.json正确判定为partially_supported，但claim.md捏造了0.91的错误数值。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 代码结构完整，防泄漏与早停机制严谨，底层evidence_table与metrics.json数据真实可靠且逻辑自洽。
- 不足: claim.md和solution.md出现严重的LLM幻觉，捏造了Fluorescence任务的虚假高分以迎合supported结论，导致报告总结与底层证据严重脱节。