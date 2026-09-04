# PAPER_ANCHOR（私有，仅裁判/编译者可见）：2501.14238 Point-LN

> 用途：LLM judge 判分基准。禁止向作答 agent 暴露本文件。所有论文数值均从 arXiv:2501.14238v1 抽出（PAGE 6-7），禁止臆造。

## 锚 A1 — ModelNet40 精度-效率（判 A1 维度）

| 项 | 值 |
|---|---|
| 指标名 | ModelNet40 总体精度 + 可学习参数量 |
| 论文数值 | 精度 **94.0%**；参数 **0.8M**；对比：PointMLP 94.1% / 12.6M（≈15.75× 参数）、Point-NN 81.8% / 0.0M、Point-GN 85.3% / 0.0M |
| 出处 | Table I（Comparison of Point Cloud Classification Methods On ModelNet40）+ §IV-C（"It achieves an accuracy of 94.0%, which is comparable to the best performing model, PointMLP [14], with an accuracy of 94.1%. However, PointMLP has a significantly larger model size (12.6M parameters)"） |
| 判分口径 | agent 实测测试精度 + 实测可学习参数；与 94.0/0.8M 对照（数值带见 SCORE_RUBRIC A1） |

## 锚 A2 — ScanObjectNN 真实场景（判 A2 维度）

| 项 | 值 |
|---|---|
| 指标名 | ScanObjectNN 各子集总体精度 |
| 论文数值 | OBJ-BG **92.2%** / OBJ-ONLY **92.1%** / PB-T50-RS **91.7%**（本包冻结 PB_T50_RS 子集，判分主锚 = 91.7%） |
| 出处 | Table II（Comparison of Point Cloud Classification Methods On ScanObjectNN）+ §IV-D（"Point-LN achieves state-of-the-art accuracy across all subsets, with 92.2% on OBJ-BG, 92.1% on OBJ-ONLY, and 91.7% on the most challenging PB-T50-RS subset"） |
| 判分口径 | agent 实测 PB-T50-RS 测试精度；与 91.7% 对照（数值带见 SCORE_RUBRIC A2） |

## 锚 A3 — 上下文（不单独计分）：数据集事实与对比

| 项 | 论文数值 | 出处 |
|---|---|---|
| ModelNet40 规模 | 12,311 CAD 模型 / 40 类；train 9,843 / test 2,468 | §IV-B |
| ScanObjectNN 规模 | 2,902 样本 / 15 类（真实扫描，含遮挡/杂乱/背景） | §IV-B |
| 采样惯例 | 每物体采样 1,024 点（PointNet++ 等惯例） | §IV-B/实验段落 |
| 对比基线 | PointMLP PB-T50-RS 85.4%（论文正文对比句）；OBJ-BG/OBJ-ONLY 见 Table II | §IV-D |

## 辅助数据事实（裁判 B 维度抽查基准；从冻结数据直接核验，非论文数值）

| 字段 | 冻结参考值 | 备注 |
|---|---|---|
| ModelNet40 train 样本数 | 9,843 | modelnet40_train.txt 行数 |
| ModelNet40 test 样本数 | 2,468 | modelnet40_test.txt 行数 |
| ModelNet40 类别数 | 40 | shape_names 行数 |
| ScanObjectNN train 样本数 | 11,416 | h5 data 第一维 |
| ScanObjectNN test 样本数 | 2,882 | h5 data 第一维（论文口径 2,902 物体为原始对象数，h5 含增广变体，属已知口径差异） |
| ScanObjectNN 类别数 | 15 | label 0-14 |
| 每样本点数 | ModelNet40 10,000（txt）/ ScanObjectNN 2,048（h5） | 采样到 1,024 由 agent 自行实现 |

## 判分对照速查（judge 用）

- A1 满分带：ModelNet40 精度 ≥ 93.0% 且参数 ≤ 2.0M（论文 94.0/0.8M）。
- A2 满分带：ScanObjectNN PB-T50-RS 精度 ≥ 90.0%（论文 91.7%）。
- B 抽查两数：(1) ModelNet40 test = 2,468；(2) ScanObjectNN h5 test 样本数 = 2,882（或 train = 11,416），从 agent 代码+冻结数据重算。
- 若 agent 精度明显低于论文但给出可信的协议差异/失效分析，A 按数值带判、C 维度可给方法讨论分；禁止把论文数字抄作实测。