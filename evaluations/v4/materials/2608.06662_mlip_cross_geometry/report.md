# EVAL REPORT v3: 2608.06662_mlip_cross_geometry

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 68.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 43.0 | 60 | A1方向性判定完全正确，neck/wire力误差显著大于bulk/slab，低配位能量误差放大（20分）；A2因ORB-V3不可得使用MPA0替代并合理归因，按rubric落入13分档（13分）；A3验证了MP-NC<MP-C方向及分组清单（10分），但全体均值能量超容差且未验证MP-C最佳模型。总计43分。 |
| B 证据真实性/实际复现 | 25.0 | 40 | 证据等级为2，但per_structure_errors.csv仅包含CHGNet数据，缺失MACE和MPA0的逐结构误差表；且代码缺失核心依赖infer_mlip.py（infer_mace.py中import了它），导致脚本无法直接运行重算。属于关键证据与代码缺失，落入[11,29]区间，给25分。 |

## A 核心结果达成度（43.0/60）

A1方向性判定完全正确，neck/wire力误差显著大于bulk/slab，低配位能量误差放大（20分）；A2因ORB-V3不可得使用MPA0替代并合理归因，按rubric落入13分档（13分）；A3验证了MP-NC<MP-C方向及分组清单（10分），但全体均值能量超容差且未验证MP-C最佳模型。总计43分。

## B 证据真实性/实际复现（25.0/40）

证据等级为2，但per_structure_errors.csv仅包含CHGNet数据，缺失MACE和MPA0的逐结构误差表；且代码缺失核心依赖infer_mlip.py（infer_mace.py中import了它），导致脚本无法直接运行重算。属于关键证据与代码缺失，落入[11,29]区间，给25分。

## 证据与重算说明

独立重算未执行。关键实测数：CHGNet全局56.02/351.04，MACE全局39.47/421.43，MPA0全局39.62/375.19；全体均值45.04/382.55。per_structure_errors.csv仅含CHGNet的574帧数据，MACE与MPA0的逐结构证据缺失，且infer_mlip.py未提交。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 方向性判定准确且机制关联深入，多模型对比与归因分析逻辑严密，提供了完整的聚合证据表与metrics.json。
- 不足: 缺失关键依赖代码（infer_mlip.py）导致脚本不可直接运行，且未提交MACE和MPA0的逐结构误差CSV，证据链不完整。