# PAPER_ANCHOR.md（私有）— 2103.10368 MSMatch

> 来源：Van Gansbeke et al., "Semi-Supervised Learning for Remote Sensing Image Classification"（arXiv:2103.10368）。

## 锚 1（主锚，L2 核心结果）
| 项 | 值 |
|---|---|
| 指标 | 分类准确率（UC Merced，每类 5 个标注样本） |
| 论文数值 | **90.71%**（MSMatch，摘要） |
| 出处 | 摘要："we reach 90.71% with five labeled examples"（UC Merced Land Use）；正文超 5.59pp 于前作 |
| 定义口径 | 每类 5 个标注样本 + 其余未标注；MSMatch 半监督框架 |
| 容差 | 相对差 d≤10% 满分；d≤30% 半满（见 SCORE_RUBRIC.md） |

## 锚 2（同方法 EuroSAT，摘要）
| 数据集 | 准确率 | 出处 |
|---|---|---|
| EuroSAT RGB | 94.53%（每类 5 标注） | 摘要 |
| EuroSAT Multispectral | 95.86%（每类 5 标注） | 摘要 |

## 锚 3（数据集设置，§3）
| 项 | 值 |
|---|---|
| 规模 | UC Merced 2,100 张（21 类 × 100） |
| 半监督口径 | 每类 k 个标注（k=5,10,20 等），其余为未标注池 |
| 影像 | 256×256 RGB |

## 冻结子集与本锚的关系（判分注意）
- 冻结 UC Merced 全量（2,100 张）；口径为每类 5 标注 + 未标注池。
- 禁止照抄 90.71；B 维度要求从冻结数据重算。
