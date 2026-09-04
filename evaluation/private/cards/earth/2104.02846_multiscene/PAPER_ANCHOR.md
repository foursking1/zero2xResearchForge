# PAPER_ANCHOR.md（私有）— 2104.02846 MultiScene（L1 critical claim）

> 来源：Hua, Mou, Jin, Zhu, "MultiScene: A Large-scale Dataset and Benchmark for Multi-scene Recognition in Single Aerial Images", IEEE TGRS 2022（arXiv:2104.02846）。以下数值均从论文原文抽取，禁止臆造。

## 锚 1（主锚，L1 核心结果）

| 项 | 值 |
|---|---|
| 指标 | 多标签分类 mAP（mean Average Precision，MultiScene-Clean 测试集） |
| 论文数值 | **64.8%**（ResNeXt-101） |
| 出处 | Table II（NUMERICAL RESULTS OF BASELINE MODELS ON THE MULTISCENE-CLEAN DATASET） |
| 定义口径 | 36 类多标签；7,000 训练 / 7,000 测试；ImageNet 预训练 CNN + sigmoid 多标签头 |
| 容差 | 绝对差 ≤4pp 满分（mAP≥60.8%）；≤10pp 半满（见 SCORE_RUBRIC.md） |

## 锚 2（辅助指标，Table II，MultiScene-Clean）

| 模型 | mAP | mCF1 | mEF1 | OF1 |
|---|---|---|---|---|
| ResNeXt-101（主锚） | 64.8 | 57.3 | 70.2 | 71.3 |
| ResNet-152 | 63.8 | 57.7 | 69.2 | 70.4 |
| ResNet-101 | 63.0 | 55.8 | 69.1 | 70.3 |
| DenseNet-169 | 63.2 | 55.3 | 68.6 | 69.9 |
| ResNeXt-50 | 63.4 | 54.2 | 68.6 | 69.8 |
| VGG-16 | 56.5 | 53.6 | 67.0 | 67.9 |
| XGBOOST | 16.9 | 12.8 | 45.8 | 47.9 |
| SVM | 14.9 | 8.6 | 41.1 | 43.5 |

## 锚 3（结论性声明）

- 论文：深度模型大幅超越传统方法（mAP 64.8 vs 14.9–16.9），但绝对性能仍有很大空间——MultiScene 是挑战性基准。
- 数据集：MultiScene 100,000 图（OSM 众包标注含噪声）、MultiScene-Clean 14,000 图（人工修正标签）。

## 锚 4（数据与任务设置）

| 项 | 值 | 出处 |
|---|---|---|
| MultiScene-Clean 规模 | 14,000 图、36 类、多标签 | §II、README |
| 划分 | 7,000 训练 / 7,000 测试 | §IV.A |
| 影像 | 512×512，0.26–7.44 m/pixel | §II |

## 冻结协议与本锚的关系（重要，判分时注意）

- 本任务冻结 MultiScene-Clean 全量 14,000 图；评测协议：固定 50/50 划分（`multiscene_split_50.csv`，seed 20260813），与论文 7,000/7,000 一致。
- 容差（±4pp 满分带）已考虑划分与实现差异；数据同源同协议。
- agent 用预训练 ResNet/ResNeXt 微调时预期 mAP 60–67%；传统方法 ~15–20%。
- 禁止照抄 64.8；B 维度要求所有数字从冻结数据重算。
