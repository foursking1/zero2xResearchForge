# EVAL REPORT v7: 2604.04673v1

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 75.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 26.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **53.0** | 60 | A1: 完整交付metrics.json、evidence_table.csv及可运行代码，机器可读结果齐全(12分)。A2: 核心claim的MLE与BetaPrime风险严格匹配锚点，Fixed/Dropout的超幅趋势正确，但Horseshoe在p=100的绝对风险(157.1)偏离锚点(130.0)超容差，扣除部分分数(26分)。A3: 方法极其严谨，主动量化ESS崩溃与MC噪声，多seed与高精度复算确保稳健性(15分)。 |
| B 真值一致性/可验证性 | 22.0 | 40 | truth_check=diverged | agent数 5.0 vs 锚点 5.0 (R01 MLE p=5) → 吻合；agent数 50.0 vs 锚点 50.0 (R02 MLE p=50) → 吻合；agent数 4.994 vs 锚点 5.0 (R07 BetaPrime p=5) → 吻合；agent数 50.025 vs 锚点 50.0 (R08 BetaPrime p=50) → 吻合；agent数 157.1 vs 锚点 130.0 (R14 Horseshoe p=100 k=100, 容差15.0) → 偏离，超出容差上限145。因存在超容差项，truth_check判为diverged。 |

## A 核心结果达成度（53.0/60 = A1 12.0 + A2 26.0 + A3 15.0）

A1: 完整交付metrics.json、evidence_table.csv及可运行代码，机器可读结果齐全(12分)。A2: 核心claim的MLE与BetaPrime风险严格匹配锚点，Fixed/Dropout的超幅趋势正确，但Horseshoe在p=100的绝对风险(157.1)偏离锚点(130.0)超容差，扣除部分分数(26分)。A3: 方法极其严谨，主动量化ESS崩溃与MC噪声，多seed与高精度复算确保稳健性(15分)。

## B 真值一致性/可验证性（22.0/40）[truth_check=diverged]

agent数 5.0 vs 锚点 5.0 (R01 MLE p=5) → 吻合；agent数 50.0 vs 锚点 50.0 (R02 MLE p=50) → 吻合；agent数 4.994 vs 锚点 5.0 (R07 BetaPrime p=5) → 吻合；agent数 50.025 vs 锚点 50.0 (R08 BetaPrime p=50) → 吻合；agent数 157.1 vs 锚点 130.0 (R14 Horseshoe p=100 k=100, 容差15.0) → 偏离，超出容差上限145。因存在超容差项，truth_check判为diverged。

## 证据与重算说明

独立重算未执行。关键实测数：MLE p=5/50/100均为5.0/50.0/100.0；BetaPrime max risk为4.994/50.025/100.017；Horseshoe p=100 k=100为157.1。证据链完整，底层JSON与汇总表自洽。

## 结论

- **科学结论**: `supported`
- **可验证性**: `diverged`
- 亮点: 方法设计严密，主动识别并量化重要性采样ESS崩溃带来的MC噪声，通过高精度和多seed复测确保了结论的稳健性。
- 不足: Horseshoe在p=100时的MC采样数受限导致绝对风险值（157.1）与论文锚值（130.0）存在超容差偏离，数值精度可进一步提升。