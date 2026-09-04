# PAPER_ANCHOR.md（私有）— 1509.03602 DeepSat

> 来源：Basu, Ganguly, Mukhopadhyay, DiBiano, Karki, Nemani, "DeepSat: A Learning Framework for Satellite Imagery", ACM SIGSPATIAL 2015（arXiv:1509.03602）。数值从论文原文抽取。

## 锚 1（主锚，L1 核心结果）
| 项 | 值 |
|---|---|
| 指标 | Overall classification accuracy（OA，6 类） |
| 论文数值 | **93.9%**（SAT-6） |
| 出处 | 摘要（"On SAT-6, it produces a classification accuracy of 93.9% and outperforms the other algorithms by ~15%"） |
| 定义口径 | SAT-6 共 405,000 图块（28×28，1m），80% 训练 / 20% 测试（不相交图块）；NLCD 标签映射 6 类；DeepSat 框架 = 特征提取 + 归一化 + DBN 分类 |
| 容差 | 相对差 d≤10% 满分（OA∈[84.5,103.3]→截断 100）；d≤30% 半满（见 SCORE_RUBRIC.md） |

## 锚 2（同摘要，SAT-4）
| 指标 | 论文数值 | 出处 | 口径 |
|---|---|---|---|
| OA（SAT-4，4 类） | 97.95% | 摘要 | SAT-4 共 500,000 图块，同框架；比 DBN/CNN/SDA 高 ~11% |

## 锚 3（数据规模，§4）
| 项 | 值 | 出处 |
|---|---|---|
| SAT-6 图块数 | 405,000（324,000 训练 + 81,000 测试） | §4 |
| 图块尺寸/分辨率 | 28×28 px / 1m | §4 |
| 类别 | 6（barren land, building, grassland, road, trees, water） | §4/Fig. 3 |

## 冻结子集与本锚的关系（判分注意）
- 冻结数据为官方 SAT-6 **Test split**（81,000 图，HF 镜像 README 明确）；论文训练集未冻结。
- 因此 agent 需自行从冻结数据划分子集训练；OA 与 93.9% 的比较属于「同数据集测试子集上的性能复现」，容差已考虑训练策略差异。
- 禁止照抄 93.9%；B 维度要求所有数字从冻结数据重算。
