# EVAL REPORT v5: bonjean_2002

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 69.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **41.0** | 60 | A1(12): 核心交付物完整，包含代码、报告、evidence表和metrics.json，无缺失。A2(14): 科学结论部分成立。C01的H最优值实测85m偏离锚值70m（容差5），C03的STDD实测12.6/9.4显著偏离锚值8/3，定量未复现；但Agent准确指出了数据本身的异常并做了合理的定性分析，受partially_supported硬上限约束给14分。A3(15): 方法极其严谨，敏锐发现冻结数据中风应力的2pi换算错误并采用Large&Pond公式重算，进行了敏感性分析，逻辑sound且完全可复现。 |
| B 证据真实性/实际复现 | 28.0 | 40 | 证据等级为2（齐全自洽），提交了完整的metrics.json和evidence_table.csv，明确区分了重算值、参考artifact和论文引用，无编造行为。但受partially_supported结论硬上限约束，B维度最高不超过28分，故给28分。 |

## A 核心结果达成度（41.0/60 = A1 12.0 + A2 14.0 + A3 15.0）

A1(12): 核心交付物完整，包含代码、报告、evidence表和metrics.json，无缺失。A2(14): 科学结论部分成立。C01的H最优值实测85m偏离锚值70m（容差5），C03的STDD实测12.6/9.4显著偏离锚值8/3，定量未复现；但Agent准确指出了数据本身的异常并做了合理的定性分析，受partially_supported硬上限约束给14分。A3(15): 方法极其严谨，敏锐发现冻结数据中风应力的2pi换算错误并采用Large&Pond公式重算，进行了敏感性分析，逻辑sound且完全可复现。

## B 证据真实性/实际复现（28.0/40）

证据等级为2（齐全自洽），提交了完整的metrics.json和evidence_table.csv，明确区分了重算值、参考artifact和论文引用，无编造行为。但受partially_supported结论硬上限约束，B维度最高不超过28分，故给28分。

## 证据与重算说明

独立重算未执行。关键实测数均落盘于evidence_table.csv与metrics.json：H_argmin=85.0m（论文70m），STDD_u=12.64cm/s（论文8.0），STDD_v=9.44cm/s（论文3.0），TAO相关系数0.83/0.76/0.51/0.46。数据源标记清晰，内部自洽。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 方法论极其严谨，敏锐发现了冻结数据中风应力字段的换算异常并采用物理公式重算；对无法复现的指标和缺失数据诚实报告，学术诚信度高。
- 不足: 部分核心量化指标（如STDD和H的精确argmin）未能落在论文锚值的严格容差内，导致整体结论仅为partially_supported。