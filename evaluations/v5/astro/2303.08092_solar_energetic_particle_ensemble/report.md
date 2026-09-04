# EVAL REPORT v5: 2303.08092_solar_energetic_particle_ensemble

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 60.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 8.0 | 15 | |
| **A 合计** | **34.0** | 60 | A1: 核心交付物完整，包含4种模型的10次切分结果、metrics.json和evidence_table.csv，符合任务要求，给12分。A2: 结论为partially_supported，复现了RH v2优于CoNN及RH集成离散度更低的核心效应，但Committee离散度未低于CoNN，且RH v2在TSS上未超越RH v1，绝对数值因epochs缩减偏离较大。受partially_supported硬上限约束（A2≤15），给14分。A3: 方法上存在明显顾虑，Agent擅自将base epochs从500缩减至150，未严格遵循论文规格，导致绝对指标偏离，影响可比性，给8分。 |
| B 证据真实性/实际复现 | 26.0 | 40 | 证据等级为2（齐全自洽），metrics.json与evidence_table.csv数据详实且内部严格自洽，清洗行数与预期一致。但受partially_supported结论硬上限约束（B≤28），给26分。 |

## A 核心结果达成度（34.0/60 = A1 12.0 + A2 14.0 + A3 8.0）

A1: 核心交付物完整，包含4种模型的10次切分结果、metrics.json和evidence_table.csv，符合任务要求，给12分。A2: 结论为partially_supported，复现了RH v2优于CoNN及RH集成离散度更低的核心效应，但Committee离散度未低于CoNN，且RH v2在TSS上未超越RH v1，绝对数值因epochs缩减偏离较大。受partially_supported硬上限约束（A2≤15），给14分。A3: 方法上存在明显顾虑，Agent擅自将base epochs从500缩减至150，未严格遵循论文规格，导致绝对指标偏离，影响可比性，给8分。

## B 证据真实性/实际复现（26.0/40）

证据等级为2（齐全自洽），metrics.json与evidence_table.csv数据详实且内部严格自洽，清洗行数与预期一致。但受partially_supported结论硬上限约束（B≤28），给26分。

## 证据与重算说明

独立重算未执行。关键实测数：清洗后24570行/74 SEP；CoNN中位TSS=0.807，RH_v2中位TSS=0.868，Committee中位TSS=0.833，RH_v1中位TSS=0.882。evidence_table.csv包含40行逐次切分详实数据，与JSON统计量严格自洽。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 证据链完整且高度自洽，逐次切分数据详实；诚实报告了未成立的子主张并给出了清晰的归因分析。
- 不足: 训练预算大幅缩减（epochs 150 vs 500）导致绝对指标偏离论文锚值，且部分核心相对主张（如Committee离散度、RH v2 vs RH v1）未能成功复现。