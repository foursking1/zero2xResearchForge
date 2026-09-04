# EVAL REPORT v7: bonjean_2002

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 57.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 12.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **39.0** | 60 | A1(12): 核心交付物完整，包含代码、evidence_table.csv和metrics.json，机器可读结果齐全。A2(12): 核心定量指标如STDD（12.6/9.4 vs 8/3）和H_argmin（85 vs 70）显著偏离论文真值，仅TAO部分站点相关系数吻合，整体定性支持但定量未复现，受partially_supported约束给12分。A3(15): 方法极其严谨，敏锐发现冻结数据中风应力字段的换算异常并采用Large&Pond物理公式重算，逻辑sound且完全可复现。 |
| B 真值一致性/可验证性 | 18.0 | 40 | truth_check=diverged | truth_check=diverged。逐条比对：1) H_argmin: agent数 85.0 vs 锚点 70 (容差5) → 偏离；2) STDD u: agent数 12.64 vs 锚点 8.0 (容差10%) → 严重偏离；3) STDD v: agent数 9.44 vs 锚点 3.0 (容差10%) → 严重偏离；4) TAO corr 170W: agent数 0.758 vs 锚点 0.76 (容差0.05) → 吻合；5) TAO corr 165E: agent数 0.832 vs 锚点 0.66 (容差0.05) → 偏离；6) TAO corr 140W: agent数 0.509 vs 锚点 0.64 (容差0.05) → 偏离。多个核心定量指标超出容差带，判定为diverged。 |

## A 核心结果达成度（39.0/60 = A1 12.0 + A2 12.0 + A3 15.0）

A1(12): 核心交付物完整，包含代码、evidence_table.csv和metrics.json，机器可读结果齐全。A2(12): 核心定量指标如STDD（12.6/9.4 vs 8/3）和H_argmin（85 vs 70）显著偏离论文真值，仅TAO部分站点相关系数吻合，整体定性支持但定量未复现，受partially_supported约束给12分。A3(15): 方法极其严谨，敏锐发现冻结数据中风应力字段的换算异常并采用Large&Pond物理公式重算，逻辑sound且完全可复现。

## B 真值一致性/可验证性（18.0/40）[truth_check=diverged]

truth_check=diverged。逐条比对：1) H_argmin: agent数 85.0 vs 锚点 70 (容差5) → 偏离；2) STDD u: agent数 12.64 vs 锚点 8.0 (容差10%) → 严重偏离；3) STDD v: agent数 9.44 vs 锚点 3.0 (容差10%) → 严重偏离；4) TAO corr 170W: agent数 0.758 vs 锚点 0.76 (容差0.05) → 吻合；5) TAO corr 165E: agent数 0.832 vs 锚点 0.66 (容差0.05) → 偏离；6) TAO corr 140W: agent数 0.509 vs 锚点 0.64 (容差0.05) → 偏离。多个核心定量指标超出容差带，判定为diverged。

## 证据与重算说明

独立重算未执行。关键实测数均落盘于evidence_table.csv与metrics.json：H_argmin=85.0m，STDD_u=12.64cm/s，STDD_v=9.44cm/s，TAO相关系数0.83/0.76/0.51/0.46。数据源标记清晰，内部自洽，且明确区分了重算值与论文引用，无编造行为，但计算结果与论文真值存在显著偏离。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 方法论极其严谨，敏锐发现了冻结数据中风应力字段的换算异常并采用物理公式重算；对无法复现的指标和缺失数据诚实报告，学术诚信度高。
- 不足: 部分核心量化指标（如STDD和H的精确argmin）未能落在论文锚值的严格容差内，导致整体结论仅为partially_supported，定量复现失败。