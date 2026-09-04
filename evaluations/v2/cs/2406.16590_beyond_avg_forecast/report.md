# EVAL REPORT v2: 2406.16590_beyond_avg_forecast

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 77.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 37.0 | 60 | A1(15分)：Agent正确读取了6个.tsf文件（M3 2829条+Tourism 1311条=4140条），严格按@horizon留测，SMAPE口径正确且无泄漏，落入满分带。A2(22分)：Agent独立复现了F2（末步NHITS占优，首步接近）和F5（胜率落入30-70%区间），部分复现F3和F6，但未复现F1（Overall ETS优于NHITS）和F4（异常点未被经典超越）。根据Rubric，复现2-3个发现落入半满带，得22分。Agent对未复现现象给出了基于数据子集差异（无M4）的合理科学归因，但数值带匹配铁律要求按实际复现数量给分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示metrics.json和evidence_table.csv等实测证据文件均存在，且包含完整的代码结构。报告中的关键实测数值（如Overall ETS 16.99、NHITS 17.34，Horizon first_step ETS 12.48、NHITS 13.26，last_step NHITS 21.54）与evidence_table.csv及metrics.json中的落盘数据严格一致，可核对无误。无抄数嫌疑，落入最高档[30,40]，给40分。 |

## A 核心结果达成度（37.0/60）

A1(15分)：Agent正确读取了6个.tsf文件（M3 2829条+Tourism 1311条=4140条），严格按@horizon留测，SMAPE口径正确且无泄漏，落入满分带。A2(22分)：Agent独立复现了F2（末步NHITS占优，首步接近）和F5（胜率落入30-70%区间），部分复现F3和F6，但未复现F1（Overall ETS优于NHITS）和F4（异常点未被经典超越）。根据Rubric，复现2-3个发现落入半满带，得22分。Agent对未复现现象给出了基于数据子集差异（无M4）的合理科学归因，但数值带匹配铁律要求按实际复现数量给分。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示metrics.json和evidence_table.csv等实测证据文件均存在，且包含完整的代码结构。报告中的关键实测数值（如Overall ETS 16.99、NHITS 17.34，Horizon first_step ETS 12.48、NHITS 13.26，last_step NHITS 21.54）与evidence_table.csv及metrics.json中的落盘数据严格一致，可核对无误。无抄数嫌疑，落入最高档[30,40]，给40分。

## 证据与重算说明

独立重算未执行。关键实测数核对：总序列数4140（M3 2829 + Tourism 1311）；Overall SMAPE（ETS 16.9858，NHITS 17.3442）；Horizon first_step（ETS 12.4802，NHITS 13.2637），last_step（NHITS 21.5391）；Win-rate NHITS vs ETS 0.4319。所有数值在report.md、evidence_table.csv和metrics.json中完全一致。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 实验设计严谨，多视角评估协议实现完整，代码与证据文件高度一致；对未复现的论文发现能结合数据子集差异（无M4、Tourism强季节性）给出极具说服力的科学归因。
- 不足: 受限于冻结数据包（无M4）和轻量级N-HiTS配置，未能复现论文中深度模型在Overall和异常点上的绝对优势，导致核心发现方向一致性（A2）得分受限。