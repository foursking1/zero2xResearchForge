# PAPER_ANCHOR（私有，仅裁判/编译者可见）：2206.02096 PEER — Solubility 任务锚

> 用途：LLM judge 判分基准。禁止向作答 agent 暴露本文件。所有论文数值均从 arXiv:2206.02096 抽出，禁止臆造。

## 锚 A1 — 数据集事实（数据事实锚）

| 项 | 值 |
|---|---|
| 指标名 | PEER Solubility 任务规模与划分 |
| 论文数值 | train **62,478** / valid **6,942** / test **1,999**；二分类（1=可溶）；指标 accuracy（%） |
| 出处 | Table 1（Benchmark task descriptions，Solubility 行：Protein-wise Cls.，62,478 / 6,942 / 1,999，Acc） |
| 判分口径 | 冻结 `solubility_{train,valid,test}.csv` 行数即 62,478 / 6,942 / 1,999；正类（label=1）比例约 41.7%（train 26,075/62,478） |

## 锚 A2 — 核心结果：单任务溶解度预测各方法 accuracy（判 A1/A2 维度）

| 项 | 值 |
|---|---|
| 指标名 | Solubility 单任务学习测试 accuracy，mean(std)，%（×100） |
| 论文数值 | DDE **59.77(1.21)**；Moran 57.73(1.33)；LSTM **70.18(0.63)**；Transformer 70.12(0.31)；CNN **64.43(0.25)**；ResNet 67.33(1.46)；ProtBert 68.15(0.92)；ProtBert*（冻结特征）59.17(0.21)；ESM-1b **70.23(0.75)**；ESM-1b*（冻结特征）67.02(0.40)；文献 SOTA DeepSol 77.0 |
| 出处 | Table 3（Benchmark results on single-task learning，Sol 行；列序：DDE / Moran / LSTM / Transformer / CNN / ResNet / ProtBert / ProtBert* / ESM-1b / ESM-1b* / Literature SOTA） |
| 判分口径 | agent 实测 accuracy 与论文数值的相对差 ≤10%（相对）视为对齐满分带；方向性排序为结构判据 |

## 锚 A3 — 核心论断（判 A3 维度）：模型族排序

| 项 | 值 |
|---|---|
| 指标名 | Solubility 上模型族性能排序：预训练 PLM vs 从零训练编码器 vs 特征工程 |
| 论文数值 | ESM-1b 70.23 ≥ LSTM 70.18 > CNN 64.43 > DDE 59.77 > Moran 57.73（Table 3，Sol 行） |
| 出处 | §5.2 Benchmark Results on Single-Task Learning；Table 3 |
| 判分口径 | 结构性论断：PLM（或最强编码器）显著高于特征工程（差 ≥3pp）即方向成立；若只实现 DDE+CNN，要求 CNN ≥ DDE + 3pp |

## 辅助数据事实（裁判 B 维度抽查基准；均从冻结数据统计，非论文数值）

| 字段 | 冻结参考值 | 备注 |
|---|---|---|
| train 行数 | 62,478 | solubility_train.csv |
| valid 行数 | 6,942 | solubility_valid.csv |
| test 行数 | 1,999 | solubility_test.csv |
| train 正类（label=1） | 26,075（41.7%） | 本包统计 |
| test 正类（label=1） | 1,000（50.0%） | 本包统计 |
| 序列长度范围 | 19–1200（中位 275） | 本包统计 |

## 判分对照速查（judge 用）

- A1（数据装配，15 分）：train/valid/test 数 = 62,478 / 6,942 / 1,999 且正类比例说明正确 → 满分。
- A2（锚复现，25 分）：agent 实测 DDE ≈59.77（±10% 相对）与 CNN ≈64.43（±10% 相对）→ 满分带；实现 LSTM/ESM 额外模型有加分说明。
- A3（论断方向，20 分）：CNN/LSTM > DDE（差 ≥3pp）且结论标签与数据一致 → 满分带。
- B 抽查两数：(1) test 行数 = 1,999；(2) 任选一个模型的 accuracy（从 agent 代码+冻结数据重算，须与报告一致，相对差 ≤1e-6）。
- 若 agent 抄论文数字冒充实测（如直接把 59.77 填进 metrics.json）→ A 总分 ×0.5 且 B 直接 ≤10 分。