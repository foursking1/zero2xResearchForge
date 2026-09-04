# PAPER_ANCHOR.md（私有）— 1706.03424 PatternNet

> 来源：Zhou et al., "PatternNet: A Benchmark Dataset for Performance Evaluation of Remote Sensing Image Retrieval", 2018（arXiv:1706.03424）。

## 锚 1（主锚，L1 核心结果）
| 项 | 值 |
|---|---|
| 指标 | mAP（内容检索，每图作 query 全库检索） |
| 论文数值 | **AlexNet_Fc1 mAP=0.6003**；VGGF mAP=0.6195 |
| 出处 | Table 4（AlexNet_Fc1 行）与 Table 5（VGGF 行）附近；§5.2 |
| 定义口径 | 每张图作 query，全库（排除自身）按特征相似度排序；mAP/P@k 平均 |
| 容差 | 相对差 d≤10% 满分；d≤30% 半满（见 SCORE_RUBRIC.md） |

## 锚 2（辅助指标）
| 模型 | mAP | P@5 | 出处 |
|---|---|---|---|
| AlexNet_Fc1 | 0.6003 | 0.9545 | Table 4 |
| AlexNet_Fc2 | 0.6042 | 0.9448 | Table 4 |
| VGGF_Fc1 | 0.6195 | 0.9246 | Table 5 |

## 锚 3（数据集设置，Table 1）
| 项 | 值 |
|---|---|
| 规模 | 38 类 × 800 = 30,400 张 |
| 尺寸 | 可变（高分辨率 Google Earth） |

## 冻结子集与本锚的关系（判分注意）
- 冻结镜像 30,400 张与论文一致；检索协议由 agent 按论文口径（每图作 query）或固定抽样实现。
- 禁止照抄 0.6003；B 维度要求 mAP 从冻结数据重算。
