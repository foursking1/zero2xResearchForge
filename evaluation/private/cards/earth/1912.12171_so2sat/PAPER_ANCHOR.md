# PAPER_ANCHOR.md（私有）— 1912.12171 So2Sat

> 来源：Zhu et al., "So2Sat LCZ42: A Dataset and Benchmark for Local Climate Zones", IEEE TGRS 2020（arXiv:1912.12171）。

## 锚 1（主锚，L1 核心结果）
| 项 | 值 |
|---|---|
| 指标 | 总体精度 OA（LCZ42 验证集） |
| 论文数值 | **OA 0.61**（ResNeXt-CBAM，仅 Sentinel-2） |
| 出处 | Table V（"ResNeXt-CBAM 0.61 0.92 0.51 0.58"，OA/WA/AA/Kappa） |
| 定义口径 | 在官方训练集训练、官方 validation 评估；S2 only |
| 容差 | 相对差 d≤10% 满分；d≤30% 半满（见 SCORE_RUBRIC.md） |

## 锚 2（同表完整行，Table V S2）
| 方法 | OA | WA | AA | Kappa | 出处 |
|---|---|---|---|---|---|
| SVM | 0.54 | 0.88 | 0.36 | 0.49 | Table V |
| ResNeXt-CBAM | 0.61 | 0.92 | 0.51 | 0.58 | Table V |

## 锚 3（数据集设置，§2）
| 项 | 值 |
|---|---|
| 规模 | 42 城市，约 40 万标注像元块（32×32） |
| 波段 | Sentinel-1（VV/VH×4 时相=8ch）、Sentinel-2（10 波段） |
| 类别 | 17 个 LCZ |
| 划分 | train（约 38 万）/ validation（官方 h5 24,119） |

## 冻结子集与本锚的关系（判分注意）
- 冻结官方 validation（24,119 样本），论文训练集未冻结 → agent 需自行划分训练/评估子集，口径差异如实报告。
- 禁止照抄 0.61；B 维度要求从冻结数据重算。
