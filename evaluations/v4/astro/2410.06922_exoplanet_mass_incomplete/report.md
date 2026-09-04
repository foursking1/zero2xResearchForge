# EVAL REPORT v3: 2410.06922_exoplanet_mass_incomplete

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 70.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 30.0 | 60 | 列出实测数值：complete kNN×KDE=0.914, GAIN=1.988；full MissForest=1.191, kNN×KDE=1.347, GAIN=4.540；extended Δ=+0.056。对照 rubric，满分要求全档案 kNN×KDE 最低且扩展差异<0.05，agent 全档案中 MissForest 优于 kNN×KDE（排名部分反转），且扩展差异为正向损伤，不满足满分条件。满足“排名部分反转但整体模式保持”的半满条件，故 A=30。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示证据等级为2（齐全自洽）。metrics.json、evidence_table.csv 及多个分布 CSV 均存在，且数值在报告、证据表与 JSON 中严格一致。实测数值与论文锚值有明显差异，无抄袭嫌疑，证据链闭环，符合“有 metrics.json 且内部自洽、并有 evidence 表齐全”的条件，B=40。 |

## A 核心结果达成度（30.0/60）

列出实测数值：complete kNN×KDE=0.914, GAIN=1.988；full MissForest=1.191, kNN×KDE=1.347, GAIN=4.540；extended Δ=+0.056。对照 rubric，满分要求全档案 kNN×KDE 最低且扩展差异<0.05，agent 全档案中 MissForest 优于 kNN×KDE（排名部分反转），且扩展差异为正向损伤，不满足满分条件。满足“排名部分反转但整体模式保持”的半满条件，故 A=30。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示证据等级为2（齐全自洽）。metrics.json、evidence_table.csv 及多个分布 CSV 均存在，且数值在报告、证据表与 JSON 中严格一致。实测数值与论文锚值有明显差异，无抄袭嫌疑，证据链闭环，符合“有 metrics.json 且内部自洽、并有 evidence 表齐全”的条件，B=40。

## 证据与重算说明

独立重算未执行。关键实测数核对：complete kNN×KDE eps=0.9139，full GAIN eps=4.5402，extended kNN×KDE eps=1.4036，与报告及 metrics.json 完全一致。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 诚实且深入地分析了快照差异导致的排名反转与方向不一致，未强行拟合论文结论；证据文件齐全，数值高度自洽。
- 不足: 全档案中 kNN×KDE 未能复现最优排名，且 8 属性扩展方向与论文相反，导致核心结果达成度止步于半满档。