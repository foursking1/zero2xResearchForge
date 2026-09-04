# EVAL REPORT v5: 2602.13288_cloud_telemetry_ad

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 70.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 15.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **42.0** | 60 | A1: 核心交付物（代码、evidence_table、metrics.json、报告）完整产出，覆盖所有要求的模型与数据集，得12分。A2: 成功复现了GRU全正及NAB无主导架构的趋势，但未能复现GRU的“唯一”全正性（TCN/TSMixer亦全正），总体结论为partially_supported。受结论级硬上限约束，A2给15分。A3: 方法严谨，严格遵循70/30时间切分与训练期校准，无数据泄漏，提供多种子与严格阈值的敏感性分析，可复现性强，得15分。 |
| B 证据真实性/实际复现 | 28.0 | 40 | 磁盘证据极其详实，包含metrics.json、多组evidence_table及敏感性分析结果，内部自洽且与报告严格一致。证据等级为2（齐全自洽），但受partially_supported结论的硬上限约束，B维度最高给28分。 |

## A 核心结果达成度（42.0/60 = A1 12.0 + A2 15.0 + A3 15.0）

A1: 核心交付物（代码、evidence_table、metrics.json、报告）完整产出，覆盖所有要求的模型与数据集，得12分。A2: 成功复现了GRU全正及NAB无主导架构的趋势，但未能复现GRU的“唯一”全正性（TCN/TSMixer亦全正），总体结论为partially_supported。受结论级硬上限约束，A2给15分。A3: 方法严谨，严格遵循70/30时间切分与训练期校准，无数据泄漏，提供多种子与严格阈值的敏感性分析，可复现性强，得15分。

## B 证据真实性/实际复现（28.0/40）

磁盘证据极其详实，包含metrics.json、多组evidence_table及敏感性分析结果，内部自洽且与报告严格一致。证据等级为2（齐全自洽），但受partially_supported结论的硬上限约束，B维度最高给28分。

## 证据与重算说明

独立重算未执行（受限于裁判环境）。关键实测数核对：Microsoft GRU application-crash-rate-1=30.7416，NAB realTraffic IsolationForest=56.121，均在evidence_table.csv与metrics.json中严格对应。Agent诚实报告了与论文锚值的差异（如TCN全正），未发现抄袭论文数字的现象。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 实验管线完整严谨，主动提供了多随机种子与严格阈值网格的敏感性分析，证据链极其扎实且诚实报告了与论文锚值的差异。
- 不足: 未能复现论文中GRU在Microsoft数据集上的“唯一全正”特性，可能源于网格搜索校准与论文贝叶斯搜索的寻优能力差异，导致核心claim仅部分成立。