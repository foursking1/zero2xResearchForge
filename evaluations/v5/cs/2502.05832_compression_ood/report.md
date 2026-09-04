# EVAL REPORT v5: 2502.05832_compression_ood

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 33.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **60.0** | 60 | A1(12): 核心交付物完整，包含代码、evidence_table、metrics.json及详细报告，完全符合任务要求。A2(33): 完美复现论文核心claim，N=50和N=100档位Δ分别为-4.11pp和-5.36pp，N=10均值Δ=-1.06pp，方向全部一致（imbalanced < balanced）且主档位显著大于1.0pp阈值，效应匹配度极高。A3(15): 方法严谨，固定种子，等总样本量控制公平，防泄漏措施到位，且提供36个独立run的checkpoint和reeval核验，可复现性极强。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示证据等级为2（齐全自洽）。提交物包含完整的evidence_table.csv、metrics.json、36个独立run的子metrics.json以及eval_all.json。特别是提供了eval_all.json进行独立重算核验，36个checkpoint全部match，证据链极其完整且内部高度自洽，符合B=40的最高档标准。 |

## A 核心结果达成度（60.0/60 = A1 12.0 + A2 33.0 + A3 15.0）

A1(12): 核心交付物完整，包含代码、evidence_table、metrics.json及详细报告，完全符合任务要求。A2(33): 完美复现论文核心claim，N=50和N=100档位Δ分别为-4.11pp和-5.36pp，N=10均值Δ=-1.06pp，方向全部一致（imbalanced < balanced）且主档位显著大于1.0pp阈值，效应匹配度极高。A3(15): 方法严谨，固定种子，等总样本量控制公平，防泄漏措施到位，且提供36个独立run的checkpoint和reeval核验，可复现性极强。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示证据等级为2（齐全自洽）。提交物包含完整的evidence_table.csv、metrics.json、36个独立run的子metrics.json以及eval_all.json。特别是提供了eval_all.json进行独立重算核验，36个checkpoint全部match，证据链极其完整且内部高度自洽，符合B=40的最高档标准。

## 证据与重算说明

独立重算未执行（裁判侧未实际运行代码），但依据落盘的eval_all.json和逐run的metrics.json确认了复算一致性。关键实测数：N=50 balanced 25.34 / imbalanced 21.23 (Δ=-4.11)；N=100 balanced 28.21 / imbalanced 22.85 (Δ=-5.36)。

## 结论

- **科学结论**: `supported`
- 亮点: 实验设计极其严谨，提供了36个独立种子的完整checkpoint和reeval核验结果，证据链扎实；对N=10的噪声现象和教师口径差异进行了诚实且深入的机制分析。
- 不足: N=10档位由于极端稀疏导致2/6重复方向反转，虽作了合理解释且均值仍为负，但在严格意义上使得全档位无瑕疵一致略有妥协。