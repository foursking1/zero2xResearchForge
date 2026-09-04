# PAPER_ANCHOR.md（私有）— 1902.06701 HybridSN

> 来源：Roy et al., "HybridSN: Exploring 3-D–2-D CNN Feature Hierarchy for Hyperspectral Image Classification", IEEE GRSL 17(2), 2020（arXiv:1902.06701）。

## 锚 1（主锚，L2 核心结果）
| 项 | 值 |
|---|---|
| 指标 | 总体精度 OA（Indian Pines，30% 训练/70% 测试） |
| 论文数值 | **99.75 ± 0.1%**（HybridSN，Table II；窗口 25×25） |
| 出处 | Table II（"HybridSN 99.75 ± 0.1"）；Table IV 窗口敏感性 25×25→99.75 |
| 定义口径 | 30% 有标注像素随机划分训练、70% 测试（正文）；多次随机取均值±标准差 |
| 容差 | 相对差 d≤10% 满分；d≤30% 半满（见 SCORE_RUBRIC.md） |

## 锚 2（另两数据集，Table II）
| 数据集 | HybridSN OA | 出处 |
|---|---|---|
| University of Pavia (UP) | 99.98 ± 0.0 | Table II |
| Salinas Scene (SA) | 100 ± 0.0 | Table II |

## 锚 3（基线对比，Table II，IP 列）
| 方法 | OA | 出处 |
|---|---|---|
| SVM | 91.70 ± 1.1 | Table II |
| 2D-CNN | 97.09 ± 0.4 | Table II |
| 3D-CNN | 98.70 ± 0.3 | Table II |
| SSRN | 99.19 ± 0.3 | Table II |

## 冻结子集与本锚的关系（判分注意）
- 冻结 IP 原始数据（145×145×200/220 + GT）；论文口径 30%/70% 随机划分需自行实现。
- 禁止照抄 99.75；B 维度要求从冻结数据重算。
