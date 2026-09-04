# PAPER_ANCHOR.md（私有）— 2110.08733 LoveDA

> 来源：Wang et al., "LoveDA: A Remote Sensing Land-Cover Dataset for Domain Adaptive Semantic Segmentation", NeurIPS 2021 D&B（arXiv:2110.08733）。

## 锚 1（主锚，L1 核心结果）
| 项 | 值 |
|---|---|
| 指标 | mIoU（语义分割，7 类） |
| 论文数值 | **49.79%**（HRNet W32，Table 2） |
| 出处 | Table 2（"HRNet [45] W32 ... 49.79"）；Table 3 MSTrTe 后 52.14% |
| 定义口径 | HRNet-W32，官方 train/val 划分，全监督 |
| 容差 | 相对差 d≤10% 满分；d≤30% 半满（见 SCORE_RUBRIC.md） |

## 锚 2（增强与对比，Table 2/3）
| 配置 | mIoU | 出处 |
|---|---|---|
| HRNet W32 | 49.79% | Table 2 |
| HRNet + MSTrTe | 52.14% | Table 3 |
| DeepLabV3+ | 47.62% | Table 3 |

## 锚 3（数据集设置，§3）
| 项 | 值 |
|---|---|
| 规模 | 5,987 张 1024×1024 影像（train 2,522 / val 1,669 / test 1,796）；7 类 |
| 特性 | 城市/乡村双域，样本由 UAS 采集 |
| 划分 | 官方 train/val/test（Table 8 in §A.1） |

## 冻结子集与本锚的关系（判分注意）
- 冻结 HF train 子集（约 562 张，2 shard），非论文全量 train/val → agent 自行划分评估子集，口径差异如实报告。
- 禁止照抄 49.79；B 维度要求从冻结数据重算。
