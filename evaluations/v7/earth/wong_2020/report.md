# EVAL REPORT v7: wong_2020

- 执行 agent: Claude Code（DeepSeek 网关）
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 66.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **41.0** | 60 | A1: 核心交付物完整，包含metrics.json、evidence_table.csv、solution.md及可运行代码，得12分。A2: 成功复现C02的核心斜率与r2，以及C03 climax子集的斜率与r2，但C01和C03 overall的指标偏离较大，整体结论为partially_supported，受结论级硬上限约束（A2≤15）给14分。A3: 方法描述详尽，提供了光级匹配和深度匹配的具体逻辑，并输出了完整的中间匹配结果CSV，无数据泄漏，可复现性强，得15分。 |
| B 真值一致性/可验证性 | 25.0 | 40 | truth_check=diverged | 真值逐条比对：1) C02 slope: agent 14858.6 vs 锚点 14910 → 吻合(<1%)；2) C02 r2: agent 0.605 vs 锚点 0.61 → 吻合(<1%)；3) C03 climax slope: agent 0.323 vs 锚点 0.33 → 吻合(~2%)；4) C03 climax r2: agent 0.898 vs 锚点 0.85 → 吻合(~5.6%)；5) C01 slope: agent 0.574 vs 锚点 0.85 → 偏离；6) C01 r2: agent 0.422 vs 锚点 0.72 → 偏离；7) C03 overall slope: agent 0.722 vs 锚点 0.99 → 偏离。因部分核心指标吻合但多项指标显著偏离真值，判定为diverged。受partially_supported硬上限（B≤28）约束，给25分。 |

## A 核心结果达成度（41.0/60 = A1 12.0 + A2 14.0 + A3 15.0）

A1: 核心交付物完整，包含metrics.json、evidence_table.csv、solution.md及可运行代码，得12分。A2: 成功复现C02的核心斜率与r2，以及C03 climax子集的斜率与r2，但C01和C03 overall的指标偏离较大，整体结论为partially_supported，受结论级硬上限约束（A2≤15）给14分。A3: 方法描述详尽，提供了光级匹配和深度匹配的具体逻辑，并输出了完整的中间匹配结果CSV，无数据泄漏，可复现性强，得15分。

## B 真值一致性/可验证性（25.0/40）[truth_check=diverged]

真值逐条比对：1) C02 slope: agent 14858.6 vs 锚点 14910 → 吻合(<1%)；2) C02 r2: agent 0.605 vs 锚点 0.61 → 吻合(<1%)；3) C03 climax slope: agent 0.323 vs 锚点 0.33 → 吻合(~2%)；4) C03 climax r2: agent 0.898 vs 锚点 0.85 → 吻合(~5.6%)；5) C01 slope: agent 0.574 vs 锚点 0.85 → 偏离；6) C01 r2: agent 0.422 vs 锚点 0.72 → 偏离；7) C03 overall slope: agent 0.722 vs 锚点 0.99 → 偏离。因部分核心指标吻合但多项指标显著偏离真值，判定为diverged。受partially_supported硬上限（B≤28）约束，给25分。

## 证据与重算说明

独立重算未执行（基于磁盘证据扫描）。关键实测数如C02 slope=14858.6, r2=0.605；C03 climax slope=0.323, r2=0.898；C01 slope=0.574, r2=0.422，所有数值均有对应的evidence_table.csv、metrics.json及多个中间匹配过程CSV支撑，证据链完整且机器可读。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 证据链极其完整，提供了详尽的中间匹配数据CSV，使得复算和校验变得非常容易；对未能复现的指标进行了诚实且合理的归因分析。
- 不足: C01和C03 overall的回归指标与论文锚值存在较大偏差，未能完全复现论文的所有统计结论，导致最终判定为partially_supported。