# EVAL REPORT v5: 08_tapley_2004

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 69.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **41.0** | 60 | A1: 完整交付了代码、证据表、metrics和报告等核心产物，给12分。A2: 复现了GRACE>GLDAS等核心趋势，但部分关键数值（如cosine max、RMS及Amazon极值）超出容差，结论判定为partially_supported，受硬上限约束最高给15分，实际给14分。A3: 纯numpy实现球谐综合并与冻结数据进行了机器精度校验，方法严谨无泄漏，给15分。 |
| B 证据真实性/实际复现 | 28.0 | 40 | 证据等级为2（齐全自洽），提供了完整的metrics、evidence表及validation校验文件，证据链完整。但受partially_supported结论的硬上限约束，B维度最高不得超过28分，故给28分。 |

## A 核心结果达成度（41.0/60 = A1 12.0 + A2 14.0 + A3 15.0）

A1: 完整交付了代码、证据表、metrics和报告等核心产物，给12分。A2: 复现了GRACE>GLDAS等核心趋势，但部分关键数值（如cosine max、RMS及Amazon极值）超出容差，结论判定为partially_supported，受硬上限约束最高给15分，实际给14分。A3: 纯numpy实现球谐综合并与冻结数据进行了机器精度校验，方法严谨无泄漏，给15分。

## B 证据真实性/实际复现（28.0/40）

证据等级为2（齐全自洽），提供了完整的metrics、evidence表及validation校验文件，证据链完整。但受partially_supported结论的硬上限约束，B维度最高不得超过28分，故给28分。

## 证据与重算说明

独立重算未执行。关键实测数：GRACE cosine min -7.244, cosine max 1.653, sine max 9.122, Amazon April max 11.369。证据文件齐全，内部自洽，validation_summary证明代码与冻结网格误差在1e-14级别。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 方法极其严谨，纯numpy实现球谐综合并达到机器精度校验；对数据版本差异导致的数值偏离给出了诚实且合理的解释。
- 不足: 部分全球RMS和极值与论文锚值偏离较大，未能完全对齐论文的14个月窗口，导致多个核心数值指标超出容差带。