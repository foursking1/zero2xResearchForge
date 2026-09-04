# PAPER_ANCHOR（私有）：2604.04911v1

> 论文：SpatialEdit: Benchmarking Fine-Grained Image Spatial Editing
> 出处：arXiv:2604.04911v1
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 22 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（numeric）SpatialEdit achieves best overall performance on SpatialEdit-Bench: Moving Score

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | numeric | Moving Score on SpatialEdit-Bench should equal 0.673 | 0.673 | abs 0.034 / 5.0% |
| R02 | numeric | Rotation Score on SpatialEdit-Bench should equal 0.632 | 0.632 | abs 0.032 / 5.0% |
| R03 | numeric | Viewpoint Error on SpatialEdit-Bench should equal 0.243 | 0.243 | abs 0.012 / 5.0% |
| R04 | numeric | Framing Error on SpatialEdit-Bench should equal 0.527 | 0.527 | abs 0.026 / 5.0% |
| R05 | numeric | Object Overall score should equal 0.653 | 0.653 | abs 0.033 / 5.0% |
| R06 | numeric | Camera Overall Error should equal 0.385 | 0.385 | abs 0.019 / 5.0% |

### C02（numeric）SpatialEdit achieves competitive general editing performance on GEdit-Bench-EN (

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R07 | numeric | Semantic Consistency score on GEdit-Bench-EN should equal 8. | 8.09 | abs 0.4 / 5.0% |
| R08 | numeric | Perceptual Quality score on GEdit-Bench-EN should equal 7.80 | 7.8 | abs 0.39 / 5.0% |
| R09 | numeric | Overall score on GEdit-Bench-EN should equal 7.52 | 7.52 | abs 0.38 / 5.0% |

### C03（trend）Multi-task mixed training (Mov+Rot+Cam) yields the best overall trade-off vs sin

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R10 | trend | Moving Score ordering: Mov+Rot+Cam > Mov+Cam > Mov+Rot > Mov | — | abs — / —% |
| R11 | trend | Rotation Score ordering: Mov+Rot+Cam >= Mov+Rot > Rot only | — | abs — / —% |
| R12 | trend | Camera Error ordering (lower is better): Mov+Rot+Cam < Mov+C | — | abs — / —% |

### C04（numeric）VE (Spearman 0.932) attains the highest correlation with ground-truth rankings, 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R13 | numeric | VE Spearman correlation with ground-truth rankings should eq | 0.932 | abs 0.047 / 5.0% |
| R14 | numeric | FE Spearman correlation with ground-truth rankings should eq | 0.659 | abs 0.033 / 5.0% |
| R15 | numeric | GPT-4.1 Spearman correlation with ground-truth rankings shou | 0.445 | abs 0.022 / 5.0% |
| R16 | trend | Spearman correlation ordering: VE > FE > GPT-4.1 | — | abs — / —% |

### C05（exists）SpatialEdit-500k dataset contains approximately 500k synthetic paired samples

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R17 | exists | SpatialEdit-500k dataset manifest or sample count record mus | — | abs — / —% |
| R18 | exists | Dataset size record should show approximately 500k total sam | 500000 | abs 25000 / 5.0% |

### C06（trend）SpatialEdit outperforms world models on camera-level spatial editing: VE 0.243, 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R19 | trend | SpatialEdit VE (0.243) must be lower than all world models:  | — | abs — / —% |
| R20 | trend | SpatialEdit FE (0.527) must be lower than all world models | — | abs — / —% |
| R21 | trend | SpatialEdit Overall Error (0.385) must be lower than all wor | — | abs — / —% |

### C07（figure）SpatialEdit enhances single-view 3D reconstruction by synthesizing novel viewpoi

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R22 | figure | Figure showing 3D point cloud comparison: (a) single-view on | — | abs — / —% |
