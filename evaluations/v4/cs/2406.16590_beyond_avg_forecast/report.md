# EVAL REPORT v3: 2406.16590_beyond_avg_forecast

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 77.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 37.0 | 60 | A1(15分)：Agent正确读取6个.tsf文件（M3 2829条+Tourism 1311条=4140条），严格按@horizon留测，SMAPE口径正确且无泄漏，落入满分带。A2(22分)：实测数值核对：Overall ETS 16.99优于NHITS 17.34（F1未复现）；Horizon首步ETS 12.48与NHITS 13.26接近，末步NHITS 21.54最优（F2复现）；频率视角年度最优但季度落后（F3部分复现）；异常点NHITS 20.32最优未被超越（F4方向相反）；胜率NHITS vs ETS 0.432、vs Theta 0.626均落入30-70%带（F5复现）；困难问题NHITS 59.46优势未缩小（F6未复现）。独立复现2个核心发现，落入半满带得22分。A总计37分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示证据等级为2（齐全自洽）。metrics.json与evidence_table.csv、winloss_table.csv等实测证据文件均存在且结构完整。报告中的关键实测数值与落盘JSON/CSV数据严格一致，内部自洽，无抄数嫌疑，符合最高档标准，给40分。 |

## A 核心结果达成度（37.0/60）

A1(15分)：Agent正确读取6个.tsf文件（M3 2829条+Tourism 1311条=4140条），严格按@horizon留测，SMAPE口径正确且无泄漏，落入满分带。A2(22分)：实测数值核对：Overall ETS 16.99优于NHITS 17.34（F1未复现）；Horizon首步ETS 12.48与NHITS 13.26接近，末步NHITS 21.54最优（F2复现）；频率视角年度最优但季度落后（F3部分复现）；异常点NHITS 20.32最优未被超越（F4方向相反）；胜率NHITS vs ETS 0.432、vs Theta 0.626均落入30-70%带（F5复现）；困难问题NHITS 59.46优势未缩小（F6未复现）。独立复现2个核心发现，落入半满带得22分。A总计37分。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示证据等级为2（齐全自洽）。metrics.json与evidence_table.csv、winloss_table.csv等实测证据文件均存在且结构完整。报告中的关键实测数值与落盘JSON/CSV数据严格一致，内部自洽，无抄数嫌疑，符合最高档标准，给40分。

## 证据与重算说明

独立重算未执行。关键实测数核对：总序列数4140；Overall SMAPE（ETS 16.9858，NHITS 17.3442）；Horizon first_step（ETS 12.4802，NHITS 13.2637），last_step（NHITS 21.5391）；Win-rate NHITS vs ETS 0.4319。所有数值在report.md、evidence_table.csv和metrics.json中完全一致。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 实验设计严谨，多视角评估协议实现完整，代码与证据文件高度一致，对未复现现象给出了基于数据子集差异（无M4）的合理科学归因。
- 不足: 受限于冻结数据包和轻量级模型配置，未能复现论文中深度模型在Overall和异常点上的绝对优势，导致核心发现方向一致性（A2）得分受限。