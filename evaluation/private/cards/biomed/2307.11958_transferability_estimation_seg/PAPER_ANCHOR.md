# 论文锚：2307.11958_transferability_estimation_seg

## 锚清单（全部来自论文，禁止臆造）

| # | 指标 | 论文数值 | 出处 | 定义口径 | 容差 |
|---|---|---|---|---|---|
| 1 | CC-FV 平均 Pearson 系数 | 0.7003 | Table 1（5 个 MSD 任务均值） | TE 分数与微调 Dice 的 Pearson 相关（Task03 0.8608 / 06 0.0903 / 07 0.9609 / 09 0.7491 / 10 0.8406） | 提交 ≥0.5 满分档 |
| 2 | CC-FV 平均加权 Kendall's τ | 0.4986 | Table 1 | 加权 Kendall's τ（Task03 0.6374 / 06 0.0735 / 07 0.6569 / 09 0.5700 / 10 0.5550） | 提交 ≥0.3 满分档 |
| 3 | 基线对比（GBC） | Pearson 0.3317 / τ 0.4111 | Table 1 | GBC 方法 5 任务均值 | 相对锚（CC-FV 须优于或持平） |
| 4 | 基线对比（LogME） | Pearson 0.2082 / τ 0.0218 | Table 1 | LogME 5 任务均值 | 相对锚 |
| 5 | 实验规模 | MSD 5 任务：Task03 Liver / Task06 Lung / Task07 Pancreas / Task09 Spleen / Task10 Colon（3D CT） | §Experiment on MSD Dataset | 论文用 5 个 MSD 数据集，每个用其他 4 个预训练、目标 1 个微调 | 冻结子集为 Spleen+Liver 2 任务 |

## 备注
- 主论断：CC-FV（类别一致性 + 特征多样性）在 source-free 条件下优于现有 TE 算法，能无训练选出最优源模型。
- 论文出处：arXiv:2307.11958，Table 1、§Experiment on MSD Dataset；数值以论文 PDF 为准。冻结数据为 MSD Spleen/Liver 子集。