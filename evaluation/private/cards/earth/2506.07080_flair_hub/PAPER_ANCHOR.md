# PAPER_ANCHOR.md（私有）— 2506.07080 FLAIR-HUB（L1 critical claim）

> 来源：Garioud, Giordano, David, Gonthier, "FLAIR-HUB: Large-scale Multimodal Dataset for Land Cover and Crop Mapping", arXiv:2506.07080v2（2026-03-05）。以下数值均从论文原文抽取，禁止臆造。

## 锚 1（主锚，L1 核心结果）

| 项 | 值 |
|---|---|
| 指标 | mIoU（15 类 land cover，像素级语义分割，类 0–14） |
| 论文数值 | **51.5%**（ResNet-50 + U-Net，仅 AERIAL RGBI 输入） |
| 出处 | Table IX（第 VII 节 A "CNN-based versus Transformer-based Model"；表内第一行 ResNet50 UNet） |
| 定义口径 | 官方 split `split_flairhub`（train 152,225 / valid 38,175 / test 50,700）；输入仅航空影像 IR/R/G 三通道；UPerFuse 框架同超参（150 epochs, AdamW, OneCycleLR）；评估类 0–14（排除弱标签类 15–18） |
| 容差 | 相对差 d≤10% 满分（mIoU∈[46.4, 56.7]）；d≤30% 半满（见 SCORE_RUBRIC.md） |

## 锚 2（辅助指标，同一 aerial-only 实验组）

| 指标 | 论文数值 | 出处 | 口径 |
|---|---|---|---|
| OA（ResNet-50+U-Net, aerial-only） | 72.6% | Table IX | 同上 |
| mIoU（Swin-Base + UPerNet, aerial-only） | 64.1% | Table IX（第 5 段） | 同上 |
| OA（Swin-Base + UPerNet, aerial-only） | 77.5% | Table IX | 同上 |
| mIoU / OA（LC-A：Aerial VHR only, UPerFuse） | 64.1% / 77.5% | Table X | 单模态配置 LC-A |
| aerial-only 性能带 | mIoU 51.5–64.1、OA 72.6–77.5 | Table IX/X 汇总 | 判定 claim 成立的下界 |

## 锚 3（多模态边际增益声明，Table X 定性结论）

- LC-A（仅航空）→ LC-L（近全模态）OA +0.9%、mIoU +1.7%（"Adding all available modalities yields only marginal improvements compared to using the Aerial VHR modality alone (OA: +0.9%, mIoU: +1.7%)"，§VII-B.1）。
- LC-ALL（含历史影像）OA 78.2% / mIoU 65.6%，略低于 LC-L（78.2% / 65.8%），历史影像引入噪声。
- 摘要头条：最佳（多模态）78.2% accuracy / 65.8% mIoU。
- 本卡仅以 aerial-only 锚为主判依据；多模态声明不作数值判定，但允许 agent 在报告中讨论（加分项）。

## 锚 4（数据与任务设置）

| 项 | 值 | 出处 |
|---|---|---|
| 数据集规模 | 241,100 patches（512×512@0.2 m）、74 时空域、2,822 ROI、2,528 km² | 数据集概览页/§II |
| 类目 | 19 类（0–18）；实验用前 15 类 0–14（building 0, greenhouse 1, swimming_pool 2, impervious 3, pervious 4, bare_soil 5, water 6, snow 7, herbaceous 8, agricultural 9, plowed 10, vineyard 11, deciduous 12, coniferous 13, brushwood 14）；15–18 弱标签排除 | §IV-A、Table VI |
| 官方 split | `split_flairhub`：train 152,225 / valid 38,175 / test 50,700（与 split 1 相同，域级划分保证 test 域未见） | §IV-B |
| 影像 | AERIAL RGBI：R,G,B,NIR 4 通道 uint8、20 cm；论文实验取 IR/R/G 三通道 | §V、README |
| 训练设置 | 150 epochs、batch 5、AdamW wd=0.01、OneCycleLR lr=5e-5、4–6 节点 V100/A100/H100 | §VI |

## 冻结子集与本锚的关系（重要，判分时注意）

- 本任务冻结 600 patch：train 400（D005 250 + D091 150）、valid 100（D005 60 + D091 40）、test 100（D015，官方 test 子集），均取自官方 `split_flairhub`。
- 数据同源、同 sensor、同标注协议（COSIA 0–14）；agent 的 test mIoU 与 51.5%（ResNet-50+U-Net 全量训练）的比较属于「同基准数据池、缩小规模 + 跨域冻结子集上的性能复现」。
- 训练域（D005 高山/雪/裸土、D091）与测试域（D015 农业/落叶林）分布差异显著 → 预期 agent mIoU 低于论文 51.5%；容差与半满带已考虑该偏差（满分带仍要求 ≤10% 相对差，半满带 ≤30%）。
- 禁止以「子集不同」为由直接照抄 51.5%；B 维度要求所有数字从冻结数据重算。
