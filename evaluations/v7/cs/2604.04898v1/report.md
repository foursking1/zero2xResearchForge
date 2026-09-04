# EVAL REPORT v7: 2604.04898v1

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 49.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 10.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **37.0** | 60 | A1: 核心交付物完整，包含 metrics.json、evidence_table.csv 及可运行代码，得 12 分。A2: 核心数值（40.0%, 56.9%等）未能通过本地计算复现，仅验证了数据集特征和部分定性趋势，结论为 partially_supported，得 10 分。A3: 方法严谨，诚实区分论文引用与本地计算，未编造数据，统计分析扎实，得 15 分。 |
| B 真值一致性/可验证性 | 12.0 | 40 | truth_check=unverified | agent数 5.433 (IMO-ProofBench local mean score) vs 锚点 40.0 (R01) → 无法对应（量纲与judge不同，未复现百分比）；agent数 5.506 (RC proxy mean score) vs 锚点 56.9 (R04/R07) → 无法对应（RSA未实现，仅用RC代理且分数为7分制）；agent数 0.3989 (RL reward mean) vs 锚点无直接数值对应 → unverified。核心指标均未在容差内吻合，属于 unverified，给 12 分。 |

## A 核心结果达成度（37.0/60 = A1 12.0 + A2 10.0 + A3 15.0）

A1: 核心交付物完整，包含 metrics.json、evidence_table.csv 及可运行代码，得 12 分。A2: 核心数值（40.0%, 56.9%等）未能通过本地计算复现，仅验证了数据集特征和部分定性趋势，结论为 partially_supported，得 10 分。A3: 方法严谨，诚实区分论文引用与本地计算，未编造数据，统计分析扎实，得 15 分。

## B 真值一致性/可验证性（12.0/40）[truth_check=unverified]

agent数 5.433 (IMO-ProofBench local mean score) vs 锚点 40.0 (R01) → 无法对应（量纲与judge不同，未复现百分比）；agent数 5.506 (RC proxy mean score) vs 锚点 56.9 (R04/R07) → 无法对应（RSA未实现，仅用RC代理且分数为7分制）；agent数 0.3989 (RL reward mean) vs 锚点无直接数值对应 → unverified。核心指标均未在容差内吻合，属于 unverified，给 12 分。

## 证据与重算说明

独立重算未执行。关键实测数：本地judge下IMO-ProofBench qed_nano_direct均分5.433/7，qed_nano_rc均分5.506/7；FineProofs-RL reward_mean为0.3989。Agent诚实标注了paper_reported与computed_local的区别，未将论文数字伪装成实测。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `unverified`
- 亮点: 极其严谨和诚实，明确区分了论文引用值与本地复现值，拒绝编造数字，统计分析扎实。
- 不足: 受限于本地环境和工具链，未能复现核心百分比指标和RSA scaffold，导致核心数值锚点全部落空。