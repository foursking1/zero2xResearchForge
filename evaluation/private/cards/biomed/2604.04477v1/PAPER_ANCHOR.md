# PAPER_ANCHOR（私有）：2604.04477v1

> 论文：MVis-Fold: A Three-Dimensional Microvascular Structure Inference Model for Super-Resolution Ultrasound
> 出处：arXiv preprint
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 14 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（numeric）MVis-Fold achieves Dice >= 0.95, sensitivity >= 0.94, specificity >= 0.95, accur

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | numeric | MVis-Fold Dice coefficient on test set should be approximate | 0.959 | abs 0.034 / 5.0% |
| R02 | numeric | MVis-Fold sensitivity on test set should be approximately 0. | 0.951 | abs 0.038 / 5.0% |
| R03 | numeric | MVis-Fold specificity on test set should be approximately 0. | 0.957 | abs 0.025 / 5.0% |
| R04 | numeric | MVis-Fold accuracy on test set should be approximately 0.962 | 0.962 | abs 0.053 / 5.0% |
| R05 | trend | MVis-Fold Dice should exceed all three baseline Dice scores | — | abs — / —% |

### C02（numeric）MVis-Fold achieves vessel density error < 0.02 mm/mm3 and mean diameter error < 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R06 | numeric | MVis-Fold vessel density error should be approximately 0.012 | 0.012 | abs 0.006 / 50.0% |
| R07 | numeric | MVis-Fold mean diameter error should be approximately 2.16 u | 2.16 | abs 0.5 / 25.0% |
| R08 | trend | MVis-Fold vessel density error should be much smaller than 2 | — | abs — / —% |

### C03（numeric）Extracted vessel density shows Pearson correlation r >= 0.85 (p < 0.01) with his

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R09 | numeric | Pearson correlation between MVis-Fold vessel density and his | 0.892 | abs 0.05 / 5.0% |
| R10 | numeric | Correlation p-value should be < 0.001 | 0.0 | abs 0.001 / 0.0% |

### C04（numeric）Internal validation set achieved Dice coefficient >= 0.95

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R11 | numeric | Internal validation Dice coefficient should be approximately | 0.964 | abs 0.041 / 5.0% |

### C05（numeric）Mean inference speed ~8.3 seconds per volume; Hausdorff distance <= 5 pixels

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R12 | numeric | Hausdorff distance between MVis-Fold predictions and gold st | 3.2 | abs 1.1 / 10.0% |
| R13 | numeric | Mean inference time per volume should be approximately 8.3 s | 8.3 | abs 2.0 / 20.0% |

### C06（figure）3D visualization shows coherent vascular structures with qualitative agreement t

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R14 | figure | 3D reconstruction visualization comparing MVis-Fold output w | — | abs — / —% |
