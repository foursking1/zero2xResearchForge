# EVAL REPORT v7: 2303.08092_solar_energetic_particle_ensemble

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 49.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 5.0 | 15 | |
| **A 合计** | **31.0** | 60 | A1: 核心交付物完整，包含 metrics.json、evidence_table.csv、claim.md 等机器可读结果，给 12 分。A2: 结论为 partially_supported，正确验证了部分相对锚点（RH v2 TSS > CoNN，RH 离散度更低），但 Committee 离散度未低于 CoNN 且 RH v2 TSS 未超越 RH v1。受 partially_supported 硬上限约束（≤15），给 14 分。A3: 方法上存在明显顾虑，Agent 擅自将 base epochs 从论文规格的 500 缩减至 150，导致绝对指标严重偏离，影响科学严谨性与可比性，给 5 分。 |
| B 真值一致性/可验证性 | 18.0 | 40 | truth_check=diverged | truth_check=diverged。逐条比对：1) CoNN TSS: agent 0.807 vs 锚点 0.906 → 偏离(-0.099，超±0.05容差)；2) RH v2 TSS: agent 0.868 vs 锚点 0.944 → 偏离(-0.076，超容差)；3) CoNN HSS: agent 0.051 vs 锚点 0.163 → 偏离(-0.112，超±0.02容差)；4) RH v2 HSS: agent 0.109 vs 锚点 0.168 → 偏离(-0.059，超容差)。所有绝对指标均超出任务规定的容差带，主要因 epochs 缩减所致。数据清洗行数 agent 24570 vs 预期 24570 → 吻合。因绝对数值显著偏离，判定为 diverged，给 18 分。 |

## A 核心结果达成度（31.0/60 = A1 12.0 + A2 14.0 + A3 5.0）

A1: 核心交付物完整，包含 metrics.json、evidence_table.csv、claim.md 等机器可读结果，给 12 分。A2: 结论为 partially_supported，正确验证了部分相对锚点（RH v2 TSS > CoNN，RH 离散度更低），但 Committee 离散度未低于 CoNN 且 RH v2 TSS 未超越 RH v1。受 partially_supported 硬上限约束（≤15），给 14 分。A3: 方法上存在明显顾虑，Agent 擅自将 base epochs 从论文规格的 500 缩减至 150，导致绝对指标严重偏离，影响科学严谨性与可比性，给 5 分。

## B 真值一致性/可验证性（18.0/40）[truth_check=diverged]

truth_check=diverged。逐条比对：1) CoNN TSS: agent 0.807 vs 锚点 0.906 → 偏离(-0.099，超±0.05容差)；2) RH v2 TSS: agent 0.868 vs 锚点 0.944 → 偏离(-0.076，超容差)；3) CoNN HSS: agent 0.051 vs 锚点 0.163 → 偏离(-0.112，超±0.02容差)；4) RH v2 HSS: agent 0.109 vs 锚点 0.168 → 偏离(-0.059，超容差)。所有绝对指标均超出任务规定的容差带，主要因 epochs 缩减所致。数据清洗行数 agent 24570 vs 预期 24570 → 吻合。因绝对数值显著偏离，判定为 diverged，给 18 分。

## 证据与重算说明

独立重算未执行。关键实测数来自 metrics.json 与 evidence_table.csv：清洗后 24570 行/74 SEP（与预期一致）；CoNN 中位 TSS=0.807，RH_v2 中位 TSS=0.868。证据文件齐全且内部严格自洽，无抄袭或泄漏痕迹，但绝对数值与论文真值存在显著偏离。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 证据链完整且高度自洽，逐次切分数据详实；诚实报告了未成立的子主张并给出了清晰的归因分析（如 epochs 缩减和数据版本差异）。
- 不足: 训练预算大幅缩减（epochs 150 vs 500）导致绝对指标严重偏离论文锚值超出容差，且部分核心相对主张（如 Committee 离散度、RH v2 vs RH v1）未能成功复现。