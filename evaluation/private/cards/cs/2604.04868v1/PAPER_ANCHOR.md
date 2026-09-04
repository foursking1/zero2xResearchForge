# PAPER_ANCHOR（私有）：2604.04868v1

> 论文：Noise Immunity in In-Context Tabular Learning: An Empirical Robustness Analysis of TabPFN's Attention Mechanisms
> 出处：arXiv:2604.04868v1, April 2026
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 17 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（numeric）Baseline: TabPFN achieves ROC-AUC=0.974; attention heatmaps show progressive con

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | numeric | TabPFN baseline ROC-AUC should equal 0.974 on synthetic data | 0.974 | abs 0.03 / 3.0% |
| R10 | figure | Attention heatmaps across layers 3, 6, 9, 12 should show pro | — | abs — / —% |

### C02（figure）PCA of feature-token embeddings shows progressive separation across layers

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R11 | figure | PCA scatter plots of feature-token embeddings at layers 3, 6 | — | abs — / —% |

### C03（figure）SHAP values show informative features dominate, random features negligible

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R12 | figure | SHAP summary plots should show features 0 and 1 (informative | — | abs — / —% |

### C04（trend）Random features test: ROC-AUC and attention metrics remain stable as features in

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R02 | trend | ROC-AUC should remain high and stable across all random feat | — | abs — / —% |
| R03 | trend | KL1 (attention concentration vs uniform) should exceed 0.2 f | — | abs — / —% |

### C05（figure）Attention heatmaps at layer 12 for 16 and 256 features show concentration on inf

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R13 | figure | Attention heatmaps at layer 12 for 16-feature and 256-featur | — | abs — / —% |

### C06（trend）Correlated features test: ROC-AUC stable; correlated features compete for attent

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R04 | trend | ROC-AUC should remain high as number of correlated features  | — | abs — / —% |
| R05 | trend | KL3 (divergence vs correlated+informative reference) should  | — | abs — / —% |

### C07（figure）SHAP with 8 correlated features shows correlated features get higher SHAP than r

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R14 | figure | SHAP plots for the 8-correlated-features case should show co | — | abs — / —% |

### C08（trend）Sample size test: metrics stable as rows increase 1500-12000, KL1 > 1

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R06 | trend | ROC-AUC should remain stable as training rows increase from  | — | abs — / —% |
| R07 | trend | KL1 should exceed 1.0 for all sample sizes, confirming stron | — | abs — / —% |

### C09（figure）Attention heatmaps and embeddings at 12000 rows match baseline pattern

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R15 | figure | Attention heatmaps and PCA embeddings at layers 3 and 12 for | — | abs — / —% |

### C10（trend）Label noise test: metrics stable as noise increases 0-35%, KL1 > 1

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R08 | trend | ROC-AUC should not degrade as label noise increases from 0%  | — | abs — / —% |
| R09 | trend | KL1 should exceed 1.0 for all noise levels, and attention me | — | abs — / —% |

### C11（figure）Attention heatmaps with 35% noise show reduced label self-attention at layer 3 a

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R16 | figure | Attention heatmaps at layers 3 and 12 with 35% label noise s | — | abs — / —% |

### C12（trend）Alternative data generation settings show consistent results across all parametr

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R17 | trend | Under all 3 alternative data generation settings (different  | — | abs — / —% |
