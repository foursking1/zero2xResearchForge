# EVAL REPORT v5: 2606.12651_physics_aware_gnn_ood

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 69.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **41.0** | 60 | A1: 12分。核心交付物（claim.md, report.md, code/, results/等）完整产出，完全符合任务要求。A2: 14分。成功复现了基线AUC、标签分布以及+both变体的显著正向提升，但+complexity和+strain单独未达显著，且敏感性分析显示效应依赖特定协议，故结论为partially_supported。受结论级硬上限约束（A2≤15），给14分。A3: 15分。方法严谨，OOD划分严格无泄漏，bootstrap统计规范，代码具备无RDKit环境的回退机制，可复现性强。 |
| B 证据真实性/实际复现 | 28.0 | 40 | 28分。磁盘证据扫描显示证据等级为2（齐全自洽），提供了完整的metrics.json、evidence_table.csv及多协议raw_evals，数据内部高度自洽，证据链闭环。但受partially_supported结论的硬上限约束（B≤28），故给28分。 |

## A 核心结果达成度（41.0/60 = A1 12.0 + A2 14.0 + A3 15.0）

A1: 12分。核心交付物（claim.md, report.md, code/, results/等）完整产出，完全符合任务要求。A2: 14分。成功复现了基线AUC、标签分布以及+both变体的显著正向提升，但+complexity和+strain单独未达显著，且敏感性分析显示效应依赖特定协议，故结论为partially_supported。受结论级硬上限约束（A2≤15），给14分。A3: 15分。方法严谨，OOD划分严格无泄漏，bootstrap统计规范，代码具备无RDKit环境的回退机制，可复现性强。

## B 证据真实性/实际复现（28.0/40）

28分。磁盘证据扫描显示证据等级为2（齐全自洽），提供了完整的metrics.json、evidence_table.csv及多协议raw_evals，数据内部高度自洽，证据链闭环。但受partially_supported结论的硬上限约束（B≤28），故给28分。

## 证据与重算说明

独立重算未执行。关键实测数：baseline AUC=0.98521，+both Δ=0.00243 (CI: 0.000938~0.003926)，语料分布 53552/12009 (81.7% easy)。所有核心指标在results/metrics.json与evidence_table.csv中均有对应且一致的记录，无抄写嫌疑。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 证据链极其完整，提供了多协议的详尽raw_evals和统计结果，复现态度严谨，统计检验实现规范且落盘证据充分。
- 不足: +complexity和+strain变体未能复现出论文中的显著正向提升，且敏感性分析显示效应依赖特定训练协议，表明原论文部分结论的鲁棒性存疑。