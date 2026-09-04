# EVAL REPORT v7: gehlen_2019

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 59.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **41.0** | 60 | A1(12): 完整产出了TASK要求的所有核心交付物，包括solution.md、可运行代码、evidence_table和metrics.json，机器可读结果完整。A2(14): Agent诚实反映了计算结果与论文真值的差异，准确给出了partially_supported和inconclusive的结论，科学分析保真；受partially_supported硬上限约束（A2≤15），给14分。A3(15): 方法严谨，严格使用冻结数据，无泄漏，额外进行了敏感性分析验证鲁棒性，代码结构清晰可复现。 |
| B 真值一致性/可验证性 | 18.0 | 40 | truth_check=diverged | agent数 vs 锚点逐条比对：1. LVI range: agent 2.0-3.5 vs 锚点 2-2.5 (R14) → 偏离；2. LFA 33 LVI: agent 2.5 vs 锚点 2.0 (R15) → 偏离；3. LFA 34 LVI: agent 2.0 vs 锚点 2.0 (R16) → 吻合；4. LFA 38 LVI: agent 2.5 vs 锚点 2.0 (R17) → 偏离；5. LFA 35 LVI: agent 2.5 vs 锚点 2.5 (R18) → 吻合；6. LFA 36 LVI: agent 2.5 vs 锚点 2.5 (R19) → 吻合；7. LFA 41 CM2.6 LVI: agent 3.5 vs 锚点 2.0 (R21) → 偏离；8. LFA 41 BNAM LVI: agent 无法计算 vs 锚点 2.5 (R20) → 无法核对；9. C02 投影对比: agent 数据缺失无法比较 vs 锚点 R35/R36 → 无法核对。综合判定为 diverged（部分吻合，部分显著偏离，部分缺失），B给18分。 |

## A 核心结果达成度（41.0/60 = A1 12.0 + A2 14.0 + A3 15.0）

A1(12): 完整产出了TASK要求的所有核心交付物，包括solution.md、可运行代码、evidence_table和metrics.json，机器可读结果完整。A2(14): Agent诚实反映了计算结果与论文真值的差异，准确给出了partially_supported和inconclusive的结论，科学分析保真；受partially_supported硬上限约束（A2≤15），给14分。A3(15): 方法严谨，严格使用冻结数据，无泄漏，额外进行了敏感性分析验证鲁棒性，代码结构清晰可复现。

## B 真值一致性/可验证性（18.0/40）[truth_check=diverged]

agent数 vs 锚点逐条比对：1. LVI range: agent 2.0-3.5 vs 锚点 2-2.5 (R14) → 偏离；2. LFA 33 LVI: agent 2.5 vs 锚点 2.0 (R15) → 偏离；3. LFA 34 LVI: agent 2.0 vs 锚点 2.0 (R16) → 吻合；4. LFA 38 LVI: agent 2.5 vs 锚点 2.0 (R17) → 偏离；5. LFA 35 LVI: agent 2.5 vs 锚点 2.5 (R18) → 吻合；6. LFA 36 LVI: agent 2.5 vs 锚点 2.5 (R19) → 吻合；7. LFA 41 CM2.6 LVI: agent 3.5 vs 锚点 2.0 (R21) → 偏离；8. LFA 41 BNAM LVI: agent 无法计算 vs 锚点 2.5 (R20) → 无法核对；9. C02 投影对比: agent 数据缺失无法比较 vs 锚点 R35/R36 → 无法核对。综合判定为 diverged（部分吻合，部分显著偏离，部分缺失），B给18分。

## 证据与重算说明

独立重算未执行。关键实测数：LVI范围2.0-3.5，LFA 41 CM2.6 LVI=3.5，CM2.6 bottom-temp change mean=1.5234。Agent明确指出BNAM 2055数据缺失导致C02无法验证，所有指标均有落盘CSV/JSON支撑，证据链完整且高度自洽。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 对数据缺失和计算偏差进行了极其诚实和详尽的分析，敏感性分析显著增强了结果的可信度与科学严谨性，证据链完整。
- 不足: 受限于冻结数据的不完整或中间结果差异，未能复现论文的核心LVI数值（如LFA 41、33、38），且C02的投影对比因数据缺失完全无法验证。