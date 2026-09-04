# EVAL REPORT v5: gehlen_2019

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 69.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **41.0** | 60 | A1(12): 完整产出了TASK要求的所有核心交付物，包括solution.md、可运行代码、evidence_table和metrics.json，代码结构清晰。A2(14): Agent诚实反映了计算结果与论文的差异，准确给出了partially_supported和inconclusive的结论，科学分析保真；受partially_supported硬上限约束（A2≤15），给14分。A3(15): 方法严谨，严格使用冻结数据，无泄漏，额外进行了敏感性分析验证鲁棒性，可复现性强。 |
| B 证据真实性/实际复现 | 28.0 | 40 | 磁盘证据扫描显示证据等级为2（齐全自洽），提供了详尽的evidence_table和metrics.json，包含13个中间结果CSV，数据内部高度自洽。但受partially_supported结论硬上限约束（B≤28），故给28分。 |

## A 核心结果达成度（41.0/60 = A1 12.0 + A2 14.0 + A3 15.0）

A1(12): 完整产出了TASK要求的所有核心交付物，包括solution.md、可运行代码、evidence_table和metrics.json，代码结构清晰。A2(14): Agent诚实反映了计算结果与论文的差异，准确给出了partially_supported和inconclusive的结论，科学分析保真；受partially_supported硬上限约束（A2≤15），给14分。A3(15): 方法严谨，严格使用冻结数据，无泄漏，额外进行了敏感性分析验证鲁棒性，可复现性强。

## B 证据真实性/实际复现（28.0/40）

磁盘证据扫描显示证据等级为2（齐全自洽），提供了详尽的evidence_table和metrics.json，包含13个中间结果CSV，数据内部高度自洽。但受partially_supported结论硬上限约束（B≤28），故给28分。

## 证据与重算说明

独立重算未执行。关键实测数：LVI范围2.0-3.5（论文2-2.5），LFA 41 CM2.6 LVI=3.5（论文2.0），CM2.6 bottom-temp change mean=1.5234。Agent明确指出BNAM 2055数据缺失导致C02无法验证，所有指标均有落盘CSV/JSON支撑。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 对数据缺失和计算偏差进行了极其诚实和详尽的分析，敏感性分析显著增强了结果的可信度与科学严谨性，证据链完整且高度自洽。
- 不足: 受限于冻结数据的不完整，未能完全复现论文的核心数值（如LFA 41的LVI），且C02的投影对比因数据缺失无法验证。