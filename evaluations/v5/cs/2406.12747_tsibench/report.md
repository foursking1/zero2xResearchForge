# EVAL REPORT v5: 2406.12747_tsibench

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 33.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **60.0** | 60 | A1: 核心交付物（代码、evidence_table、metrics.json、报告等）完整产出，符合任务明确要求，得12分。A2: 实测Linear均值0.2037，完美复现论文声称的效应与排序趋势（Linear<LOCF<Median<Mean），数值落入满分带，得33分。A3: 方法严谨，train-only标准化与掩码协议正确，提供独立校验脚本，可复现性极强，得15分。 |
| B 证据真实性/实际复现 | 40 | 40 | 证据等级为2（齐全自洽）。metrics.json与evidence_table.csv等实测证据文件齐全且内部数值严格一致。seed=42掩码点总数2385及Linear test MAE 0.2033249300539183与冻结协议参考值精确匹配（bit-for-bit）。提供verify_anchor.py校验脚本，证据链完整，无抄数行为，给满分40分。 |

## A 核心结果达成度（60.0/60 = A1 12.0 + A2 33.0 + A3 15.0）

A1: 核心交付物（代码、evidence_table、metrics.json、报告等）完整产出，符合任务明确要求，得12分。A2: 实测Linear均值0.2037，完美复现论文声称的效应与排序趋势（Linear<LOCF<Median<Mean），数值落入满分带，得33分。A3: 方法严谨，train-only标准化与掩码协议正确，提供独立校验脚本，可复现性极强，得15分。

## B 证据真实性/实际复现（40/40）

证据等级为2（齐全自洽）。metrics.json与evidence_table.csv等实测证据文件齐全且内部数值严格一致。seed=42掩码点总数2385及Linear test MAE 0.2033249300539183与冻结协议参考值精确匹配（bit-for-bit）。提供verify_anchor.py校验脚本，证据链完整，无抄数行为，给满分40分。

## 证据与重算说明

独立重算未执行，但基于提交物内部强一致性及校验脚本输出判定。关键实测数：seed=42掩码点2385，Linear MAE=0.2033249300539183，LOCF MAE=0.3024，Mean MAE=0.8713，Median MAE=0.8588，均与PAPER_ANCHOR辅助事实完美吻合。

## 结论

- **科学结论**: `supported`
- 亮点: 协议复现极其精确，与冻结参考协议bit-for-bit匹配；提供独立校验脚本，证据链完整且高度自洽；严格区分实测与论文引用值。
- 不足: 无明显弱点，提交物堪称L1层级科研复现的标杆范例。