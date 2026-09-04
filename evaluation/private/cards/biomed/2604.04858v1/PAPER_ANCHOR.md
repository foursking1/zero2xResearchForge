# PAPER_ANCHOR（私有）：2604.04858v1

> 论文：FairLogue: A Toolkit for Intersectional Fairness Analysis in Clinical Machine Learning Models
> 出处：arXiv:2604.04858v1
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 34 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（numeric）Logistic regression achieves AUROC=0.709 and accuracy=0.651 on All of Us data wi

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | numeric | Verify logistic regression model achieves AUROC=0.709 on tes | 0.709 | abs 0 / 5.0% |
| R02 | numeric | Verify logistic regression model achieves accuracy=0.651 on  | 0.651 | abs 0.02 / 0% |

### C02（numeric）Intersectional fairness gaps (DP=0.20, TPR gap=0.33, FPR gap=0.15) exceed single

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R03 | numeric | Verify intersectional demographic parity gap=0.20 (Table 2) | 0.20 | abs 0.02 / 0% |
| R04 | numeric | Verify intersectional equalized odds FPR gap=0.15 (Table 2) | 0.15 | abs 0.02 / 0% |
| R05 | numeric | Verify intersectional equalized odds TPR gap=0.33 (Table 2) | 0.33 | abs 0.03 / 0% |
| R06 | trend | Verify intersectional DP gap (0.20) exceeds race-only DP (0. | — | abs — / —% |
| R07 | trend | Verify intersectional TPR gap (0.33) exceeds race-only (0.08 | — | abs — / —% |
| R08 | trend | Verify intersectional FPR gap (0.15) exceeds race-only (0.10 | — | abs — / —% |

### C03（numeric）Per-group TPR/FPR values for 4 intersectional and 4 single-axis groups match pap

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R09 | numeric | Verify Black Female subgroup TPR=0.66 (Table 1) | 0.66 | abs 0.02 / 0% |
| R10 | numeric | Verify Black Male subgroup TPR=0.72 (Table 1) | 0.72 | abs 0.02 / 0% |
| R11 | numeric | Verify White Female subgroup TPR=0.78 (Table 1) | 0.78 | abs 0.02 / 0% |
| R12 | numeric | Verify White Male subgroup TPR=0.45 (Table 1) | 0.45 | abs 0.02 / 0% |
| R13 | numeric | Verify single-axis TPR values: Black=0.69, White=0.61, Femal | 0.69 | abs 0.02 / 0% |
| R14 | numeric | Verify single-axis FPR values: Black=0.40, White=0.30, Femal | 0.40 | abs 0.02 / 0% |

### C04（numeric）Counterfactual analysis u-values approach zero across all 6 aggregate metrics

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R15 | numeric | Verify 200 permutation-based null distribution iterations us | 200 | abs 0 / 0% |
| R16 | numeric | Verify maximum absolute u-value across all 6 aggregate metri | 0.0 | abs 0.05 / 0% |
| R17 | numeric | Verify average absolute u-value across all metrics is near z | 0.0 | abs 0.03 / 0% |
| R34 | figure | Figure 3: Counterfactual analysis density plots showing obse | — | abs — / —% |

### C05（numeric）Cohort: N=3880, 53.2% Female, 47.1% White, 18.7% outcome prevalence

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R18 | numeric | Verify glaucoma cohort contains 3,880 participants (before u | 3880 | abs 10 / 0% |
| R19 | numeric | Verify cohort is 53.2% Female | 53.2 | abs 1.0 / 0% |
| R20 | numeric | Verify cohort is 47.1% White | 47.1 | abs 1.0 / 0% |
| R21 | numeric | Verify 18.7% outcome prevalence (726/3880 received glaucoma  | 18.7 | abs 1.0 / 0% |

### C06（exists）FairLogue has three modular components in source code

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R22 | exists | Verify FairLogue toolkit has three distinct components (obse | 3 | abs — / —% |
| R23 | exists | Verify three component module files exist in FairLogue sourc | — | abs — / —% |

### C07（exists）56 predictor variables with race/gender as protected attributes

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R24 | numeric | Verify model uses 56 predictor variables from EHR data | 56 | abs 0 / 0% |
| R25 | exists | Verify race and gender are defined as protected attributes ( | ["race", "gender"] | abs — / —% |

### C08（numeric）Fairness threshold=0.1, u-values below threshold

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R26 | numeric | Verify prespecified fairness threshold of 0.1 used in Compon | 0.1 | abs 0 / 0% |
| R27 | trend | Verify all u-values are below the fairness threshold of 0.1, | — | abs — / —% |

### C09（numeric）Intersectional subgroup size percentages verified

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R28 | numeric | Verify White/Male subgroup is 31.5% of cohort | 31.5 | abs 1.0 / 0% |
| R29 | numeric | Verify White/Female subgroup is 28.0% of cohort | 28.0 | abs 1.0 / 0% |
| R30 | numeric | Verify Black/Female subgroup is 22.7% of cohort | 22.7 | abs 1.0 / 0% |
| R31 | numeric | Verify Black/Male subgroup is 17.9% of cohort | 17.9 | abs 1.0 / 0% |
| R32 | numeric | Verify minimum subgroup size filter applied (all groups n >= | 20 | abs 0 / 0% |

### C10（numeric）Train/test split ratio in 70-80%/20-30% range

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R33 | numeric | Verify train set size is 70-80% of cohort | 80.0 | abs 10.0 / 0% |
