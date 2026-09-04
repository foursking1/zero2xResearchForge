# PAPER_ANCHOR（私有）：2604.04518v1

> 论文：Reproducibility study on how to find Spurious Correlations, Shortcut Learning, Clever Hans or Group-Distributional non-robustness and how to fix them
> 出处：arXiv:2604.04518v1 [cs.LG], April 2026
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 15 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（numeric）Uncorrected ERM-trained student models on poisoned datasets achieve high empiric

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | numeric | Uncorrected ERM student on Squares symmetric should achieve  | 51.1 | abs 2.5 / 5.0% |
| R02 | numeric | Uncorrected ERM student on Squares symmetric should achieve  | 1.8 | abs 0.5 / 5.0% |
| R03 | trend | For all 9 uncorrected ERM students, empirical accuracy shoul | — | abs — / —% |

### C02（trend）XAI-based correction methods (P-ClArC, RR-ClArC, CFKD) generally outperform non-

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R04 | trend | XAI-based correction methods (CFKD, P-ClArC, RR-ClArC) shoul | — | abs — / —% |

### C03（trend）CFKD achieves the highest AGA in 6 of 9 datasets and ranks second in 2 more, pro

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R05 | trend | CFKD should achieve the highest or second-highest AGA across | — | abs — / —% |

### C04（trend）When using SpRAy-derived group labels instead of ground truth, correction perfor

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R06 | trend | Correction methods using SpRAy-derived labels should achieve | — | abs — / —% |
| R07 | trend | CFKD should achieve similar AGA in both Table 2 (ground-trut | — | abs — / —% |

### C05（numeric）SpRAy label quality degrades as confounder complexity increases: near-perfect fo

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R08 | numeric | SpRAy label accuracy for Squares should be near-perfect (clo | 100.0 | abs 5.0 / 5.0% |
| R09 | numeric | SpRAy label accuracy for CelebA Blond minority groups should | 20.0 | abs 10.0 / 5.0% |
| R10 | trend | SpRAy label accuracy should decrease as confounder complexit | — | abs — / —% |

### C06（figure）The severity of Clever Hans effect varies with dataset complexity: simpler confo

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R11 | figure | Decision boundary plots for uncorrected Squares students sho | — | abs — / —% |

### C07（figure）For P-ClArC, the optimal projection layer l varies across datasets and between s

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R12 | figure | Line plot showing P-ClArC AGA vs projection layer (0-12) for | — | abs — / —% |

### C08（figure）Validation AGA is an unreliable estimator for test AGA in data-scarce settings, 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R13 | figure | Paired bar charts showing top-20 RR-ClArC models ranked by v | — | abs — / —% |

### C09（numeric）DFR achieves only modest AGA improvements, often limited by accuracy saturation 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R14 | trend | DFR-corrected AGA should show only modest improvement over u | — | abs — / —% |

### C10（trend）Group DRO generally outperforms DFR but underperforms XAI-based methods, with mo

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R15 | trend | Group DRO should achieve AGA between DFR and XAI-based metho | — | abs — / —% |
