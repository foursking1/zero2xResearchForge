# PAPER_ANCHOR（私有）：bonjean_2002

> 论文：Diagnostic Model and Analysis of the Surface Currents in the Tropical Pacific Ocean
> 出处：Journal of Physical Oceanography, Volume 32, October 2002 (pp. 2938-2954)
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 26 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（numeric）Optimal depth-scale parameter H = 70 m determined by minimizing momentum balance

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | numeric | Optimal depth-scale parameter H should be approximately 70 m | 70 | abs 5 / —% |

### C02（figure）Equatorial momentum balance shows wind stress and pressure gradient compensation

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R02 | compare | Compare generated equatorial momentum balance figure against | — | abs — / —% |

### C03（numeric）Mean diagnostic velocity agrees with drifter field; STDD = 8 cm/s (zonal), 3 cm/

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R03 | numeric | Standard deviation of difference between modeled and drifter | 8.0 | abs — / 10.0% |
| R04 | numeric | Standard deviation of difference between modeled and drifter | 3.0 | abs — / 10.0% |
| R05 | compare | Compare generated mean velocity vector map against reference | — | abs — / —% |

### C04（figure）Diagnostic velocity from GCM fields is nearly identical to GCM velocity

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R06 | compare | Compare generated GCM velocity comparison figure against ref | — | abs — / —% |

### C05（trend）Diagnostic model reproduces SEC two-branch structure with reduced westward bias 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R07 | trend | Diagnostic model SEC two-branch structure in meridional prof | — | abs — / —% |
| R08 | compare | Compare generated meridional profile comparison figure again | — | abs — / —% |

### C06（figure）Seasonal cycle shows SEC reversal and NECC variations

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R09 | compare | Compare generated seasonal cycle velocity vector maps agains | — | abs — / —% |

### C07（figure）De-meaned seasonal fluctuations agree with DRCM in Hovmoller diagrams

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R10 | compare | Compare generated Hovmoller diagram figure against reference | — | abs — / —% |

### C08（numeric）TAO time series correlations 0.66, 0.76, 0.64, 0.62; reduced mean bias

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R11 | numeric | Correlation between model and TAO zonal velocity at 165E sho | 0.66 | abs 0.05 / —% |
| R12 | numeric | Correlation between model and TAO zonal velocity at 170W sho | 0.76 | abs 0.05 / —% |
| R13 | numeric | Correlation between model and TAO zonal velocity at 140W sho | 0.64 | abs 0.05 / —% |
| R14 | numeric | Correlation between model and TAO zonal velocity at 110W sho | 0.62 | abs 0.05 / —% |
| R15 | numeric | Mean bias (u_bar - u_TAO) at 140W should be approximately 0. | 0.11 | abs 0.03 / —% |
| R16 | numeric | Mean bias (u_bar - u_TAO) at 110W should be approximately 0. | 0.01 | abs 0.03 / —% |
| R17 | trend | Diagnostic model mean bias at 140W and 110W should be substa | — | abs — / —% |
| R18 | compare | Compare generated TAO time series figure against reference | — | abs — / —% |

### C09（numeric）EOF analysis yields explained variance >64%, Gaussian e-folding ~3.1 deg, PC-TAO

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R19 | numeric | First-mode EOF explained variance should exceed 64% at all f | 64.0 | abs 5.0 / 0% |
| R20 | numeric | EOF meridional profile Gaussian fit e-folding scale lambda s | 3.1 | abs 0.5 / —% |
| R21 | numeric | Correlation between EOF first-mode PC and TAO zonal current  | 0.67 | abs 0.05 / —% |
| R22 | numeric | Correlation between EOF first-mode PC and TAO zonal current  | 0.77 | abs 0.05 / —% |
| R23 | numeric | Correlation between EOF first-mode PC and TAO zonal current  | 0.66 | abs 0.05 / —% |
| R24 | numeric | Correlation between EOF first-mode PC and TAO zonal current  | 0.61 | abs 0.05 / —% |
| R25 | compare | Compare generated EOF analysis figure against reference | — | abs — / —% |

### C10（figure）ENSO velocity anomalies show current reversal and eastward flow

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R26 | compare | Compare generated ENSO anomaly figure against reference | — | abs — / —% |
