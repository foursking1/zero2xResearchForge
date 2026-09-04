# PAPER_ANCHOR（私有）：2604.04878v1

> 论文：Learning, Potential, and Retention: An Approach for Evaluating Adaptive AI-Enabled Medical Devices
> 出处：arXiv:2604.04878v1
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 14 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（trend）Single population shift: stable performance/retention across steps; learning fol

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | trend | Performance AUROC values should show relative stability (no  | — | abs — / —% |
| R02 | trend | Learning curve should track potential curve closely across a | — | abs — / —% |
| R03 | trend | Potential should reach its maximum value at modification ste | — | abs — / —% |
| R04 | trend | Retention values should remain stable (no significant trend) | — | abs — / —% |

### C02（trend）Limited plasticity: gradual performance decrease; learning never reaches potenti

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R05 | trend | Performance should show a gradual decreasing trend from step | — | abs — / —% |
| R06 | trend | Learning should be strictly less than potential at every mod | — | abs — / —% |
| R07 | trend | Retention values should not show a clear increasing or decre | — | abs — / —% |

### C03（trend）Double population shift: non-monotonic performance; learning/potential spike at 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R08 | trend | Performance should not increase monotonically across the 5 m | — | abs — / —% |
| R09 | trend | Potential and learning should show local maxima at steps 1 a | — | abs — / —% |
| R10 | trend | At step 3, performance should decrease while retention incre | — | abs — / —% |

### C04（numeric）Metrics computed using Equations 1-3 with lambda = 0.5

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R11 | numeric | The retention decay weight parameter lambda should equal 0.5 | 0.5 | abs 0.001 / 0.0% |

### C05（numeric）Results reported as mean and 95% CI across 25 repetitions

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R12 | numeric | All experiments should use exactly 25 repetitions for statis | 25 | abs 0 / 0.0% |
| R13 | exists | Results should include 95% confidence intervals for all repo | — | abs — / —% |

### C06（exists）VIGILANT package publicly available at github.com/DIDSR/VIGILANT

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R14 | exists | The VIGILANT repository should be cloned and installed | — | abs — / —% |
