# PAPER_ANCHOR.md（私有）— 1703.00121 RESISC45

> 来源：Cheng, Han, Lu, "Remote Sensing Image Scene Classification: Benchmark and State of the Art", Proceedings of the IEEE 105(10), 2017（arXiv:1703.00121）。

## 锚 1（主锚，L1 核心结果）
| 项 | 值 |
|---|---|
| 指标 | Overall accuracy（OA，45 类） |
| 论文数值 | **87.15±0.45%（10% 训练）/ 90.36±0.18%（20% 训练）**（Fine-tuned VGGNet-16） |
| 出处 | Table 6（第 V 节；训练比例按每类随机子集） |
| 定义口径 | 每类随机取 10%/20% 作训练、其余测试；微调 ImageNet 预训练 VGGNet-16 |
| 容差 | 相对差 d≤10% 满分；d≤30% 半满（见 SCORE_RUBRIC.md） |

## 锚 2（同表参考，其他方法）
| 方法 | 10% | 20% | 出处 |
|---|---|---|---|
| Fine-tuned AlexNet | 81.22±0.19 | 85.16±0.18 | Table 6 |
| Fine-tuned GoogLeNet | 82.57±0.12 | 86.02±0.18 | Table 6 |

## 锚 3（数据集设置，摘要/§II）
| 项 | 值 |
|---|---|
| 规模 | 31,500 张，45 类 × 700 |
| 尺寸 | 256×256 |
| 分辨率 | 约 0.2–30 m/px |

## 冻结子集与本锚的关系（判分注意）
- 冻结全量 31,500 张（与论文一致）；划分由 agent 按论文口径从冻结数据生成。
- 禁止照抄 87.15/90.36；B 维度要求数字从冻结数据重算。
