# PAPER_ANCHOR（私有）：2604.04915v1

> 论文：Exploring Expert Perspectives on Wearable-Triggered LLM Conversational Support for Daily Stress Management
> 出处：Interactive Health Conference (IH '26), July 05-08, 2026, Porto, Portugal (ACM)
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 14 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（exists）EmBot is a functional mobile application combining wearable-triggered stress det

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | exists | A mobile application implementing EmBot with four-stage inte | exists | abs — / —% |
| R02 | exists | The reproduction implements all four interaction stages: Det | — | abs — / —% |

### C02（exists）Semi-structured interviews with 15 mental health experts using EmBot surfaced de

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R04 | exists | Evidence that semi-structured interviews were conducted with | — | abs — / —% |

### C06（exists）Stress events were simulated during interviews for consistency across participan

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R03 | exists | The reproduction includes a mechanism to trigger simulated s | implemented | abs — / —% |

### C07（exists）Reflexive thematic analysis performed by two independent coders following Braun 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R09 | exists | Evidence of reflexive thematic analysis following Braun and  | — | abs — / —% |

### C09（numeric）Study parameters: 18 conducted, 15 usable interviews, 45-60 minute duration

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R05 | numeric | Number of usable interviews should be 15 (18 conducted, 3 ex | 15 | abs 0 / 0% |
| R06 | numeric | Each interview should last between 45-60 minutes | 52.5 | abs 7.5 / 14.3% |

### C10（numeric）Interview protocol: pre-probe (5-10 min background + 10-15 min views), post-prob

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R07 | numeric | Pre-probe phase total should be 15-25 minutes (background 5- | 20 | abs 5 / 25% |
| R08 | numeric | Post-probe phase total should be 30-40 minutes (interaction  | 35 | abs 5 / 14.3% |
