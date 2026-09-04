# EVAL REPORT v7: 08_tapley_2004

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 60.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 13.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **40.0** | 60 | A1: 交付了完整的代码、metrics.json、evidence_table.csv等核心产物，机器可读结果齐全，给12分。A2: 结论判定为partially_supported，受硬上限约束A2≤15。复现了部分指标和定性趋势，但多个核心数值偏离锚点，给13分。A3: 纯numpy实现球谐综合，与冻结网格校验达到机器精度，方法严谨且对数据版本差异有诚实分析，给15分。 |
| B 真值一致性/可验证性 | 20.0 | 40 | truth_check=diverged | 真值比对：R01 agent -7.244 vs 锚点 -7.2 → 吻合；R02 agent 1.653 vs 锚点 3.0 → 偏离(超容差0.3)；R03 agent 0.592 vs 锚点 0.9 → 偏离(超容差0.1)；R08 agent 2.254 vs 锚点 3.2 → 偏离(超容差0.3)；R13 agent 11.369 vs 锚点 14.0 → 偏离(超容差1.0)；R17 agent 2.146 vs 锚点 2.5 → 吻合。由于多个关键极值和RMS指标明显偏离锚点容差带，判定为diverged。 |

## A 核心结果达成度（40.0/60 = A1 12.0 + A2 13.0 + A3 15.0）

A1: 交付了完整的代码、metrics.json、evidence_table.csv等核心产物，机器可读结果齐全，给12分。A2: 结论判定为partially_supported，受硬上限约束A2≤15。复现了部分指标和定性趋势，但多个核心数值偏离锚点，给13分。A3: 纯numpy实现球谐综合，与冻结网格校验达到机器精度，方法严谨且对数据版本差异有诚实分析，给15分。

## B 真值一致性/可验证性（20.0/40）[truth_check=diverged]

真值比对：R01 agent -7.244 vs 锚点 -7.2 → 吻合；R02 agent 1.653 vs 锚点 3.0 → 偏离(超容差0.3)；R03 agent 0.592 vs 锚点 0.9 → 偏离(超容差0.1)；R08 agent 2.254 vs 锚点 3.2 → 偏离(超容差0.3)；R13 agent 11.369 vs 锚点 14.0 → 偏离(超容差1.0)；R17 agent 2.146 vs 锚点 2.5 → 吻合。由于多个关键极值和RMS指标明显偏离锚点容差带，判定为diverged。

## 证据与重算说明

独立重算未执行。关键实测数：GRACE cosine min -7.244, cosine max 1.653, RMS 0.592; Amazon April max 11.369。证据文件齐全，内部自洽，validation_summary证明代码与冻结网格误差在1e-14级别，但部分计算结果与论文真值存在显著偏差。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 方法极其严谨，纯numpy实现球谐综合并达到机器精度校验；对数据版本差异（RL06 vs RL01）导致的数值偏离给出了诚实且合理的解释。
- 不足: 部分全球RMS和极值（如GRACE cosine max, Amazon April max）与论文锚值偏离较大，未能完全对齐论文的14个月窗口，导致多个核心数值指标超出容差带。