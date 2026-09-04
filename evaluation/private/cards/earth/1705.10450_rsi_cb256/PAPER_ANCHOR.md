# PAPER_ANCHOR.md（私有）— 1705.10450 RSI-CB256

> 来源：Li et al., "RSI-CB: A Large-Scale Remote Sensing Image Classification Benchmark Using Crowdsourced Samples", Remote Sensing 9(11), 2017（arXiv:1705.10450）。

## 锚 1（主锚，L1 核心结果）
| 项 | 值 |
|---|---|
| 指标 | Overall accuracy（OA，测试集） |
| 论文数值 | **95.13%（VGG-16）**；训练 OA 98%+ |
| 出处 | Table 6（"Tabel6. OA of training and test on datasets using DCNN"） |
| 定义口径 | RSI-CB256（256×256，6 大类 + 35 子类）；VGG-16 DCNN |
| 容差 | 相对差 d≤10% 满分；d≤30% 半满（见 SCORE_RUBRIC.md） |

## 锚 2（同表其他模型，RSI-CB256 测试 OA）
| 模型 | 测试 OA | 出处 |
|---|---|---|
| AlexNet | 94.78% | Table 6 |
| GoogLeNet | 94.07% | Table 6 |
| ResNet | 95.02% | Table 6 |

## 锚 3（数据集设置，§3/Table 1-2）
| 项 | 值 |
|---|---|
| 规模 | RSI-CB256 24,000+ 张（6 大类 35 子类） |
| 尺寸 | 256×256 |
| 标注 | 两级层次（大类 + 子类） |

## 冻结子集与本锚的关系（判分注意）
- 冻结镜像 24,750 张，label_1 为 7 类、label_2 为 42 类（镜像标注较论文略细）。锚为论文 RSI-CB256 测试 OA 量级；B 维度重算基于冻结数据。
- 禁止照抄 95.13%；须从冻结数据重算并说明标签口径。
