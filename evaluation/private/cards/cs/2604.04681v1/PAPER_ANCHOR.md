# PAPER_ANCHOR（私有）：2604.04681v1

> 论文：Batch Loss Score for Dynamic Data Pruning
> 出处：CVPR 2026
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 30 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（numeric）BLS proxies per-sample loss methods (InfoBatch, SeTa) on large-scale datasets (T

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | numeric | BLS-InfoBatch and BLS-SeTa achieve comparable or improved CI | — | abs — / —% |
| R02 | numeric | BLS-variants achieve strong parity with baselines on MJ+ST ( | — | abs — / —% |
| R03 | numeric | BLS-SeTa achieves comparable COCO CIDEr to SeTa on SS1M (3M  | 45.6 | abs 1.0 / 3.0% |

### C02（numeric）BLS achieves statistically indistinguishable accuracy from InfoBatch/SeTa on CIF

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R04 | numeric | BLS-InfoBatch accuracy on CIFAR10 at 30% pruning is statisti | — | abs — / —% |
| R05 | numeric | BLS-SeTa accuracy on CIFAR100 at 50% pruning is statisticall | — | abs — / —% |
| R06 | numeric | BLS-InfoBatch accuracy on CIFAR100 at 70% pruning is statist | — | abs — / —% |

### C03（numeric）BLS demonstrates cross-architecture generalization on ImageNet-1K and CIFAR100 w

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R07 | numeric | BLS maintains accuracy close to full training for ResNet18 o | 70.0 | abs 2.0 / 3.0% |
| R08 | numeric | BLS maintains accuracy close to full training for ViT on Ima | 78.0 | abs 2.0 / 3.0% |
| R09 | numeric | BLS maintains accuracy close to full training for Vim (Visio | 75.0 | abs 2.0 / 3.0% |

### C04（numeric）BLS works on diverse tasks: image captioning (COCO), video captioning (MSR-VTT),

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R10 | numeric | BLS variants achieve comparable B@4, M, C, S metrics to full | — | abs — / —% |
| R11 | numeric | BLS variants achieve comparable B@4, M, C, S metrics to full | — | abs — / —% |
| R12 | numeric | BLS variants achieve comparable <3-i accuracy to full traini | — | abs — / —% |

### C05（numeric）BLS works with generative models (VAE/MNIST, DDPM/CIFAR10, DDPM-CFG/CIFAR10), pr

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R13 | numeric | BLS preserves FID scores for VAE on MNIST while pruning ~22- | 10.0 | abs 3.0 / 30.0% |
| R14 | numeric | BLS preserves FID scores for DDPM on CIFAR10 while pruning ~ | 12.0 | abs 3.0 / 25.0% |
| R15 | numeric | BLS preserves FID scores for DDPM-CFG on CIFAR10 while pruni | 8.0 | abs 3.0 / 37.0% |

### C06（numeric）BLS integrates into SSL (FixMatch/CIFAR100, FlexMatch/Yelp, Dash/ESC-50), prunin

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R16 | numeric | BLS achieves comparable accuracy to full training for FixMat | — | abs — / —% |
| R17 | numeric | BLS achieves comparable accuracy to full training for FlexMa | — | abs — / —% |
| R18 | numeric | BLS achieves comparable accuracy to full training for Dash o | — | abs — / —% |

### C07（numeric）BLS enhances YOLOv5 for classification (CIFAR100), detection (COCO), segmentatio

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R19 | numeric | BLS maintains or improves mAP for YOLOv5n object detection o | — | abs — / —% |
| R20 | numeric | BLS maintains or improves mAP for YOLOv5n instance segmentat | — | abs — / —% |

### C08（figure）Frequency separation: noise N_i has higher PSD at high frequencies than signal S

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R21 | figure | Figure 2: Average PSD over 50K samples showing noise compone | — | abs — / —% |

### C09（numeric）Ablation: EMA is critical; full BLS > w/o EMA BLS; full BLS matches baselines

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R22 | trend | Removing EMA degrades accuracy compared to full BLS on CIFAR | — | abs — / —% |
| R23 | trend | Removing EMA degrades accuracy compared to full BLS on CIFAR | — | abs — / —% |
| R24 | numeric | Full BLS matches or exceeds original InfoBatch accuracy on C | — | abs — / —% |
| R25 | numeric | Full BLS matches or exceeds original SeTa accuracy on CIFAR1 | — | abs — / —% |

### C10（figure）Alpha in [0.7, 0.8] gives best accuracy-pruning trade-off; alpha=0.7 default (Fi

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R26 | figure | Figure 3: Accuracy and pruning ratio vs alpha for ResNet18 a | — | abs — / —% |
| R27 | trend | Alpha=0.7 achieves better accuracy than alpha=0.5 on CIFAR10 | — | abs — / —% |
| R28 | trend | Pruning ratio increases as alpha decreases on CIFAR100 with  | — | abs — / —% |

### C11（numeric）BLS overhead is negligible: <0.02s added per 1M samples vs base methods

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R29 | numeric | BLS-InfoBatch adds less than 0.02s overhead compared to Info | 0.015 | abs 0.02 / 50.0% |
| R30 | numeric | BLS-SeTa adds approximately 0.02s overhead compared to SeTa  | 0.02 | abs 0.02 / 50.0% |
