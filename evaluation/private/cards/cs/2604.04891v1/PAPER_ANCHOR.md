# PAPER_ANCHOR（私有）：2604.04891v1

> 论文：Muon Dynamics as a Spectral Wasserstein Flow
> 出处：arXiv preprint 2604.04891v1, April 2026
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 10 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（numeric）Static spectral couplings for Schatten p = 1, 2, infinity show different optimal

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | numeric | Optimal transport cost for Schatten p=1 (trace norm) should  | 23.745 | abs 1.2 / 5.0% |
| R02 | numeric | Optimal transport cost for Schatten p=2 (Frobenius norm) sho | 19.916 | abs 1.0 / 5.0% |
| R03 | numeric | Optimal transport cost for Schatten p=infinity (operator nor | 19.323 | abs 1.0 / 5.0% |
| R04 | trend | Optimal transport costs should decrease monotonically as p i | — | abs — / —% |
| R09 | figure | Figure 1: Three-panel plot showing static spectral couplings | — | abs — / —% |

### C02（figure）MMD gradient flows with Schatten p = 1, 2, infinity produce qualitatively differ

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R05 | numeric | Final MMD loss for gradient flow with Schatten p=1 (W2 flow) | 0.0018 | abs 0.0003 / 15.0% |
| R06 | numeric | Final MMD loss for gradient flow with Schatten p=2 (Frobeniu | 0.0016 | abs 0.00025 / 15.0% |
| R07 | numeric | Final MMD loss for gradient flow with Schatten p=infinity (M | 0.0011 | abs 0.0002 / 15.0% |
| R08 | trend | Final MMD losses should decrease monotonically as p increase | — | abs — / —% |
| R10 | figure | Figure 2: Three-panel plot showing all particle trajectories | — | abs — / —% |
