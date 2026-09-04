# EVAL REPORT v7: 2410.06922_exoplanet_mass_incomplete

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 63.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **41.0** | 60 | A1(12)：核心交付物完整，包含机器可读的 metrics.json、evidence_table.csv 及可运行代码，符合任务要求。A2(14)：结论为 partially_supported，受硬上限约束(≤15)。Agent 准确识别了完整子集排名模式保持，但全档案排名反转及8属性扩展方向相反，未强行拟合论文，科学态度严谨。A3(15)：方法严谨，防泄漏措施（距离计算排除质量维）明确，鲁棒性分析（batch-LOO vs 严格LOO、温度敏感性）深入且 sound。 |
| B 真值一致性/可验证性 | 22.0 | 40 | truth_check=diverged | truth_check=diverged。agent数 vs 锚点真值逐条比对：1. complete kNN×KDE: agent 0.914 vs 锚点 0.886 → 偏离；2. complete GAIN: agent 1.988 vs 锚点 1.253 → 偏离；3. full kNN×KDE: agent 1.347 vs 锚点 1.510 → 偏离；4. full MissForest: agent 1.191 vs 锚点 1.701 → 偏离，且导致全档案最优排名反转（MF优于kNN×KDE）；5. extended 8属性方向: agent 1.404(vs 1.347)为损伤，锚点 1.502(vs 1.510)为提升 → 方向偏离。因快照差异导致绝对值与部分结构结论 diverged，按规则 B 给 22。 |

## A 核心结果达成度（41.0/60 = A1 12.0 + A2 14.0 + A3 15.0）

A1(12)：核心交付物完整，包含机器可读的 metrics.json、evidence_table.csv 及可运行代码，符合任务要求。A2(14)：结论为 partially_supported，受硬上限约束(≤15)。Agent 准确识别了完整子集排名模式保持，但全档案排名反转及8属性扩展方向相反，未强行拟合论文，科学态度严谨。A3(15)：方法严谨，防泄漏措施（距离计算排除质量维）明确，鲁棒性分析（batch-LOO vs 严格LOO、温度敏感性）深入且 sound。

## B 真值一致性/可验证性（22.0/40）[truth_check=diverged]

truth_check=diverged。agent数 vs 锚点真值逐条比对：1. complete kNN×KDE: agent 0.914 vs 锚点 0.886 → 偏离；2. complete GAIN: agent 1.988 vs 锚点 1.253 → 偏离；3. full kNN×KDE: agent 1.347 vs 锚点 1.510 → 偏离；4. full MissForest: agent 1.191 vs 锚点 1.701 → 偏离，且导致全档案最优排名反转（MF优于kNN×KDE）；5. extended 8属性方向: agent 1.404(vs 1.347)为损伤，锚点 1.502(vs 1.510)为提升 → 方向偏离。因快照差异导致绝对值与部分结构结论 diverged，按规则 B 给 22。

## 证据与重算说明

独立重算未执行。关键实测数核对：evidence_table.csv 中 complete kNN×KDE eps=0.9139，full GAIN eps=4.5402，extended kNN×KDE eps=1.4036，与 report.md 及 metrics.json 完全一致，证据内部高度自洽且无抄袭论文数字嫌疑。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 诚实且深入地分析了快照差异导致的排名反转与方向不一致，未强行拟合论文结论；证据文件齐全，数值高度自洽，透明度极高。
- 不足: 全档案中 kNN×KDE 未能复现最优排名（被 MissForest 超越），且 8 属性扩展方向与论文相反，导致核心结论仅为部分支持，与论文真值存在结构性偏离。