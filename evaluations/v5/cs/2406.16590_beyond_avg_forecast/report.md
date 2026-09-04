# EVAL REPORT v5: 2406.16590_beyond_avg_forecast

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 70.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 15.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **42.0** | 60 | A1(12)：核心交付物完整，包含深度全局模型(N-HiTS)、6种经典局部方法、多视角评估协议及完整的evidence_table和metrics.json。A2(15)：独立复现了F2(末步优势)和F5(胜率区间)等核心发现，但因缺失M4数据导致F1、F4等方向未复现，结论标签为partially_supported，受硬上限约束给满分档15分。A3(15)：方法严谨，严格遵循末H留测防泄漏，条件定义基于SNaive训练期残差，代码带固定种子且可复现。 |
| B 证据真实性/实际复现 | 28.0 | 40 | 磁盘证据扫描显示证据等级为2（齐全自洽），metrics.json与evidence_table.csv等实测证据文件均存在且结构完整，报告中的关键实测数值与落盘数据严格一致，无抄数嫌疑。但受partially_supported结论的硬上限约束，B维度最高给28分。 |

## A 核心结果达成度（42.0/60 = A1 12.0 + A2 15.0 + A3 15.0）

A1(12)：核心交付物完整，包含深度全局模型(N-HiTS)、6种经典局部方法、多视角评估协议及完整的evidence_table和metrics.json。A2(15)：独立复现了F2(末步优势)和F5(胜率区间)等核心发现，但因缺失M4数据导致F1、F4等方向未复现，结论标签为partially_supported，受硬上限约束给满分档15分。A3(15)：方法严谨，严格遵循末H留测防泄漏，条件定义基于SNaive训练期残差，代码带固定种子且可复现。

## B 证据真实性/实际复现（28.0/40）

磁盘证据扫描显示证据等级为2（齐全自洽），metrics.json与evidence_table.csv等实测证据文件均存在且结构完整，报告中的关键实测数值与落盘数据严格一致，无抄数嫌疑。但受partially_supported结论的硬上限约束，B维度最高给28分。

## 证据与重算说明

独立重算未执行。关键实测数核对：总序列数4140；Overall SMAPE（ETS 16.99，NHITS 17.34）；Horizon first_step（ETS 12.48，NHITS 13.26），last_step（NHITS 21.54）；Win-rate NHITS vs ETS 0.432。所有数值在report.md、evidence_table.csv和metrics.json中完全一致。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 实验设计极其严谨，多视角评估协议实现完整，对未复现现象给出了基于数据子集差异（无M4）的极具说服力的科学归因。
- 不足: 受限于冻结数据包（无M4）和轻量级模型配置，未能复现论文中深度模型在Overall和异常点上的绝对优势，导致核心结论仅为部分支持。