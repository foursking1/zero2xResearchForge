# PAPER_ANCHOR（私有）：2604.04914v1

> 论文：Analyzing Symbolic Properties for DRL Agents in Systems and Networking
> 出处：Proc. ACM Meas. Anal. Comput. Syst., Vol. 10, No. 2, Article 29 (June 2026)
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 11 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（figure）Pensieve Capacity Utilization verification heatmaps across checkpoints and model

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | figure | Verify Pensieve Capacity Utilization heatmaps showing per-qu | — | abs — / —% |

### C03（figure）Query execution time shows substantial variability across CROWN and MIP backends

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R03 | figure | Verify box plots comparing query execution times across CROW | — | abs — / —% |

### C04（figure）Pensieve Rebuffering Avoidance and Robustness aggregated results across checkpoi

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R02 | figure | Verify stacked bar charts for Pensieve Rebuffering Avoidance | — | abs — / —% |

### C05（figure）CMARS verification outcomes compared across Marabou, MIP, and CROWN for three pr

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R04 | figure | Verify horizontal stacked bar charts comparing CMARS safe/un | — | abs — / —% |

### C06（figure）CMARS query execution time for Channel Compensation shows log-scale variability 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R05 | figure | Verify box plots of CMARS query execution times for Channel  | — | abs — / —% |

### C07（numeric）Aurora verification: all safe at 70% coverage; at 100% coverage MIP finds unsafe

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R06 | trend | At 70% coverage, all three Aurora properties (Robustness, Ac | — | abs — / —% |
| R07 | trend | At 100% coverage, all three Aurora properties return 'unsafe | — | abs — / —% |
| R11 | trend | At 100% coverage, MIP backend uniquely finds unsafe results  | — | abs — / —% |

### C08（numeric）Smaller Pensieve model (H=64) produces approximately 45% fewer unknown results t

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R08 | numeric | The smaller Pensieve model (H=64) produces approximately 45% | 45.0 | abs 5.0 / 10.0% |

### C09（numeric）Approximately 60% of resolved Pensieve H=128 queries decided by only one engine 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R09 | numeric | Approximately 60% of resolved (non-unknown) queries for Pens | 60.0 | abs 5.0 / 10.0% |

### C10（numeric）CMARS pi_{2,30} with epsilon=0.001: perturbation induces 26 resource unit shift 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R10 | numeric | For CMARS pi_{2,30} robustness with epsilon=0.001, a perturb | 26.0 | abs 1.0 / 5.0% |
