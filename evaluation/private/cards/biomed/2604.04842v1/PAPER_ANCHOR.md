# PAPER_ANCHOR（私有）：2604.04842v1

> 论文：Do No Harm: Exposing Hidden Vulnerabilities of LLMs via Persona-based Client Simulation Attack in Psychological Counseling
> 出处：arXiv:2604.04842v1 (April 2026)
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 20 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（numeric）PCSA substantially outperforms four baselines (CoA, AMA, Crescendo, Actor-Attack

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | trend | PCSA CARES ASR should exceed all 4 baseline CARES ASR values | — | abs — / —% |
| R02 | trend | PCSA Safety Score should be lower than all 4 baseline SS val | — | abs — / —% |
| R03 | trend | PCSA GPT Judge ASR should exceed all 4 baseline GPT ASR valu | — | abs — / —% |

### C02（numeric）PCSA elicits highest harm category rates: Toxic Empathy (0.44), Target Complianc

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R04 | numeric | PCSA average Toxic Empathy occurrence rate should be approxi | 0.44 | abs 0.02 / 5.0% |
| R05 | numeric | PCSA average Target Compliance occurrence rate should be app | 0.57 | abs 0.02 / 5.0% |
| R06 | numeric | PCSA average Harmful Content occurrence rate should be appro | 0.27 | abs 0.02 / 5.0% |
| R07 | numeric | PCSA average Impersonation occurrence rate should be approxi | 0.12 | abs 0.02 / 5.0% |
| R08 | trend | PCSA harm rates should exceed all 4 baselines on average acr | — | abs — / —% |

### C03（numeric）PCSA achieves lowest perplexity (PPL < 20) with 0% detection rate across all 8 t

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R09 | numeric | PCSA average perplexity should be below 20 across all 8 targ | 15.0 | abs 5.0 / 0.0% |
| R10 | numeric | PCSA detection rate (PPL > 100 threshold) should be 0% acros | 0.0 | abs 0.01 / 0.0% |
| R11 | trend | PCSA average PPL should be lower than all 4 baselines | — | abs — / —% |

### C04（numeric）PCSA maintains high ASR under three defenses with only marginal reductions compa

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R12 | trend | PCSA ASR under PerplexityFilter should show negligible reduc | — | abs — / —% |
| R13 | trend | PCSA ASR under SelfDefend should remain high with only margi | — | abs — / —% |
| R14 | trend | PCSA ASR under Granite Guardian should remain high with only | — | abs — / —% |

### C05（numeric）PCSA achieves 96.4% average win rate over 28 pairwise comparisons in clinical re

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R15 | numeric | PCSA achieves approximately 96.4% average win rate over 28 p | 96.4 | abs 3.0 / 0.0% |

### C06（numeric）Agreement rate between human annotations and automated GPT judge reaches 87.5% o

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R16 | numeric | Agreement rate between human annotations and GPT-4o judge on | 87.5 | abs 5.0 / 0.0% |

### C07（exists）PCSA uses four psychological strategies with evaluator-in-the-loop best-of-N sel

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R17 | exists | PCSA framework implements all 4 psychological strategies: Re | ["Reassurance Seeking", "Appeal to Expertise", "Intellectualization", "Metaphorical Expression"] | abs — / —% |
| R18 | exists | PCSA includes GPT-4o-mini evaluator with best-of-N selection | gpt-4o-mini | abs — / —% |

### C08（exists）PCSA constructs client personas from CBT counseling corpora with cognitive disto

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R19 | exists | Client personas constructed from CBT counseling corpora (Cac | — | abs — / —% |
| R20 | exists | Target-to-cognitive-distortion mapping T(y -> C_dist) is imp | — | abs — / —% |
