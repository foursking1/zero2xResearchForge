# EVAL REPORT v7: 2604.04930v1

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 54.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 12.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **39.0** | 60 | A1(12分)：核心交付物完整，包含metrics.json、evidence_table.csv及可运行代码，机器可读结果齐全。A2(12分)：结论判定为partially_supported，受硬上限约束（≤15）。Agent如实反映了冻结数据下CR未稳定达到50-75%、correct tokens远低于锚点的事实，未强行迎合论文，给12分。A3(15分)：方法严谨，代码从原始JSONL逐条重算，清晰区分scisolve与repro数据，无数据泄漏，诚实指出截断与样本量局限。 |
| B 真值一致性/可验证性 | 15.0 | 40 | truth_check=diverged | 1. R01 (CR): agent数 47.01% (scisolve AIME) / 最高62.47% (repro AIME thr0.70) vs 锚点 62.5 (容差50-75%) → 偏离（大部分阈值及数据集低于50%下限）。2. R10 (Correct tokens): agent数 5662.8 (scisolve) / 1333.3 (repro) vs 锚点 25000 → 严重偏离（受限于冻结数据max_tokens=8192截断，量级不匹配）。3. R19/R21/R22: agent未报告B=16K及delimiter差异 → 无法核对(unverified)。因关键指标与真值客观偏离，truth_check判为diverged。 |

## A 核心结果达成度（39.0/60 = A1 12.0 + A2 12.0 + A3 15.0）

A1(12分)：核心交付物完整，包含metrics.json、evidence_table.csv及可运行代码，机器可读结果齐全。A2(12分)：结论判定为partially_supported，受硬上限约束（≤15）。Agent如实反映了冻结数据下CR未稳定达到50-75%、correct tokens远低于锚点的事实，未强行迎合论文，给12分。A3(15分)：方法严谨，代码从原始JSONL逐条重算，清晰区分scisolve与repro数据，无数据泄漏，诚实指出截断与样本量局限。

## B 真值一致性/可验证性（15.0/40）[truth_check=diverged]

1. R01 (CR): agent数 47.01% (scisolve AIME) / 最高62.47% (repro AIME thr0.70) vs 锚点 62.5 (容差50-75%) → 偏离（大部分阈值及数据集低于50%下限）。2. R10 (Correct tokens): agent数 5662.8 (scisolve) / 1333.3 (repro) vs 锚点 25000 → 严重偏离（受限于冻结数据max_tokens=8192截断，量级不匹配）。3. R19/R21/R22: agent未报告B=16K及delimiter差异 → 无法核对(unverified)。因关键指标与真值客观偏离，truth_check判为diverged。

## 证据与重算说明

独立重算未执行。关键实测数如CR 47.01%、correct tokens 5662.8均来自agent提供的metrics_scisolve.json与evidence_table.csv，代码逻辑支持这些数字的生成，无编造或抄袭论文锚值痕迹，但与论文真值存在客观偏离。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 科学态度极佳，诚实揭示了冻结数据在max_tokens截断和样本量上的局限性，未强行篡改数据以迎合论文结论。
- 不足: 受限于冻结数据规模与截断，核心指标（如CR和correct tokens）未能复现论文真值，多个claim只能判定为partially_supported或inconclusive。