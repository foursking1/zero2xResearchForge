# EVAL REPORT v7: 2606.12651_physics_aware_gnn_ood

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 61.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **41.0** | 60 | A1(12分)：核心交付物完整，包含metrics.json、evidence_table.csv及多协议raw_evals等机器可读结果文件，完全符合任务要求。A2(14分)：结论为partially_supported，受硬上限约束(≤15)。基线AUC和标签分布完美复现，+both变体定性复现（方向为正且CI不含0），但定量数值与论文有差距，且+complexity和+strain未能复现论文所述的显著提升。A3(15分)：方法严谨，OOD划分严格无泄漏，配对bootstrap统计规范，代码具备无RDKit环境的回退机制，可复现性强。 |
| B 真值一致性/可验证性 | 20.0 | 40 | truth_check=diverged | 真值逐条比对：1. 基线OOD AUC：agent 0.98521 vs 锚点 0.9774 → 吻合（相对差0.8% < 5%容差）。2. 标签分布：agent 81.7% easy vs 锚点 81.6% (53159/65177) → 吻合。3. +both Δ：agent +0.00243 vs 锚点 +0.0066 → 偏离（数值差距超60%，但方向一致且CI不含0）。4. +complexity Δ：agent -0.00115 vs 锚点 +0.0060 → 偏离（方向相反，未复现）。5. +strain Δ：agent +0.00151 vs 锚点 +0.0032 → 偏离（数值差一半且CI含0）。综合判定为diverged，因核心变体提升幅度与论文真值存在明显偏离，且部分变体方向/显著性未复现。 |

## A 核心结果达成度（41.0/60 = A1 12.0 + A2 14.0 + A3 15.0）

A1(12分)：核心交付物完整，包含metrics.json、evidence_table.csv及多协议raw_evals等机器可读结果文件，完全符合任务要求。A2(14分)：结论为partially_supported，受硬上限约束(≤15)。基线AUC和标签分布完美复现，+both变体定性复现（方向为正且CI不含0），但定量数值与论文有差距，且+complexity和+strain未能复现论文所述的显著提升。A3(15分)：方法严谨，OOD划分严格无泄漏，配对bootstrap统计规范，代码具备无RDKit环境的回退机制，可复现性强。

## B 真值一致性/可验证性（20.0/40）[truth_check=diverged]

真值逐条比对：1. 基线OOD AUC：agent 0.98521 vs 锚点 0.9774 → 吻合（相对差0.8% < 5%容差）。2. 标签分布：agent 81.7% easy vs 锚点 81.6% (53159/65177) → 吻合。3. +both Δ：agent +0.00243 vs 锚点 +0.0066 → 偏离（数值差距超60%，但方向一致且CI不含0）。4. +complexity Δ：agent -0.00115 vs 锚点 +0.0060 → 偏离（方向相反，未复现）。5. +strain Δ：agent +0.00151 vs 锚点 +0.0032 → 偏离（数值差一半且CI含0）。综合判定为diverged，因核心变体提升幅度与论文真值存在明显偏离，且部分变体方向/显著性未复现。

## 证据与重算说明

独立重算未执行。关键实测数：baseline AUC=0.98521，+both Δ=0.00243 (CI: 0.000938~0.003926)，语料分布 53552/12009 (81.7% easy)。所有核心指标在results/metrics.json与evidence_table.csv中均有对应且一致的记录，证据链闭环，无抄写论文数字嫌疑，但变体Δ实测值与论文真值存在客观偏离。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 证据链极其完整，提供了多协议（regime1/2）的详尽raw_evals和统计结果，复现态度严谨，统计检验（bootstrap CI）实现规范且落盘证据充分。
- 不足: +complexity和+strain变体未能复现出论文中的显著正向提升，且+both的定量提升幅度与论文真值差距较大，敏感性分析显示效应依赖特定训练协议，表明原论文结论的鲁棒性存疑。