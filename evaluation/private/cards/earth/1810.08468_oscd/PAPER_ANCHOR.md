# PAPER_ANCHOR.md（私有）— 1810.08468 OSCD（L1 critical claim）

> 来源：Daudt et al., "Urban Change Detection for Multispectral Earth Observation Using Convolutional Neural Networks", IGARSS 2018（arXiv:1810.08468）。以下数值均从论文原文抽取，禁止臆造。

## 锚 1（主锚，L1 核心结果）

| 项 | 值 |
|---|---|
| 指标 | 整体分类精度（Accuracy，正确像素/总像素） |
| 论文数值 | **83.63%**（3 通道 Early Fusion） |
| 出处 | Table 1（"3 ch." 行 EF 列，整体 Acc） |
| 定义口径 | OSCD 测试集 10 对影像逐像素二值分类（变化/无变化）；EF=双时相影像通道拼接输入 CNN；类别加权损失 |
| 容差 | 绝对差 ≤3pp 满分（Acc≥80.63%）；≤8pp 半满（见 SCORE_RUBRIC.md） |

## 锚 2（辅助指标，Table 1）

| 方法 | 整体 Acc | 变化类 Acc | 无变化类 Acc |
|---|---|---|---|
| 3 ch. EF（主锚） | 83.63 | 82.14 | 83.71 |
| 3 ch. Siamese | 84.13 | 78.57 | 84.43 |
| 4 ch. EF | 89.66 | 80.30 | 90.16 |
| 10 ch. EF | 89.15 | 82.75 | 89.50 |
| 13 ch. EF | 88.15 | 84.69 | 88.33 |
| 13 ch. Siamese | 85.37 | 85.63 | 85.35 |
| Img diff / Log-ratio / GLRT | 76.12 / 76.93 / 76.25 | 63.42 / 59.68 / 60.48 | 76.82 / 77.87 / 77.11 |

## 锚 3（结论性声明）

- "Table 1 explores eight variants of CNNs and shows their superiority to the difference image methods"——CNN 方法（尤其 EF）显著优于经典差值方法。
- 多光谱通道（10/13 ch.）进一步改善结果；本卡冻结 RGB 版，对应 "3 ch." 行。

## 锚 4（数据与任务设置）

| 项 | 值 | 出处 |
|---|---|---|
| 数据集 | 24 对 Sentinel-2 双时相影像（2015–2018），14 训练 / 10 测试 | §2、README |
| 掩码 | 二值变化掩码（城市变化：新建建筑/道路） | §2 |
| 影像 | RGB 582×522（本卡冻结）；官方全分辨率 10000×10000 13 波段 | README |
| 度量 | 整体/变化/无变化类精度 | Table 1 |

## 冻结协议与本锚的关系（重要，判分时注意）

- 本任务冻结 OSCD RGB 全量（14+10 对，582×522）；评测协议与论文一致：train 14 对训练、test 10 对评测，报告整体/变化/无变化精度。
- 锚取 3 通道 EF 83.63%（本冻结数据即 RGB 3 通道）；容差（±3pp 满分带）已考虑实现差异（架构/损失/阈值）。
- 数据同源同协议；agent 用简单 U-Net/EF-CNN 认真复现时预期整体 80–86%；差值基线 ~76%。
- 禁止照抄 83.63；B 维度要求所有数字从冻结数据重算。
