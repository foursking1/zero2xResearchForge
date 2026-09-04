# EVAL REPORT v7: 2602.13288_cloud_telemetry_ad

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 62.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 15.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **42.0** | 60 | A1: 核心交付物完整，包含metrics.json、evidence_table.csv、多组敏感性分析结果及可运行代码，得12分。A2: Agent正确识别了GRU全正但TCN/TSMixer亦全正，得出partially_supported结论，受结论级硬上限约束，A2给15分。A3: 方法严谨，严格遵循70/30时间切分与训练期校准，防泄漏声明清晰，提供多种子与严格阈值敏感性分析，得15分。 |
| B 真值一致性/可验证性 | 20.0 | 40 | truth_check=diverged | agent数 vs 锚点逐条比对：1. MS acr-1 GRU: Agent 30.74 vs 锚点 31.76 → 吻合（量级与正负号一致）；2. MS mm-rps TCN: Agent 15.56 vs 锚点 0.00 → 偏离（导致claim a唯一性不成立）；3. NAB artificialWithAnomaly GRU: Agent -12.57 vs 锚点 11.06 → 偏离（方向相反且|Δ|>15）；4. NAB realTraffic 最佳: Agent IF 56.12 vs 锚点 GRU 20.26 → 偏离（归属不同）。存在多处显著数值与方向偏离，truth_check判为diverged，给20分。 |

## A 核心结果达成度（42.0/60 = A1 12.0 + A2 15.0 + A3 15.0）

A1: 核心交付物完整，包含metrics.json、evidence_table.csv、多组敏感性分析结果及可运行代码，得12分。A2: Agent正确识别了GRU全正但TCN/TSMixer亦全正，得出partially_supported结论，受结论级硬上限约束，A2给15分。A3: 方法严谨，严格遵循70/30时间切分与训练期校准，防泄漏声明清晰，提供多种子与严格阈值敏感性分析，得15分。

## B 真值一致性/可验证性（20.0/40）[truth_check=diverged]

agent数 vs 锚点逐条比对：1. MS acr-1 GRU: Agent 30.74 vs 锚点 31.76 → 吻合（量级与正负号一致）；2. MS mm-rps TCN: Agent 15.56 vs 锚点 0.00 → 偏离（导致claim a唯一性不成立）；3. NAB artificialWithAnomaly GRU: Agent -12.57 vs 锚点 11.06 → 偏离（方向相反且|Δ|>15）；4. NAB realTraffic 最佳: Agent IF 56.12 vs 锚点 GRU 20.26 → 偏离（归属不同）。存在多处显著数值与方向偏离，truth_check判为diverged，给20分。

## 证据与重算说明

独立重算未执行。关键实测数（如MS GRU acr-1=30.7416，NAB realTraffic IF=56.121）均在evidence_table.csv与metrics.json中严格落盘，证据链完整且内部自洽，但与论文真值存在客观偏离。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 实验管线完整严谨，诚实报告了与论文锚值的差异（如TCN全正、GRU在NAB部分子组为负），未伪造或照抄论文数据。
- 不足: 受限于校准方法（网格搜索vs论文贝叶斯搜索），未能复现论文中部分模型得分为0或特定架构主导的精确数值，导致核心claim仅部分成立。