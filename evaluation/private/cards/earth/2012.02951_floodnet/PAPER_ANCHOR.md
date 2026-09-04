# PAPER_ANCHOR.md（私有）— 2012.02951 FloodNet

> 来源：Rahnemoonfar et al., "FloodNet: A High Resolution Aerial Imagery Dataset for Post Flood Scene Understanding", IEEE TPAMI 2021（arXiv:2012.02951）。

## 锚 1（主锚，L1 核心结果）
| 项 | 值 |
|---|---|
| 指标 | VQA 整体准确率（Overall Accuracy） |
| 论文数值 | **Validation 0.72 / Testing 0.73**（MFB with Co-Attention） |
| 出处 | Table 5（"MFB with Co-Attention [71] Validation 0.72 ... Testing 0.73"） |
| 定义口径 | VGG16 图像特征 + 双层 LSTM 问题特征 + MFB 双线性融合；官方 train/valid/test 划分 |
| 容差 | 相对差 d≤10% 满分；d≤30% 半满（见 SCORE_RUBRIC.md） |

## 锚 2（按问题类型，Table 5 MFB 行）
| 类型 | Validation | Testing | 出处 |
|---|---|---|---|
| Overall Accuracy | 0.72 | 0.73 | Table 5 |
| Simple Counting | 0.31 | 0.29 | Table 5 |
| Complex Counting | 0.28 | 0.26 | Table 5 |
| Yes/No | 0.98 | 0.99 | Table 5 |
| Entire Image Condition | 0.96 | 0.97 | Table 5 |

## 锚 3（数据集设置，§3）
| 项 | 值 |
|---|---|
| 规模 | 2,343 张航拍影像（train ~60% / valid ~20% / test ~20%） |
| VQA | Train 4,511 问-答对；4 类问题（Condition/Simple/Complex/Yes-No） |
| 影像 | DJI Mavic Pro 采集，3000×4000 高分辨率 |

## 冻结子集与本锚的关系（判分注意）
- 冻结官方 Training 问答（4,511 对含答案）+ 影像；官方 Valid/Test 答案未发布 → agent 自行划分评估子集，口径差异如实报告。
- 禁止照抄 0.72/0.73；B 维度要求从冻结数据重算。
