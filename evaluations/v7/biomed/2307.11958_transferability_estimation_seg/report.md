# EVAL REPORT v7: 2307.11958_transferability_estimation_seg

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 59.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **41.0** | 60 | A1: 核心交付物完整，包含 metrics.json、evidence_table.csv、claim.md 等机器可读结果文件，得 12 分。A2: 结论为 partially_supported，CC-FV 在相对排序上优于部分基线，但绝对数值偏离论文真值较大，且 Top-1 选择未命中，受 partially_supported 硬上限（≤15）约束得 14 分。A3: 方法严谨，诚实记录并处理了冻结数据的 gzip 截断缺陷，实现了 source-free 伪标签评估且防泄漏，代码逻辑 sound 且可复现，得 15 分。 |
| B 真值一致性/可验证性 | 18.0 | 40 | truth_check=diverged | agent CC-FV Pearson 0.3827 vs 锚点 0.7003 → 严重偏离；agent CC-FV tau 0.4000 vs 锚点 0.4986 → 偏离；agent LogME Pearson 0.2728 vs 锚点 0.2082 → 偏离；agent GBC Pearson 0.1707 vs 锚点 0.3317 → 偏离。所有关键相关性指标均不在容差带内，且 Top-1 命中失败，truth_check 判定为 diverged。受 partially_supported 结论硬上限（B≤28）约束，给 18 分。 |

## A 核心结果达成度（41.0/60 = A1 12.0 + A2 14.0 + A3 15.0）

A1: 核心交付物完整，包含 metrics.json、evidence_table.csv、claim.md 等机器可读结果文件，得 12 分。A2: 结论为 partially_supported，CC-FV 在相对排序上优于部分基线，但绝对数值偏离论文真值较大，且 Top-1 选择未命中，受 partially_supported 硬上限（≤15）约束得 14 分。A3: 方法严谨，诚实记录并处理了冻结数据的 gzip 截断缺陷，实现了 source-free 伪标签评估且防泄漏，代码逻辑 sound 且可复现，得 15 分。

## B 真值一致性/可验证性（18.0/40）[truth_check=diverged]

agent CC-FV Pearson 0.3827 vs 锚点 0.7003 → 严重偏离；agent CC-FV tau 0.4000 vs 锚点 0.4986 → 偏离；agent LogME Pearson 0.2728 vs 锚点 0.2082 → 偏离；agent GBC Pearson 0.1707 vs 锚点 0.3317 → 偏离。所有关键相关性指标均不在容差带内，且 Top-1 命中失败，truth_check 判定为 diverged。受 partially_supported 结论硬上限（B≤28）约束，给 18 分。

## 证据与重算说明

独立重算未执行。关键实测数：CC-FV Pearson=0.3827、τ=0.4000（metrics.json）；liver_l16_short ft_dice=0.85857（evidence_table.csv）。数据截断问题有 data_check.json 详细审计记录，证据链完整自洽，论文锚值独立存放未混入实测。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 诚实且详尽地记录了冻结数据的 gzip 截断缺陷及其对源池规模的毁灭性影响，TE 方法的 source-free 伪标签实现逻辑严密，基线对比完整且证据链高度一致。
- 不足: 受限于数据缺陷导致源池退化，top-1 选择未命中，且相关系数绝对值未能复现论文锚值的量级，偏差较大。