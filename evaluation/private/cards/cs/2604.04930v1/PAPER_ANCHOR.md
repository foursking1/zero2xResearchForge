# PAPER_ANCHOR（私有）：2604.04930v1

> 论文：Early Stopping for Large Reasoning Models via Confidence Dynamics
> 出处：arXiv preprint (Under review, April 2026)
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 22 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（numeric）CoDE-Stop achieves a more favorable accuracy-compute tradeoff than baseline earl

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | numeric | CoDE-Stop compression rate (CR) should be between 50-75% acr | 62.5 | abs 12.5 / 20.0% |
| R02 | trend | CoDE-Stop accuracy should be within 2 percentage points of V | — | abs — / —% |
| R03 | trend | CoDE-Stop should achieve lower CR than all baseline methods  | — | abs — / —% |
| R04 | figure | Figure 5: scatter plots showing CoDE-Stop points in upper-le | — | abs — / —% |

### C02（trend）CoDE-Stop can be combined with different prompting strategies and further improv

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R05 | trend | For each of the 4 prompting strategies (Vanilla, Budget Forc | — | abs — / —% |
| R06 | trend | CoDE-Stop combined with each prompting strategy should maint | — | abs — / —% |
| R07 | figure | Figure 6: accuracy vs total tokens for each prompting strate | — | abs — / —% |

### C03（trend）Correct trajectories reach high confidence early while incorrect trajectories ex

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R08 | trend | Early-stage confidence (first quartile of steps) should show | — | abs — / —% |
| R09 | trend | Incorrect trajectories should have higher confidence varianc | — | abs — / —% |
| R10 | numeric | Correct trajectories should average approximately 12K tokens | 25000 | abs 5000 / 20.0% |
| R11 | trend | Incorrect trajectories should have significantly more reason | — | abs — / —% |

### C04（trend）CoDE-Stop reduces unnecessary computation on incorrect rollouts compared to DEER

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R12 | trend | CoDE-Stop should achieve higher accuracy at shorter average  | — | abs — / —% |
| R13 | figure | Figure 7: accuracy vs average reasoning length on incorrect  | — | abs — / —% |

### C05（trend）Trend-aware v_i and log weighting w_i each achieve the best accuracy-compression

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R14 | trend | Trend-aware v_i variant should achieve the best accuracy-com | — | abs — / —% |
| R15 | trend | Log weighting w_i variant should achieve the best accuracy-c | — | abs — / —% |
| R16 | figure | Figure 8: two panels showing accuracy vs CR curves for v_i a | — | abs — / —% |

### C06（trend）Varying the degeneration threshold tau produces a smooth accuracy-compute tradeo

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R17 | trend | As tau increases, both accuracy and total tokens should gene | — | abs — / —% |
| R18 | figure | Figure 9: accuracy and total tokens plotted against tau valu | — | abs — / —% |

### C07（numeric）CoDE-Stop remains effective with lower budget (B=16K) across all models and benc

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R19 | numeric | CoDE-Stop at B=16K should achieve accuracy within 3 percenta | 0 | abs 3.0 / 0% |
| R20 | trend | CoDE-Stop at B=16K should maintain favorable compression rat | — | abs — / —% |

### C08（numeric）CoDE-Stop is robust to reasoning step delimiter choice (Wait vs Alternatively), 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R21 | numeric | Accuracy difference between 'Wait' and 'Alternatively' delim | 0 | abs 2.0 / 0% |
| R22 | numeric | Cost difference between 'Wait' and 'Alternatively' delimiter | 0 | abs 5.0 / 0% |
