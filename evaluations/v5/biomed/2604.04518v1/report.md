# EVAL REPORT v5: 2604.04518v1

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 67.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 12.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **39.0** | 60 | A1(12): 核心交付物（代码、evidence_table、metrics.json、solution.md）完整产出，符合任务要求，无缺失。A2(12): 成功复现了C01（Clever Hans baseline，R01落入容差）和SpRAy标签质量（R08），但受限于算力与环境，核心的C02/C03（XAI correction与CFKD的优势）未能复现，agent诚实判定为contradicted。因核心结论未完全成立，受partially_supported硬上限（A2≤15）约束，给予12分。A3(15): 方法严谨，对数据重建、proxy简化及超参缩减等deviation进行了极其诚实且详尽的记录，无数据泄漏，可复现性极强。 |
| B 证据真实性/实际复现 | 28.0 | 40 | 磁盘证据扫描显示证据等级为2（齐全自洽），metrics.json与evidence_table.csv数据丰富、结构清晰且内部自洽，包含大量中间模型指标、SpRAy聚类结果与运行日志，证据链完整闭环，无任何编造痕迹。受partially_supported结论硬上限（B≤28）约束，给予28分。 |

## A 核心结果达成度（39.0/60 = A1 12.0 + A2 12.0 + A3 15.0）

A1(12): 核心交付物（代码、evidence_table、metrics.json、solution.md）完整产出，符合任务要求，无缺失。A2(12): 成功复现了C01（Clever Hans baseline，R01落入容差）和SpRAy标签质量（R08），但受限于算力与环境，核心的C02/C03（XAI correction与CFKD的优势）未能复现，agent诚实判定为contradicted。因核心结论未完全成立，受partially_supported硬上限（A2≤15）约束，给予12分。A3(15): 方法严谨，对数据重建、proxy简化及超参缩减等deviation进行了极其诚实且详尽的记录，无数据泄漏，可复现性极强。

## B 证据真实性/实际复现（28.0/40）

磁盘证据扫描显示证据等级为2（齐全自洽），metrics.json与evidence_table.csv数据丰富、结构清晰且内部自洽，包含大量中间模型指标、SpRAy聚类结果与运行日志，证据链完整闭环，无任何编造痕迹。受partially_supported结论硬上限（B≤28）约束，给予28分。

## 证据与重算说明

独立重算未执行（依规则仅做磁盘扫描与逻辑校验）。关键实测数：R01复现AGA=0.501（锚51.1%），R08复现SpRAy acc=0.992（锚100%），均在容差内或方向一致；C02/C03的correction AGA提升未达论文水平，均有真实落盘metrics支撑其contradicted结论。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 科学态度极其严谨，对未能复现的claim没有强行凑数，而是通过feature-probe机制分析给出了令人信服的解释；数据与代码证据链极其完整。
- 不足: 受限于CPU算力，部分核心correction方法使用了缩减网格或proxy，导致C02/C03的定量结果与论文存在较大差距，未能复现论文的核心修复效果。