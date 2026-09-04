# EVAL REPORT v5: 2401.15089_pst_matbench

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 69.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **41.0** | 60 | A1(12): 核心交付物（代码、evidence_table、metrics.json、报告）完整产出，完成了3个属性的5折CV及消融实验，符合任务要求。A2(14): 实测MAE（Gap 0.504, Form 0.167, Shear 0.108）与论文锚值绝对精度差距较大（1.5x-5x），但消融实验方向（PDD-only最差，组合最优）与论文一致，定性匹配。受限于partially_supported结论硬上限，给14分。A3(15): 方法严谨，使用任务允许的简化代理模型（LightGBM），固定种子并使用验证集early stopping防泄漏，特征计算与数据对齐验证充分，可由提交物复算。 |
| B 证据真实性/实际复现 | 28.0 | 40 | 磁盘证据扫描显示证据等级为2（齐全自洽），metrics.json、evidence_table.csv及预测CSV均存在且内部数值严格对齐，无抄写论文数字嫌疑。但受限于partially_supported结论的硬上限（B≤28），给28分。 |

## A 核心结果达成度（41.0/60 = A1 12.0 + A2 14.0 + A3 15.0）

A1(12): 核心交付物（代码、evidence_table、metrics.json、报告）完整产出，完成了3个属性的5折CV及消融实验，符合任务要求。A2(14): 实测MAE（Gap 0.504, Form 0.167, Shear 0.108）与论文锚值绝对精度差距较大（1.5x-5x），但消融实验方向（PDD-only最差，组合最优）与论文一致，定性匹配。受限于partially_supported结论硬上限，给14分。A3(15): 方法严谨，使用任务允许的简化代理模型（LightGBM），固定种子并使用验证集early stopping防泄漏，特征计算与数据对齐验证充分，可由提交物复算。

## B 证据真实性/实际复现（28.0/40）

磁盘证据扫描显示证据等级为2（齐全自洽），metrics.json、evidence_table.csv及预测CSV均存在且内部数值严格对齐，无抄写论文数字嫌疑。但受限于partially_supported结论的硬上限（B≤28），给28分。

## 证据与重算说明

独立重算未执行。关键实测数：mp_gap MAE 0.5037，mp_e_form MAE 0.1671，log_gvrh MAE 0.1084；消融：Comp-only 0.5275，PDD-only 0.8142，PST-ish 0.5156。所有数值在evidence_table、metrics.json中严格一致。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 严格遵循任务允许的简化代理模型方案，完整执行5折CV协议，消融实验方向与论文完全一致，且证据链多文件严格对齐。
- 不足: 绝对精度与论文锚值差距较大（特别是Formation Energy差约5倍），未能复现PST的绝对精度优势；数据统计仅详细展示了fold0而非全量5折。