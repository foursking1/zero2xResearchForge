# PAPER_ANCHOR（私有）：2604.04673v1

> 论文：Minimaxity and Admissibility of Bayesian Neural Networks
> 出处：arXiv:2604.04673v1 [math.ST], April 2026
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 22 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（figure）At p=5, fixed-scale BNN risk exceeds minimax level p for large \|\|theta\|\|, wh

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R04 | trend | At p=5 and large \ | — | abs — / —% |
| R07 | numeric | BetaPrime BNN maximum risk at p=5 should stay within 10% of  | 5.0 | abs 0.5 / 10.0% |
| R10 | numeric | Fixed-scale BNN risk at p=5 for large \ | — | abs — / —% |
| R17 | figure | Figure 1: Risk comparison plot at p=5 showing four decision  | — | abs — / —% |

### C02（figure）At p=50, fixed-scale BNN and dropout BNN risks exceed minimax level p, while Bet

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R05 | trend | At p=50 and large \ | — | abs — / —% |
| R08 | numeric | BetaPrime BNN maximum risk at p=50 should stay within 10% of | 50.0 | abs 5.0 / 10.0% |
| R18 | figure | Figure 2: Risk comparison plot at p=50 showing four decision | — | abs — / —% |

### C03（figure）At p=100, fixed-scale BNN and dropout BNN risks exceed minimax, BetaPrime remain

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R06 | trend | At p=100 and large \ | — | abs — / —% |
| R09 | numeric | BetaPrime BNN maximum risk at p=100 should stay within 10% o | 100.0 | abs 10.0 / 10.0% |
| R19 | figure | Figure 3: Risk comparison plot at p=100 showing four decisio | — | abs — / —% |

### C04（figure）At p=5, BetaPrime risk depends only on \|\|theta\|\| and stays near p; Horseshoe

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R11 | trend | At p=5, Horseshoe risk should vary across sparsity levels k= | — | abs — / —% |
| R15 | numeric | BetaPrime BNN risk at p=5 depends only on \ | — | abs — / —% |
| R20 | figure | Figure 4: Sparsity risk comparison at p=5 showing MLE, BetaP | — | abs — / —% |

### C05（figure）At p=50, BetaPrime risk near minimax while Horseshoe risk diverges across sparsi

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R12 | trend | At p=50, Horseshoe risk should vary significantly across spa | — | abs — / —% |
| R21 | figure | Figure 5: Sparsity risk comparison at p=50 showing MLE, Beta | — | abs — / —% |

### C06（figure）At p=100, BetaPrime risk near minimax; Horseshoe at k=100 reaches approximately 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R13 | trend | At p=100, Horseshoe risk should vary dramatically across spa | — | abs — / —% |
| R14 | numeric | At p=100 and k=100, Horseshoe risk reaches approximately 130 | 130.0 | abs 15.0 / 15.0% |
| R16 | numeric | Maximum Horseshoe risk at p=100 should exceed minimax level  | 100.0 | abs 0.0 / 0.0% |
| R22 | figure | Figure 6: Sparsity risk comparison at p=100 showing MLE, Bet | — | abs — / —% |

### C07（numeric）MLE risk estimate equals p (minimax risk) across all dimensions p=5,50,100

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | numeric | MLE risk at p=5 should equal the minimax level of 5 | 5.0 | abs 0.5 / 10.0% |
| R02 | numeric | MLE risk at p=50 should equal the minimax level of 50 | 50.0 | abs 5.0 / 10.0% |
| R03 | numeric | MLE risk at p=100 should equal the minimax level of 100 | 100.0 | abs 10.0 / 10.0% |
