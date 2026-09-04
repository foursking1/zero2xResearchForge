# PAPER_ANCHOR.md（私有）— 1712.07835 RSICD（L1 critical claim）

> 来源：Lu et al., "Exploring Models and Data for Remote Sensing Image Caption Generation", IEEE TGRS 2018（arXiv:1712.07835）。以下数值均从论文原文抽取，禁止臆造。

## 锚 1（主锚，L1 核心结果）

| 项 | 值 |
|---|---|
| 指标 | CIDEr（5 句参考，范围 0–5） |
| 论文数值 | **1.98312**（AlexNet 特征 + hard attention） |
| 出处 | Table IX（attention-based method，RSICD 列） |
| 定义口径 | RSICD 测试集（10%）；注意力解码器；CNN 特征 + attention 逐区域加权；BLEU/ROUGE/METEOR/CIDEr 全套指标 |
| 容差 | 绝对差 ≤0.5 满分（CIDEr≥1.48）；≤1.0 半满（见 SCORE_RUBRIC.md；考虑冻结子集为官方 1/9 规模） |

## 锚 2（辅助指标）

| 指标 | 数值 | 出处 |
|---|---|---|
| CIDEr（AlexNet-hard attention，主锚） | 1.98312 | Table IX |
| CIDEr（VGG16-soft attention） | 1.96432 | Table IX |
| CIDEr（multimodal LSTM + AlexNet 特征） | 2.05261 | Table VI |
| CIDEr（multimodal LSTM + VGG19 特征） | 2.03324 | Table VI |
| CIDEr（手工特征 FV/VLAD + LSTM，最佳） | 1.05284 / 1.03918 | Table IV |
| BLEU-1 / BLEU-4 / METEOR / ROUGE-L（主锚行） | 0.68968 / 0.36895 / 0.33521 / 0.62673 | Table IX |

## 锚 3（结论性声明）

- 论文：所有 CNN 特征结果优于手工特征（§5.5.2）；注意力方法进一步改善描述质量。
- 数据规模优势：RSICD 10,921 图 × 5 句，优于 UCM-captions / Sydney-captions（§1、§5）。

## 锚 4（数据与任务设置）

| 项 | 值 | 出处 |
|---|---|---|
| 数据集规模 | 10,921 张 224×224，每图 5 句 | §1 |
| 划分 | 80/10/10 随机 | §5.4（Table II-IV 协议） |
| 度量 | BLEU-1..4、METEOR、ROUGE-L、CIDEr | §5.4 |

## 冻结协议与本锚的关系（重要，判分时注意）

- 本任务冻结官方子集镜像（1,400 图：1,000/200/200，比例 ~71/14/14）；评测协议：train 1,000 训练、test 200 评测，报告全套指标，CIDEr 为主锚。
- 论文 Table IX 在全量 10,921 的 10% 测试集上（~1,092 图）；本卡测试集为官方子集 200 图。容差（±0.5 满分带）已考虑子集规模差异与实现差异；判分同时参照论文内部相对差距（深度特征 vs 手工特征 ~1.9 vs 1.05）。
- 数据同源同任务；agent 用预训练 CNN 特征 + 注意力解码器认真复现时预期 CIDEr 1.2–1.8；纯手工特征或弱模型 0.6–1.2。
- 禁止照抄 1.98；B 维度要求所有数字从冻结数据重算。
