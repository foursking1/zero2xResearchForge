# EVAL REPORT v5: wong_2020

- 执行 agent: Claude Code（DeepSeek 网关）
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 69.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **41.0** | 60 | A1: 完整产出了TASK要求的所有核心交付物，包括solution.md、代码、evidence_table和metrics.json，得12分。A2: Agent成功复现了C02的核心斜率和r2，以及C03 climax子集的斜率和r2，但C01和C03 overall的指标偏离较大，整体结论为partially_supported。受结论级硬上限约束（A2≤15），给14分。A3: 方法描述详尽，提供了光级匹配和深度匹配的具体逻辑，并输出了完整的中间匹配结果CSV，无数据泄漏，可复现性强，得15分。 |
| B 证据真实性/实际复现 | 28.0 | 40 | 证据等级为2（齐全自洽）。Agent不仅提供了metrics.json和evidence_table.csv，还输出了多个详细的中间匹配过程CSV，证据链极其完整。但受限于partially_supported结论的硬上限（B≤28），故给28分。 |

## A 核心结果达成度（41.0/60 = A1 12.0 + A2 14.0 + A3 15.0）

A1: 完整产出了TASK要求的所有核心交付物，包括solution.md、代码、evidence_table和metrics.json，得12分。A2: Agent成功复现了C02的核心斜率和r2，以及C03 climax子集的斜率和r2，但C01和C03 overall的指标偏离较大，整体结论为partially_supported。受结论级硬上限约束（A2≤15），给14分。A3: 方法描述详尽，提供了光级匹配和深度匹配的具体逻辑，并输出了完整的中间匹配结果CSV，无数据泄漏，可复现性强，得15分。

## B 证据真实性/实际复现（28.0/40）

证据等级为2（齐全自洽）。Agent不仅提供了metrics.json和evidence_table.csv，还输出了多个详细的中间匹配过程CSV，证据链极其完整。但受限于partially_supported结论的硬上限（B≤28），故给28分。

## 证据与重算说明

独立重算未执行（基于磁盘证据扫描）。关键实测数：C02 slope=14858.6, r2=0.605；C03 climax slope=0.323, r2=0.898；C01 slope=0.574, r2=0.422。所有数值均有对应的evidence_table和metrics.json及中间CSV支撑。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 证据链极其完整，提供了详尽的中间匹配数据CSV，使得复算和校验变得非常容易；对未能复现的指标进行了诚实且合理的归因分析。
- 不足: C01和C03 overall的回归指标与论文锚值存在较大偏差，未能完全复现论文的所有统计结论，导致最终判定为partially_supported。