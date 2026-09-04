# EVAL REPORT v3: 2401.15089_pst_matbench

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v3（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 83.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 48.0 | 60 | A1(16/20): 统计了fold0样本数及5折协议，但未列出全量5折统计。A2(22/25): 完成3个属性5折CV及消融，使用LightGBM代理模型，符合任务允许的简化方案。A3(10/15): 实测MAE（Gap 0.504, Form 0.167, Shear 0.108）与锚值（0.210, 0.032, 0.074）偏差明显（1.5x-5.2x），但消融方向（PDD-only 0.814 > Comp-only 0.528 > 组合 0.516）与论文一致，落入部分满足band。 |
| B 证据真实性/实际复现 | 35.0 | 40 | 磁盘证据齐全（metrics.json, evidence_table.csv, 代码, 日志），证据等级2。evidence_table与日志、metrics.json数值严格对齐（如mp_gap fold0 0.5026），无抄写论文数字嫌疑，属于[30,40]区间，给35分。 |

## A 核心结果达成度（48.0/60）

A1(16/20): 统计了fold0样本数及5折协议，但未列出全量5折统计。A2(22/25): 完成3个属性5折CV及消融，使用LightGBM代理模型，符合任务允许的简化方案。A3(10/15): 实测MAE（Gap 0.504, Form 0.167, Shear 0.108）与锚值（0.210, 0.032, 0.074）偏差明显（1.5x-5.2x），但消融方向（PDD-only 0.814 > Comp-only 0.528 > 组合 0.516）与论文一致，落入部分满足band。

## B 证据真实性/实际复现（35.0/40）

磁盘证据齐全（metrics.json, evidence_table.csv, 代码, 日志），证据等级2。evidence_table与日志、metrics.json数值严格对齐（如mp_gap fold0 0.5026），无抄写论文数字嫌疑，属于[30,40]区间，给35分。

## 证据与重算说明

独立重算未执行。关键实测数：mp_gap MAE 0.5037，mp_e_form MAE 0.1671，log_gvrh MAE 0.1084；消融：Comp-only 0.5275，PDD-only 0.8142，PST-ish 0.5156。证据文件齐全且内部自洽。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 严格遵循简化代理模型方案，完整执行5折CV协议，消融实验方向与论文完全一致，证据链完整且多文件数值严格对齐。
- 不足: Formation Energy等属性的绝对精度与论文锚值差距较大（约5倍），未能完全复现PST的绝对精度优势；数据统计仅详细展示了fold0而非全量5折。