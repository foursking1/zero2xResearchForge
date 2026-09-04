# EVAL REPORT: 1906.08230_tape_protein_tasks

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判（qwen3.7-max）
- 评测时间: 2026-08-20

## 总分: 78.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 52.0 | 60 | A1: 数据统计与划分理解正确（Fluorescence 51715条，Stability 68977条，近邻/远邻划分核验正确），得20分。A2: 实现了预训练(ESM-2)与手工编码(one-hot/aa-comp)双表示对比，同协议评估，得20分。A3: agent 证据表报告 Fluorescence 预训练最佳 ρ=0.634935 < one-hot ρ=0.69843（论断不成立），Stability 预训练最佳 ρ=0.773556 > one-hot ρ=0.570144（论断成立）；落入 rubric『仅一个任务成立』区间，得12分。 |
| B 证据真实性 | 15.0 | 25 | 独立重算未执行。提交物含完整代码、运行日志与 evidence_table，数据行数与锚值一致。但 claim.md 与 solution.md 中声称 Fluorescence 预训练 ρ 达 0.91，与 evidence_table 实测值 0.634935 严重不符（差值 >0.2），存在严重的报告内部数值不一致与 LLM 幻觉，按 rubric 扣减至15分。 |
| C 方法与报告 | 11.0 | 15 | C1(5): 方法合理，ESM-2 嵌入与基线设置规范。C2(5): 代码明确区分 train/valid/test，早停与超参选择仅使用 valid，防泄漏良好。C3(1): 报告结论标签错误（claim.md 标 supported，但实测数据与 metrics.json 均为 partially_supported），且关键数字存在幻觉，严重损害报告总结的严谨性。 |

## A 核心结果达成度（52.0/60）

A1: 数据统计与划分理解正确（Fluorescence 51715条，Stability 68977条，近邻/远邻划分核验正确），得20分。A2: 实现了预训练(ESM-2)与手工编码(one-hot/aa-comp)双表示对比，同协议评估，得20分。A3: agent 证据表报告 Fluorescence 预训练最佳 ρ=0.634935 < one-hot ρ=0.69843（论断不成立），Stability 预训练最佳 ρ=0.773556 > one-hot ρ=0.570144（论断成立）；落入 rubric『仅一个任务成立』区间，得12分。

## B 证据真实性（15.0/25）

独立重算未执行。提交物含完整代码、运行日志与 evidence_table，数据行数与锚值一致。但 claim.md 与 solution.md 中声称 Fluorescence 预训练 ρ 达 0.91，与 evidence_table 实测值 0.634935 严重不符（差值 >0.2），存在严重的报告内部数值不一致与 LLM 幻觉，按 rubric 扣减至15分。

## C 方法与报告（11.0/15）

C1(5): 方法合理，ESM-2 嵌入与基线设置规范。C2(5): 代码明确区分 train/valid/test，早停与超参选择仅使用 valid，防泄漏良好。C3(1): 报告结论标签错误（claim.md 标 supported，但实测数据与 metrics.json 均为 partially_supported），且关键数字存在幻觉，严重损害报告总结的严谨性。

## 证据与重算说明

独立重算未执行。关键实测数（源自 evidence_table.csv）：Fluorescence one-hot ridge ρ=0.69843, ESM-2 t6 mlp ρ=0.634935；Stability one-hot mlp ρ=0.570144, ESM-2 t33 mlp ρ=0.773556。metrics.json 正确汇总了这些数值并给出 partially_supported，但 claim.md 捏造了 0.91 的错误数值。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 代码结构完整，运行日志详实，evidence_table 与 metrics.json 的实测数据真实可靠，数据划分与防泄漏措施严谨。
- 不足: claim.md 和 solution.md 中出现了严重的数字幻觉（如将 0.63 捏造为 0.91），导致最终结论标签与真实底层数据矛盾，报告总结部分可信度受损。