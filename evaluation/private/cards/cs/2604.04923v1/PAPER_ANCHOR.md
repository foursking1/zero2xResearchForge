# PAPER_ANCHOR（私有）：2604.04923v1

> 论文：Stratifying Reinforcement Learning with Signal Temporal Logic
> 出处：arXiv:2604.04923v1, April 2026
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 20 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（numeric）VGT captures dimension drop from 2 in room to 1 in corridor on room-with-corrido

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | numeric | VGT local dimension in room region should be approximately 2 | 2.0 | abs 0.3 / 15.0% |
| R02 | numeric | VGT local dimension in corridor region should be approximate | 1.0 | abs 0.3 / 30.0% |
| R03 | trend | VGT should show clearer separation between room and corridor | — | abs — / —% |

### C02（numeric）VGT curves show slopes of 2 for probe points a/b and slope 1 for point c with tr

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R04 | numeric | VGT curve slope for probe point a (room-corridor connection) | 2.0 | abs 0.3 / 15.0% |
| R05 | numeric | VGT curve slope for probe point b (room center) should be ap | 2.0 | abs 0.3 / 15.0% |
| R06 | numeric | VGT curve slope for probe point c (corridor midpoint) should | 1.0 | abs 0.3 / 30.0% |
| R07 | numeric | VGT slope transition for probe point c should occur around r | 0.3 | abs 0.1 / 33.0% |
| R08 | trend | Probe c initial slope (1) should be less than probe a and b  | — | abs — / —% |

### C03（figure）HADES detects singularities accurately, DIC misses hourglass neck, VGT-dot provi

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R09 | figure | Figure 8: 6-panel comparison of HADES, DIC, and VGT-dot on r | — | abs — / —% |

### C04（exists）Trained DRL agent with Transformer-XL + PPO using STL robustness reward exists a

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R10 | exists | Trained DRL agent model weights must exist for both game var | — | abs — / —% |
| R11 | exists | Agent must use 256D token embeddings with 2 transformer bloc | 256 | abs — / —% |
| R12 | exists | STL robustness reward must be normalized to [-1, 1] range | -1.0 | abs — / —% |

### C05（figure）UMAP of game 1 embeddings reveals two separated clouds; VGT-dot 3-clustering pro

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R13 | numeric | Game 1 (eventually) should have approximately 7.6k unique em | 7600 | abs 1000 / 13.0% |
| R15 | figure | Figure 11: UMAP 3D projection of ~7.6k unique 256D embedding | — | abs — / —% |
| R19 | trend | Game 2 (eventually+always-not) should have more unique embed | — | abs — / —% |
| R20 | numeric | Each game should have 250 trajectories x 194 steps = 48,500  | 48500 | abs 500 / 1.0% |

### C06（figure）HADES on 100D DCT embeddings identifies non-manifold points concentrated at hour

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R16 | figure | Figure 12: 3D UMAP of 100D DCT-reduced embeddings with HADES | — | abs — / —% |

### C07（figure）UMAP and ISOMAP of game 2 embeddings with VGT-dot 2-clustering show hourglass pa

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R14 | numeric | Game 2 (eventually+always-not) should have approximately 12k | 12000 | abs 1500 / 12.5% |
| R17 | figure | Figure 13 left: UMAP 3D projection of ~12k game 2 embeddings | — | abs — / —% |
| R18 | figure | Figure 13 right: ISOMAP 3D projection of ~12k game 2 embeddi | — | abs — / —% |
