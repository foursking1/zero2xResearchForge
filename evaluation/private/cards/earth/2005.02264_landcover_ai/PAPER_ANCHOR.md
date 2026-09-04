# PAPER_ANCHOR.md（私有）— 2005.02264 LandCover.ai

> 来源：Boguszewski et al., "LandCover.ai: Dataset for Automatic Mapping of Buildings, Woodlands, Water and Roads from Aerial Imagery", CVPR 2021（arXiv:2005.02264）。

## 锚 1（主锚，L1 核心结果）
| 项 | 值 |
|---|---|
| 指标 | mIoU（test 集，5 类） |
| 论文数值 | **85.56%**（DeepLabv3+，OS=4） |
| 出处 | §4：baseline DeepLabv3+ OS16=81.81%，OS4 提升 1.47% 达 85.56%；"we report simple benchmark results, achieving 85.56%" |
| 定义口径 | DeepLabv3+（ResNet 骨架），输出步长 4，官方 train/test 划分 |
| 容差 | 相对差 d≤10% 满分；d≤30% 半满（见 SCORE_RUBRIC.md） |

## 锚 2（方法对比，§4）
| 方法 | mIoU | 出处 |
|---|---|---|
| DeepLabv3+ OS16 | 81.81% | §4 |
| DeepLabv3+ OS4 | 85.56% | §4 |

## 锚 3（数据集设置，§3）
| 项 | 值 |
|---|---|
| 规模 | 33.2 km² / 5 类（building、woodland、water、road、other） |
| 影像 | 0.25 m/px 航拍正射影像（v1 包 42 张 5000×5000） |
| 划分 | 官方 patch 清单（train 7,470 / val 1,602 / test 1,602，512×512） |

## 冻结子集与本锚的关系（判分注意）
- 冻结官方完整 zip；锚为论文 test 口径。
- 禁止照抄 85.56%；B 维度要求从冻结数据重算。
