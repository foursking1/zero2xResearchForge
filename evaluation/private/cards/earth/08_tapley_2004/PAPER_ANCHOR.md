# PAPER_ANCHOR（私有）：08_tapley_2004

> 论文：GRACE Measurements of Mass Variability in the Earth System
> 出处：Science 305, 503–505 (23 July 2004); DOI: 10.1126/science.1099192
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 24 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（numeric）Annual variation in geoid height from GRACE compared with GLDAS hydrology model 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | numeric | GRACE annual cosine component minimum value should be -7.2 m | -7.2 | abs 0.5 / 7.0% |
| R02 | numeric | GRACE annual cosine component maximum value should be +3.0 m | 3.0 | abs 0.3 / 10.0% |
| R03 | numeric | GRACE annual cosine component global RMS should be 0.9 mm | 0.9 | abs 0.1 / 10.0% |
| R04 | numeric | GRACE annual sine component minimum value should be -6.4 mm | -6.4 | abs 0.5 / 7.0% |
| R05 | numeric | GRACE annual sine component maximum value should be +8.9 mm | 8.9 | abs 0.5 / 7.0% |
| R06 | numeric | GRACE annual sine component global RMS should be 1.3 mm | 1.3 | abs 0.15 / 10.0% |
| R07 | numeric | GLDAS annual cosine component minimum value should be -2.3 m | -2.3 | abs 0.3 / 10.0% |
| R08 | numeric | GLDAS annual cosine component maximum value should be +3.2 m | 3.2 | abs 0.3 / 10.0% |
| R09 | numeric | GLDAS annual cosine component global RMS should be 0.4 mm | 0.4 | abs 0.1 / 15.0% |
| R10 | numeric | GLDAS annual sine component minimum value should be -4.0 mm | -4.0 | abs 0.3 / 10.0% |
| R11 | numeric | GLDAS annual sine component maximum value should be +6.7 mm | 6.7 | abs 0.5 / 10.0% |
| R12 | numeric | GLDAS annual sine component global RMS should be 1.0 mm | 1.0 | abs 0.1 / 10.0% |

### C02（numeric）Month-to-month geoid variability for equatorial South America during 2003 shows 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R13 | numeric | Amazon basin local maximum geoid anomaly in April 2003 shoul | 14.0 | abs 1.0 / 7.0% |
| R14 | numeric | Amazon basin local minimum geoid anomaly in October 2003 sho | -7.7 | abs 0.8 / 10.0% |
| R15 | figure | Figure showing monthly geoid anomaly maps for equatorial Sou | — | abs — / —% |

### C03（figure）Observed geoid height differences for April 2002 (1000 km smoothing) and April 2

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R16 | figure | Four-panel figure comparing observed geoid signals (top row) | — | abs — / —% |

### C04（numeric）GRACE monthly gravity field estimates have geoid height accuracy of 2 to 3 mm at

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R17 | numeric | GRACE 2003 solutions should have error level of 2 to 3 mm fo | 2.5 | abs 0.5 / 20.0% |
| R18 | numeric | GRACE 2002 solutions should have error level of 2 to 3 mm on | 2.5 | abs 0.5 / 20.0% |

### C05（trend）GRACE observed significantly larger magnitudes of annual geoid variability compa

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R19 | trend | GRACE cosine amplitude range (10.2 mm) should exceed GLDAS c | — | abs — / —% |
| R20 | trend | GRACE sine amplitude range (15.3 mm) should exceed GLDAS sin | — | abs — / —% |
| R21 | trend | GRACE RMS should exceed GLDAS RMS for both cosine (0.9 > 0.4 | — | abs — / —% |

### C06（trend）The annual cycle in geoid variations peaks predominantly in the spring and fall 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R22 | trend | GRACE sine RMS (1.3 mm) should exceed cosine RMS (0.9 mm), i | — | abs — / —% |
| R23 | trend | GLDAS sine RMS (1.0 mm) should exceed cosine RMS (0.4 mm), c | — | abs — / —% |

### C07（trend）There is a clear difference between the 2002 and 2003 monthly GRACE solutions, w

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R24 | trend | 2003 solutions should achieve 2-3 mm error at 600 km smoothi | — | abs — / —% |
