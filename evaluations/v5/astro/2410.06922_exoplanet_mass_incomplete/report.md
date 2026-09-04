# EVAL REPORT v5: 2410.06922_exoplanet_mass_incomplete

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 69.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **41.0** | 60 | A1(12)：核心交付物（代码、证据表、metrics.json、报告等）完整产出，符合任务要求。A2(14)：完整子集排名模式（kNN×KDE最优、GAIN最差）完美复现，但全档案中MissForest超越kNN×KDE导致排名部分反转，且8属性扩展方向与论文相反（略损而非提升），属于部分支持；受partially_supported硬上限（A2≤15）约束给14分。A3(15)：方法严谨，防泄漏措施（距离计算排除质量维）明确，鲁棒性分析（batch-LOO vs 严格LOO、温度敏感性）深入且sound。 |
| B 证据真实性/实际复现 | 28.0 | 40 | 磁盘证据扫描显示证据等级为2（齐全自洽）。metrics.json与evidence_table.csv均存在，且关键数值在报告、证据表与JSON中严格一致。实测数值与论文锚值有明显差异，符合快照差异预期，无抄袭嫌疑，证据链闭环。受partially_supported结论硬上限（B≤28）约束，给28分。 |

## A 核心结果达成度（41.0/60 = A1 12.0 + A2 14.0 + A3 15.0）

A1(12)：核心交付物（代码、证据表、metrics.json、报告等）完整产出，符合任务要求。A2(14)：完整子集排名模式（kNN×KDE最优、GAIN最差）完美复现，但全档案中MissForest超越kNN×KDE导致排名部分反转，且8属性扩展方向与论文相反（略损而非提升），属于部分支持；受partially_supported硬上限（A2≤15）约束给14分。A3(15)：方法严谨，防泄漏措施（距离计算排除质量维）明确，鲁棒性分析（batch-LOO vs 严格LOO、温度敏感性）深入且sound。

## B 证据真实性/实际复现（28.0/40）

磁盘证据扫描显示证据等级为2（齐全自洽）。metrics.json与evidence_table.csv均存在，且关键数值在报告、证据表与JSON中严格一致。实测数值与论文锚值有明显差异，符合快照差异预期，无抄袭嫌疑，证据链闭环。受partially_supported结论硬上限（B≤28）约束，给28分。

## 证据与重算说明

独立重算未执行。关键实测数核对：complete kNN×KDE eps=0.9139，full GAIN eps=4.5402，extended kNN×KDE eps=1.4036，与报告及metrics.json完全一致，证据内部高度自洽。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 诚实且深入地分析了快照差异（2026 vs 2023）导致的排名反转与方向不一致，未强行拟合论文结论；证据文件齐全，数值高度自洽，透明度极高。
- 不足: 全档案中kNN×KDE未能复现最优排名（被MissForest超越），且8属性扩展方向与论文相反，导致核心结论仅为部分支持。