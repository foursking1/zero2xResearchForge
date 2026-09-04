# EVAL REPORT v5: 2509.16616_risky_investors_ranking

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 45.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 5.0 | 33 | |
| A3 方法严谨与可复现 | 10.0 | 15 | |
| **A 合计** | **27.0** | 60 | A1(12): 核心交付物（代码、evidence_table、metrics.json、data_facts等）完整产出，符合任务要求。A2(5): 实测结果与论文核心claim完全矛盾（PA-RiskRanker在两个数据集上均被多个基线反超，且F1和Loss均劣于Rankformer），结论为contradicted，落入“矛盾”档位，受硬上限约束给5分。A3(10): 实验设计严谨（3-fold CV、固定种子、防泄漏），但agent自承tabular adaptation欠规范及缺乏专有预训练权重导致复现失败，存在轻微方法论顾虑，给10分。 |
| B 证据真实性/实际复现 | 18.0 | 40 | 磁盘证据扫描显示等级为2（证据齐全自洽），包含metrics.json、evidence_table、大量per-fold中间结果及data_facts.json，内部数值高度一致。但受限于conclusion=contradicted的硬上限（B≤20），给18分。 |

## A 核心结果达成度（27.0/60 = A1 12.0 + A2 5.0 + A3 10.0）

A1(12): 核心交付物（代码、evidence_table、metrics.json、data_facts等）完整产出，符合任务要求。A2(5): 实测结果与论文核心claim完全矛盾（PA-RiskRanker在两个数据集上均被多个基线反超，且F1和Loss均劣于Rankformer），结论为contradicted，落入“矛盾”档位，受硬上限约束给5分。A3(10): 实验设计严谨（3-fold CV、固定种子、防泄漏），但agent自承tabular adaptation欠规范及缺乏专有预训练权重导致复现失败，存在轻微方法论顾虑，给10分。

## B 证据真实性/实际复现（18.0/40）

磁盘证据扫描显示等级为2（证据齐全自洽），包含metrics.json、evidence_table、大量per-fold中间结果及data_facts.json，内部数值高度一致。但受限于conclusion=contradicted的硬上限（B≤20），给18分。

## 证据与重算说明

独立重算未执行。关键实测数：creditcard with-prior PA F1=0.9088/Loss=100619.51，Rankformer F1=0.9357；jobprofit with-prior PA F1=0.8046/Loss=35283.02。data_facts.json证实数据规模（敏锐指出jobprofit实际14479行）与1%正类比例，证据链真实可靠。

## 结论

- **科学结论**: `contradicted`
- 亮点: 实验设计严谨，诚实报告了复现失败并给出了极具洞察力的归因分析（replicability gap），证据链文件极其丰富且内部高度自洽。
- 不足: 受限于缺乏专有预训练权重及tabular adaptation的欠规范，未能复现论文的最优结论，核心claim被证伪，导致总分受硬上限截断。