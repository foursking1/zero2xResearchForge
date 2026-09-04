# EVAL REPORT v2: 2606.12651_physics_aware_gnn_ood

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 98.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1：基线OOD AUC实测0.98521，与论文0.9774相对差约0.8%（≤5%），落入满分带，证据见于metrics.json与evidence_table.csv，得20分。A2：+both变体Δ=+0.00243，95% CI=[+0.00094, +0.00393]，方向为正且CI不含0，满足'至少实现一个变体显著'的满分条件，得20分。A3：标签分布实测53552 easy / 12009 hard（81.7%），与论文82%相对差<1%，落入满分带，得20分。A总分60。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘扫描显示metrics.json、evidence_table.csv及多个raw_evals文件均存在且结构完整。报告中的关键数值（如baseline AUC 0.98521，+both Δ 0.00243及CI）与metrics.json和evidence_table.csv中的落盘数据严格一致，证据链闭环且可核对。属于'有证据文件且数值与报告严格一致'档位，给38分。 |

## A 核心结果达成度（60/60）

A1：基线OOD AUC实测0.98521，与论文0.9774相对差约0.8%（≤5%），落入满分带，证据见于metrics.json与evidence_table.csv，得20分。A2：+both变体Δ=+0.00243，95% CI=[+0.00094, +0.00393]，方向为正且CI不含0，满足'至少实现一个变体显著'的满分条件，得20分。A3：标签分布实测53552 easy / 12009 hard（81.7%），与论文82%相对差<1%，落入满分带，得20分。A总分60。

## B 证据真实性/实际复现（38.0/40）

磁盘扫描显示metrics.json、evidence_table.csv及多个raw_evals文件均存在且结构完整。报告中的关键数值（如baseline AUC 0.98521，+both Δ 0.00243及CI）与metrics.json和evidence_table.csv中的落盘数据严格一致，证据链闭环且可核对。属于'有证据文件且数值与报告严格一致'档位，给38分。

## 证据与重算说明

独立重算未执行。关键实测数：baseline AUC=0.98521，+both Δ=0.002426 (CI: 0.000938~0.003926)，语料分布 53552/12009。所有核心指标在results/metrics.json与evidence_table.csv中均有对应且一致的记录，无抄写论文数字嫌疑。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 证据链极其完整，提供了多协议（regime1/2）的详尽raw_evals和统计结果，代码结构清晰且具备无RDKit环境的回退机制，复现态度严谨。
- 不足: +complexity和+strain变体未能复现出论文中的显著正向提升，且敏感性分析显示效应依赖特定训练协议，表明原论文结论的鲁棒性存疑。