# EVAL REPORT v7: 2608.06662_mlip_cross_geometry

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 46.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 6.0 | 12 | |
| A2 科学结论保真 | 15.0 | 33 | |
| A3 方法严谨与可复现 | 5.0 | 15 | |
| **A 合计** | **26.0** | 60 | A1(6): 产出了metrics.json和evidence_table，但per_structure_errors.csv仅含CHGNet，缺失MACE/MPA0数据，且缺核心推理与聚合代码，存在明显交付缺口。A2(15): 成功复现几何依赖退化方向及MP-NC<MP-C趋势，但核心数值（均值、最佳模型）偏离或未验证，受partially_supported硬上限约束给15分。A3(5): 缺失关键推理与聚合代码，且多模型底层CSV不全，无法独立复算，可复现性存在明显顾虑。 |
| B 真值一致性/可验证性 | 20.0 | 40 | truth_check=diverged | agent数 vs 锚点逐条比对：1. 均值能量：agent 45.04 vs 锚点 20 → 偏离（超容差）；2. 均值力：agent 382.55 vs 锚点 400 → 吻合（在±100容差内）；3. MP-NC < MP-C 方向：agent MPA0(39.62) < MP-C均值(47.75) vs 锚点 MP-NC < MP-C → 吻合；4. 几何方向性(neck/wire力最大)：agent CHGNet neck+wire(478.6) > bulk+slab(256.4) vs 锚点 neck/wire最大 → 吻合；5. ORB-V3最佳数值：agent 未运行 vs 锚点 6/197.3 → 无法核对。综合判定为diverged。 |

## A 核心结果达成度（26.0/60 = A1 6.0 + A2 15.0 + A3 5.0）

A1(6): 产出了metrics.json和evidence_table，但per_structure_errors.csv仅含CHGNet，缺失MACE/MPA0数据，且缺核心推理与聚合代码，存在明显交付缺口。A2(15): 成功复现几何依赖退化方向及MP-NC<MP-C趋势，但核心数值（均值、最佳模型）偏离或未验证，受partially_supported硬上限约束给15分。A3(5): 缺失关键推理与聚合代码，且多模型底层CSV不全，无法独立复算，可复现性存在明显顾虑。

## B 真值一致性/可验证性（20.0/40）[truth_check=diverged]

agent数 vs 锚点逐条比对：1. 均值能量：agent 45.04 vs 锚点 20 → 偏离（超容差）；2. 均值力：agent 382.55 vs 锚点 400 → 吻合（在±100容差内）；3. MP-NC < MP-C 方向：agent MPA0(39.62) < MP-C均值(47.75) vs 锚点 MP-NC < MP-C → 吻合；4. 几何方向性(neck/wire力最大)：agent CHGNet neck+wire(478.6) > bulk+slab(256.4) vs 锚点 neck/wire最大 → 吻合；5. ORB-V3最佳数值：agent 未运行 vs 锚点 6/197.3 → 无法核对。综合判定为diverged。

## 证据与重算说明

独立重算未执行。关键实测数：CHGNet全局56.02/351.04，MACE全局39.47/421.43，MPA0全局39.62/375.19；全体均值45.04/382.55。per_structure_errors.csv仅含CHGNet的574帧数据，MACE与MPA0的逐结构证据缺失，且核心推理代码未提交。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 准确复现了几何依赖退化的核心方向性结论以及MP-NC优于MP-C的分组趋势，机制关联分析合理。
- 不足: 缺失关键推理与聚合代码导致不可复现，且未提交所有模型的逐结构误差CSV，核心数值（如均值能量）与论文真值存在较大偏离。