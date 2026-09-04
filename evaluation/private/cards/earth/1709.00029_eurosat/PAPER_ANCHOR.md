# PAPER_ANCHOR.md（私有）— 1709.00029 EuroSAT

> 来源：Helber, Bischke, Dengel, Korbar, "EuroSAT: A Novel Dataset and Deep Learning Benchmark for Land Use and Land Cover Classification", IEEE JSTARS 2019（arXiv:1709.00029）。

## 锚 1（主锚，L1 核心结果）
| 项 | 值 |
|---|---|
| 指标 | Overall classification accuracy（OA，10 类） |
| 论文数值 | **98.57%** |
| 出处 | 摘要（"we achieved an overall classification accuracy of 98.57%"） |
| 定义口径 | 基于深度 CNN（VGG 变体）；§III 报告浅 CNN 89.03% 为另一配置 |
| 容差 | 相对差 d≤10% 满分（OA∈[88.7,100]）；d≤30% 半满（见 SCORE_RUBRIC.md） |

## 锚 2（§III 浅层 CNN）
| 指标 | 论文数值 | 出处 |
|---|---|---|
| OA（浅 CNN 配置） | 89.03% | §III（"a classification accuracy of up to 89.03%"） |

## 锚 3（数据集设置，摘要/§III）
| 项 | 值 |
|---|---|
| 图数 | 27,000（10 类 × 2,700） |
| 尺寸 | 64×64 |
| 波段 | 13（Sentinel-2 多光谱；RGB 为其中 3 波段） |
| 划分 | train/validation/test ≈ 60/20/20 |

## 冻结子集与本锚的关系（判分注意）
- 冻结 RGB 三波段（HF 镜像）；论文主结果可基于多光谱或 RGB。容差已考虑 RGB-only 与通道差异。
- 训练集/测试集已按官方划分冻结；agent 不得用 test 调参。
- 禁止照抄 98.57%；B 维度要求数字从冻结数据重算。
