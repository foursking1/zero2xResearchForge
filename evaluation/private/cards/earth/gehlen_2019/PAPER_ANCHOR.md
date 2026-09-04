# PAPER_ANCHOR（私有）：gehlen_2019

> 论文：A framework for assessing climate change impacts on shared fisheries resources and dependent coastal communities
> 出处：Frontiers in Marine Science, 2019 (doi: 10.3389/fmars.2019.00579)
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 36 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C03（numeric）LVI scores per LFA range from 2 to 2.5; LFA 41 scores 2.5 (BNAM) / 2 (CM2.6); no

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R13 | compare | Compare generated vulnerability sub-index boxplots against r | — | abs — / —% |
| R14 | numeric | LVI scores across all LFAs should range from 2 to 2.5 | 2.5 | abs 0.25 / 0.0% |
| R15 | numeric | LFA 33 LVI score should be 2 (lowest) | 2.0 | abs 0.25 / 0.0% |
| R16 | numeric | LFA 34 LVI score should be 2 (lowest) | 2.0 | abs 0.25 / 0.0% |
| R17 | numeric | LFA 38 LVI score should be 2 (lowest) | 2.0 | abs 0.25 / 0.0% |
| R18 | numeric | LFA 35 LVI score should be 2.5 (highest) | 2.5 | abs 0.25 / 0.0% |
| R19 | numeric | LFA 36 LVI score should be 2.5 (highest) | 2.5 | abs 0.25 / 0.0% |
| R20 | numeric | LFA 41 LVI score under BNAM scenario should be 2.5 | 2.5 | abs 0.25 / 0.0% |
| R21 | numeric | LFA 41 LVI score under CM2.6 scenario should be 2 | 2.0 | abs 0.25 / 0.0% |

### C06（trend）BNAM and CM2.6 bottom temperature projections show similar spatial patterns but 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R35 | trend | BNAM and CM2.6 bottom temperature projections should show si | — | abs — / —% |
| R36 | trend | CM2.6 should predict larger temperature changes than BNAM (g | — | abs — / —% |
