# PAPER_ANCHOR.md（私有）— 2206.00515 Landslide4Sense

> 来源：Ghorbanzadeh, Xu, Ghamisi, Kopp, Kreil, "Landslide4Sense: Reference Benchmark Data and Deep Learning Models for Landslide Detection", IEEE TGRS vol.60, 2022（arXiv:2206.00515v3）。以下数值均从论文原文抽取，禁止臆造。

## 锚 1（主锚，L1 核心结果）

| 项 | 值 |
|---|---|
| 指标 | F1-score（landslide 类，像素级二分类） |
| 论文数值 | **71.65%**（ResU-Net，11 个模型最优） |
| 出处 | Table I（第 V 节 "Experimental Results"） |
| 定义口径 | 训练 959 patch（每研究区前 1/4）+ 测试 2840 patch（其余 3/4）；14 波段（S2 B1–B12 + ALOS PALSAR Slope/DEM）128×128；所有模型 Adam lr=1e-3、batch 32、5000 iter、from scratch；测试集为四研究区独立保留 patch |
| 容差 | 相对差 d≤10% 满分（F1∈[64.5,78.8]）；d≤30% 半满（见 SCORE_RUBRIC.md） |

## 锚 2（辅助指标，同表）

| 指标 | 论文数值 | 出处 | 口径 |
|---|---|---|---|
| Precision（ResU-Net） | 76.08% | Table I | 同上 |
| Recall（ResU-Net） | 67.71% | Table I | 同上 |
| F1（U-Net） | 69.94% | Table I | 同上 |
| F1（PSPNet，最低） | 56.39% | Table I | 同上 |

## 锚 3（模型排名，Table I 隐含的定性结论）

ResU-Net (71.65) > SQNet (70.24) > FRRN-B (70.10) > U-Net (69.94) > FRRN-A (69.96 排序在 U-Net 前) … > PSPNet (56.39)。论文原文：ResU-Net 最优，其次 SQNet（"marginally surpasses the third-best model FRRN-B by 0.14 percentage points"）。注意原文 F1 排序：FRRN-A=69.96、FRRN-B=70.10、SQNet=70.24、U-Net=69.94。

## 锚 4（数据与任务设置，Table I 之外）

| 项 | 值 | 出处 |
|---|---|---|
| 数据集规模 | 3,799 patches（959 train / 2,840 test） | 摘要；第 IV 节 |
| 研究区 | Iburi(2018-09)、Kodagu(2018-08)、Gorkha(2015-04)、Taiwan(2009-08) | 摘要；第 III 节 |
| 波段 | 14：S2 B1–B12 + Slope B13 + DEM B14，重采样 ~10m | 第 IV 节、README FAQ |
| patch 尺寸 | 128×128，像素级标注（0 非滑坡 / 1 滑坡） | 第 IV 节 |
| 类别比例 | 训练部分滑坡像素占比约 5.5%（"close to 5.5% of the training section"） | 第 IV 节（Fig. 8 讨论段） |
| 训练设置 | Adam lr=1e-3、batch 32、5000 iterations、from scratch、4×V100 | 第 V 节 A |

## 冻结子集与本锚的关系（重要，判分时注意）

- 本任务冻结 240 train + 240 test patch（官方 3799 池按文件序固定子集），非论文原 959/2840 划分（论文未公开 patch→研究区映射，无法精确复刻）。
- 数据同源、同 sensor、同标注协议；因此 agent 的 F1 与 71.65% 的比较属于「同基准数据池子集上的性能复现」，容差已考虑子集差异（满分带 ±10% 相对差）。
- 禁止以「子集不同」为由直接照抄 71.65%；B 维度要求所有数字从冻结数据重算。
