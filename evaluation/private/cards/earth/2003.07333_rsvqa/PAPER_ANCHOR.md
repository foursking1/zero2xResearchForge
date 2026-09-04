# PAPER_ANCHOR.md（私有）— 2003.07333 RSVQA

> 来源：Lobry et al., "RSVQA: Visual Question Answering on Remote Sensing Images", IEEE TGRS 58(10), 2020（arXiv:2003.07333）。

## 锚 1（主锚，L1 核心结果）
| 项 | 值 |
|---|---|
| 指标 | 总体准确率 OA（LR 测试集） |
| 论文数值 | **79.08%（±0.20）** |
| 出处 | Table II（OA 行 79.08% (0.20%)）；正文 "overall accuracy of 79%" |
| 定义口径 | CNN（VGG16 特征）+ LSTM 问题编码，LR 数据集 test split |
| 容差 | 相对差 d≤10% 满分；d≤30% 半满（见 SCORE_RUBRIC.md） |

## 锚 2（按问题类型，Table II LR test）
| 类型 | 准确率 | 出处 |
|---|---|---|
| Count | 67.01%（0.59%） | Table II |
| Presence | 87.46%（0.06%） | Table II |
| Comparison | 81.50%（0.03%） | Table II |
| Rural/Urban | 90.00%（1.41%） | Table II |
| AA | 81.49%（0.49%） | Table II |

## 锚 3（语言偏差消融，§IV）
| 项 | 值 |
|---|---|
| 随机换图 OA（LR test） | 73.78% |
| 随机换图 OA（HR test1/test2） | 73.78% / 72.51% |
| 解读 | 模型部分依赖问题先验；HR 上换图掉点更多 |

## 冻结子集与本锚的关系（判分注意）
- 冻结 LR validation 2,000 问答子集（非论文 test）；锚为论文 LR test 量级，agent 自行划分评估子集，口径差异如实报告。
- 禁止照抄 79.08%；B 维度要求从冻结数据重算。
