# PAPER_ANCHOR（私有）：pages2k_2019

> 论文：Consistent multidecadal variability in global temperature reconstructions and simulations over the Common Era
> 出处：Nature Geoscience, 2019 (doi: 10.1038/s41561-019-0400-0)
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 37 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（numeric）Seven reconstruction methods produce coherent 2000-year GMST reconstructions wit

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | numeric | Median pre-industrial cooling rate for methods with lower-th | -0.23 | abs 0.08 / 0.0% |
| R02 | numeric | Median pre-industrial cooling rate for methods with annual r | -0.09 | abs 0.09 / 0.0% |
| R03 | numeric | Fraction of ensemble members with warmest 10-year period in  | 0.94 | abs 0.05 / 0.0% |
| R04 | numeric | Temperature difference between warmest method (DA) and colde | 0.5 | abs 0.1 / 0.0% |
| R05 | exists | Anomaly reference period must be 1961-1990 CE | 1961-1990 | abs — / —% |

### C02（figure）Bandpass-filtered (30-200 yr) GMST shows tighter agreement across methods with c

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R06 | figure | Figure 1b: 30-200 yr bandpass-filtered GMST reconstruction e | — | abs — / —% |

### C03（numeric）Model/data variance ratios close to 1 (median 1.01) and significant correlations

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R07 | numeric | CPS method variance ratio median (model/data) should be appr | 0.96 | abs 0.05 / 0.0% |
| R08 | numeric | PCR method variance ratio median should be approximately 1.0 | 1.01 | abs 0.05 / 0.0% |
| R09 | numeric | OIE method variance ratio median should be approximately 1.1 | 1.13 | abs 0.05 / 0.0% |
| R10 | numeric | M08 method variance ratio median should be approximately 1.0 | 1.01 | abs 0.05 / 0.0% |
| R11 | numeric | PAI method variance ratio median should be approximately 0.6 | 0.63 | abs 0.05 / 0.0% |
| R12 | numeric | BHM method variance ratio median should be approximately 1.1 | 1.12 | abs 0.05 / 0.0% |
| R13 | numeric | DA method variance ratio median should be approximately 1.15 | 1.15 | abs 0.05 / 0.0% |
| R14 | numeric | Overall median variance ratio across all 7 methods should be | 1.01 | abs 0.05 / 0.0% |
| R15 | numeric | CPS method model-data correlation median should be approxima | 0.64 | abs 0.03 / 0.0% |
| R16 | numeric | PCR method model-data correlation median should be approxima | 0.6 | abs 0.03 / 0.0% |
| R17 | numeric | OIE method model-data correlation median should be approxima | 0.61 | abs 0.03 / 0.0% |
| R18 | numeric | M08 method model-data correlation median should be approxima | 0.65 | abs 0.03 / 0.0% |
| R19 | numeric | PAI method model-data correlation median should be approxima | 0.63 | abs 0.03 / 0.0% |
| R20 | numeric | BHM method model-data correlation median should be approxima | 0.53 | abs 0.03 / 0.0% |
| R21 | numeric | DA method model-data correlation median should be approximat | 0.62 | abs 0.03 / 0.0% |
| R22 | trend | All 7 methods must have more than 95% of ensemble members wi | — | abs — / —% |

### C05（numeric）Unforced variability from D&A residuals consistent with control simulation varia

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R27 | numeric | Percentage of D&A residual-based unforced variability estima | 0.99 | abs 0.04 / 0.0% |
| R28 | numeric | D&A residual amplitude should be in the range of approximate | 0.045 | abs 0.025 / 0.0% |
| R29 | numeric | Number of D&A estimates should be exactly 7000 | 7000 | abs 0 / 0.0% |
| R30 | numeric | Number of control run estimates should be exactly 43 | 43 | abs 0 / 0.0% |

### C06（numeric）51-yr running trends: 79% largest in 20th century, instrumental after 1948 excee

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R31 | numeric | Fraction of ensemble members with largest 51-year trend in t | 0.79 | abs 0.03 / 0.0% |
| R32 | numeric | Trend window length should be exactly 51 years | 51 | abs 0 / 0.0% |
| R33 | numeric | Total number of ensemble members should be exactly 7000 (7 m | 7000 | abs 0 / 0.0% |
| R34 | figure | Figure 4a: 51-year running linear GMST trends over the Commo | — | abs — / —% |

### C07（trend）Trend probability after 1850 exceeds AR-noise and random baselines for timescale

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R35 | figure | Figure 4b: Ensemble probability that the largest trend occur | — | abs — / —% |
| R36 | trend | For trend lengths longer than approximately 20 years, the re | — | abs — / —% |
| R37 | trend | For trend lengths longer than approximately 20 years, the re | — | abs — / —% |
