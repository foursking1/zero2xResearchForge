# EVAL REPORT v2: 2608.06662_mlip_cross_geometry

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 65.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 43.0 | 60 | A1(20分): 方向判定完全正确，neck/wire力误差显著大于bulk/slab，低配位能量误差放大，且关联了机制，证据表与metrics.json数据一致。A2(13分): ORB-V3因环境依赖问题不可得，使用MPA0替代并明确归因，按rubric规定落入13分档。A3(10分): 运行了3个模型，MP-NC<MP-C方向正确(5分)，报告了清单与分组(5分)；但全体均值能量45.04超出20±5容差(0分)，未验证MP-C最佳模型ORB-V2-MPtrj(0分)。 |
| B 证据真实性/实际复现 | 22.0 | 40 | 有metrics.json和evidence_table.csv，且聚合数值与报告一致。但per_structure_errors.csv仅包含CHGNet的逐结构数据，缺失MACE和MPA0的逐结构CSV，导致列不完整；且代码缺失infer_mlip.py和aggregate.py，无法直接运行重算。依据规则「列不完整/仅为脚本无输出」，B落入[16,29]区间，给22分。 |

## A 核心结果达成度（43.0/60）

A1(20分): 方向判定完全正确，neck/wire力误差显著大于bulk/slab，低配位能量误差放大，且关联了机制，证据表与metrics.json数据一致。A2(13分): ORB-V3因环境依赖问题不可得，使用MPA0替代并明确归因，按rubric规定落入13分档。A3(10分): 运行了3个模型，MP-NC<MP-C方向正确(5分)，报告了清单与分组(5分)；但全体均值能量45.04超出20±5容差(0分)，未验证MP-C最佳模型ORB-V2-MPtrj(0分)。

## B 证据真实性/实际复现（22.0/40）

有metrics.json和evidence_table.csv，且聚合数值与报告一致。但per_structure_errors.csv仅包含CHGNet的逐结构数据，缺失MACE和MPA0的逐结构CSV，导致列不完整；且代码缺失infer_mlip.py和aggregate.py，无法直接运行重算。依据规则「列不完整/仅为脚本无输出」，B落入[16,29]区间，给22分。

## 证据与重算说明

独立重算未执行。关键实测数：CHGNet全局56.02/351.04，MACE全局39.47/421.43，MPA0全局39.62/375.19；全体均值45.04/382.55。per_structure_errors.csv仅含CHGNet的574帧数据，MACE与MPA0的逐结构证据缺失。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 方向性判定准确且机制关联深入，多模型对比与归因分析逻辑严密，提供了完整的聚合证据表。
- 不足: 缺失关键依赖代码（infer_mlip.py等）导致脚本不可直接运行，且未提交MACE和MPA0的逐结构误差CSV，证据链不完整。