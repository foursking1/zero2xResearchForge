# PAPER_ANCHOR.md（私有）— 2010.00243 MLRSNet（L1 critical claim）

> 来源：Qi et al., "MLRSNet: A Multi-label High Spatial Resolution Remote Sensing Dataset for Semantic Scene Understanding", ISPRS J. 2020（arXiv:2010.00243）。以下数值均从论文原文抽取，禁止臆造。

## 锚 1（主锚，L1 核心结果）

| 项 | 值 |
|---|---|
| 指标 | 多标签分类 mAP（mean Average Precision，按类 AP 均值） |
| 论文数值 | **88.77%**（MLRSNet-DenseNet201，40% 训练比例） |
| 出处 | Table 6（mAP of the eight fine-tuned models under different training ratios） |
| 定义口径 | 60 类多标签；ImageNet 预训练 CNN 微调 + sigmoid 输出 + 0.5 阈值（§3.1）；随机 40% 训练 |
| 容差 | 绝对差 ≤3pp 满分（mAP≥85.77%）；≤8pp 半满（见 SCORE_RUBRIC.md） |

## 锚 2（辅助指标，Table 6/7）

| 模型 | mAP@40% | F1@40% | 出处 |
|---|---|---|---|
| MLRSNet-DenseNet201（主锚） | 88.77 | 0.8538 | Table 6/7 |
| MLRSNet-DenseNet169 | 87.35 | 0.8521 | Table 6/7 |
| MLRSNet-ResNet101 | 85.72 | 0.8226 | Table 6/7 |
| MLRSNet-ResNet50 | 86.01 | 0.8353 | Table 6/7 |
| MLRSNet-InceptionV3 | 84.84 | 0.8146 | Table 6/7 |
| MLRSNet-VGGNet16 | 75.39 | 0.6855 | Table 6/7 |

## 锚 3（结论性声明）

- 论文：MLRSNet 上微调深度 CNN 可有效完成多标签场景识别；"MLRSNet-DenseNet201 and MLRSNet-DenseNet169 achieve over 0.80 F1 score"；训练数据增加性能提升（§3.2 结论）。
- 数据集：109,161 张 256×256，60 类标签，平均每图约 5 个标签（§2）。

## 锚 4（数据与任务设置）

| 项 | 值 | 出处 |
|---|---|---|
| 数据集规模 | 109,161 图，60 类多标签，256×256 | §2 |
| 训练比例 | 20% / 30% / 40% | Table 6 |
| 度量 | mAP、F1 | §3.2 |

## 冻结协议与本锚的关系（重要，判分时注意）

- 本任务冻结全量 109,161 图；评测协议：固定 40/60 划分（`mlrsnet_split_40.csv`，seed 20260813），mAP/F1 在冻结测试 65,497 图上计算。
- 论文 Table 6 的 40% 列为随机划分 10 次均值；本固定划分为其确定性实例，容差（±3pp 满分带）已考虑划分与实现差异。
- 数据同源同协议；agent 用预训练 DenseNet/ResNet 微调时预期 mAP 84–89%；VGG 系 ~73–76%。
- 禁止照抄 88.77；B 维度要求所有数字从冻结数据重算。
