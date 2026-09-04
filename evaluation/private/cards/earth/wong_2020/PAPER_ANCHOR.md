# PAPER_ANCHOR（私有）：wong_2020

> 论文：Phytoplankton Growth and Productivity in the Western North Atlantic: Observations of Regional Variability From the NAAMES Field Campaigns
> 出处：Frontiers in Marine Science, Volume 7, Article 24, February 2020
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 22 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（numeric）Field-measured theta_opt values exhibit good agreement with PaM-modeled theta_Pa

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | numeric | Regression slope between optically-derived theta_opt and PaM | 0.85 | abs 0.085 / 10.0% |
| R02 | numeric | Regression intercept between theta_opt and theta_PaM should  | 12.34 | abs 1.234 / 10.0% |
| R03 | numeric | R-squared of theta_opt vs theta_PaM regression should be app | 0.72 | abs 0.072 / 10.0% |
| R04 | numeric | RMSE of theta_opt vs theta_PaM regression should be approxim | 19.17 | abs 1.917 / 10.0% |

### C02（numeric）Modeled C_phyto^mod vs bbp(470) yields linear regression (y = 14910x + 0.70, r^2

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R05 | numeric | Regression slope of modeled C_phyto^mod against bbp(470) sho | 14910 | abs 1491.0 / 10.0% |
| R06 | numeric | Regression intercept of C_phyto^mod vs bbp(470) should be ap | 0.7 | abs 0.07 / 10.0% |
| R07 | numeric | R-squared of C_phyto^mod vs bbp(470) regression should be ap | 0.61 | abs 0.061 / 10.0% |
| R08 | numeric | RMSE of C_phyto^mod vs bbp(470) regression should be approxi | 16.31 | abs 1.631 / 10.0% |

### C03（numeric）Modeled NPP agrees with 14C incubations overall (y = 0.99x - 1.4, r^2 = 0.80, n 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R09 | numeric | Overall regression slope of modeled NPP vs 14C measurements  | 0.99 | abs 0.099 / 10.0% |
| R10 | numeric | Overall regression intercept of NPP vs 14C should be approxi | -1.4 | abs 0.14 / 10.0% |
| R11 | numeric | Overall R-squared of NPP vs 14C regression should be approxi | 0.8 | abs 0.08 / 10.0% |
| R12 | numeric | Subarctic climax regression slope of NPP vs 14C should be ap | 0.33 | abs 0.033 / 10.0% |
| R13 | numeric | Subarctic climax R-squared of NPP vs 14C regression should b | 0.85 | abs 0.085 / 10.0% |
| R14 | numeric | Subarctic climax RMSE of NPP vs 14C regression should be app | 6.43 | abs 0.643 / 10.0% |

### C04（figure）Depth-resolved modeled NPP profiles match discrete 14C measurements throughout e

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R15 | compare | Compare generated depth-resolved NPP profile figure against  | — | abs — / —% |

### C05（numeric）Depth-integrated NPP and division rate show distinct seasonal/regional patterns;

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R16 | numeric | Mean depth-integrated NPP (fNPP) in subarctic during climax  | 1464 | abs 146.4 / 10.0% |
| R17 | numeric | Standard deviation of fNPP in subarctic climax transition sh | 440 | abs 44.0 / 10.0% |
| R18 | trend | Subarctic f_mu fold-increase from winter to climax transitio | — | abs — / —% |

### C06（figure）MLD, Ig, C_phyto^bbp, ChlACS show strong seasonal and regional patterns across N

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R19 | compare | Compare generated transect overview figure against reference | — | abs — / —% |

### C07（figure）N:P ratios show distinct seasonal patterns with community composition shifts bet

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R20 | compare | Compare generated N:P ratio and community composition figure | — | abs — / —% |

### C08（numeric）Summary statistics of physical, biological, chemical parameters (MLD, Kd, N:P, H

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R21 | numeric | Summary statistics table must include mean and standard devi | 0 | abs 0 / 0% |
| R22 | trend | Summary statistics must cover all seven parameters: MLD, Kd, | — | abs — / —% |
