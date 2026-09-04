# PAPER_ANCHOR（私有）：bensen_2007

> 论文：Processing seismic ambient noise data to obtain reliable broad-band surface wave dispersion measurements
> 出处：Geophysical Journal International (2007), 169, 1239-1260
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 25 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（figure）Broad-band symmetric-component cross-correlation from 12-months of data between 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | compare | Compare generated ANMO-HRV six-passband cross-correlation fi | — | abs — / —% |

### C02（figure）Comparison of five time-domain normalization methods shows that one-bit, running

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R02 | compare | Compare generated normalization method comparison figure aga | — | abs — / —% |
| R03 | trend | Verify SNR ordering: running-absolute-mean, one-bit, and wat | — | abs — / —% |

### C03（figure）Tuning temporal normalization weights to the earthquake band (15-50s) reduces sp

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R04 | compare | Compare generated earthquake-band tuning comparison figure a | — | abs — / —% |

### C04（figure）Spectral whitening flattens the amplitude spectrum at station HRV, removing micr

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R05 | compare | Compare generated spectral whitening spectrum figure against | — | abs — / —% |

### C05（figure）Spectral whitening removes the 26s monochromatic noise peak from ANMO-CCM cross-

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R06 | compare | Compare generated 26s noise removal comparison figure agains | — | abs — / —% |

### C06（figure）Cross-correlations with spectral whitening between CCM and SSPA produce broader-

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R07 | compare | Compare generated broader-band cross-correlation figure agai | — | abs — / —% |

### C07（trend）Rayleigh wave signal emerges with increasing stacking length (1 < 3 < 12 < 24 mo

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R08 | compare | Compare generated SNR emergence with stacking length figure  | — | abs — / —% |
| R09 | trend | Verify spectral SNR increases monotonically with stacking le | — | abs — / —% |

### C08（numeric）Power law fit SNR = A*t^(1/n) with exponent n varying from ~2.55 at 10s to ~3.4 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R10 | numeric | Power law exponent n at 10s period should be approximately 2 | 2.55 | abs 0.25 / 10.0% |
| R11 | numeric | Power law exponent n at 25s period should be approximately 2 | 2.88 | abs 0.29 / 10.0% |
| R12 | numeric | Power law exponent n at 50s period should be approximately 3 | 3.4 | abs 0.34 / 10.0% |
| R13 | numeric | Power law exponent n at 100s period should be approximately  | 2.66 | abs 0.27 / 10.0% |
| R14 | trend | Verify power law exponent n ordering: n(10s) < n(25s) < n(50 | — | abs — / —% |

### C09（figure）Automated FTAN on 12-month ANMO-COR produces group speed curve consistent with S

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R15 | compare | Compare generated FTAN dispersion measurement figure against | — | abs — / —% |

### C10（figure）Cross-correlations between PFO and five stations show waveform agreement with Oc

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R16 | compare | Compare generated earthquake waveform comparison figure agai | — | abs — / —% |

### C11（figure）Spatial cluster of 10 SoCal stations shows group and phase speed curves that agr

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R17 | compare | Compare generated spatial cluster analysis figure against re | — | abs — / —% |

### C12（numeric）10 of 12 three-month stacks of CCM-DWPF yield consistent group velocity measurem

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R18 | compare | Compare generated temporal variability figure against refere | — | abs — / —% |
| R19 | numeric | At least 10 of 12 three-month stacks should yield acceptable | 10 | abs 1 / 0% |

### C13（trend）Linear inverse relationship between standard deviation of group speed and spectr

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R20 | compare | Compare generated SNR proxy curve scatter plot against refer | — | abs — / —% |
| R21 | trend | Verify that binned standard deviation decreases as spectral  | — | abs — / —% |

### C14（numeric）Ambient noise misfit (std=12.6s) is tighter than earthquake misfit (std=22.7s) a

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R22 | numeric | Ambient noise misfit standard deviation at 16s period across | 12.6 | abs 1.3 / 10.0% |
| R23 | numeric | Earthquake misfit standard deviation at 16s period across Eu | 22.7 | abs 2.3 / 10.0% |
| R24 | trend | Ambient noise misfit std dev should be approximately half th | — | abs — / —% |
| R25 | compare | Compare generated misfit histogram figure against reference | — | abs — / —% |
