# PAPER_ANCHOR（私有，仅裁判/编译者可见）：2508.14107 SuryaBench — DS4 耀斑预测

> 用途：LLM judge 的判分基准。禁止向作答 agent 暴露本文件。所有数值均从论文正文/表格抽出（arXiv:2508.14107v1），禁止臆造。

## 锚 A1 — DS4 数据集规模（数据事实锚）

| 项 | 值 |
|---|---|
| 指标名 | DS4（flare forecasting）标签总数 N |
| 论文数值 | **128,352** |
| 出处 | §2.2.4（"There are total 128,352 labels in the dataset."）；Table 2 的 DS4 行 N=128,352 |
| 定义口径 | 2010-05 → 2024-12 每小时一个 24h 预测窗口的二进制标签集（label_max / label_cum 两列）；动态范围 0/1（Table 2 末列） |
| 容差/判分口径 | 官方 HF README 与冻结全量 `data.csv` 为 128,328 行（差 24 行 = 1 天，为论文计数与发布文件间的已知差异）。判分以**冻结数据重算**为准：agent 报告 128,328（或四分裂之和 74,760+3,672+43,848+6,048=128,328）即视为正确复现数据规模；报告"约 128k"且数量级正确不扣分 |

## 锚 A2 — 二进制标签定义（口径锚）

| 项 | 值 |
|---|---|
| 指标名 | label_max / label_cum 阈值定义 |
| 论文数值 | 两个二进制标签：`Lmax > M1.0`（label_max）、`Lcum > 10`（label_cum） |
| 出处 | §2.2.4 末尾（"we create two binary labels checking (1) Lmax > M1.0 and Lcum > 10"）；Eqs. (3)–(5)（Lmax 取窗口内峰值级别、Lcum 为 C×1/M×10/X×100 加权和）；官方 HF README（`label_max` = goes_class ≥ M1.0；`label_cum` = cumulative_index ≥ 10） |
| 定义口径 | 冻结数据实现为 `max_goes_class ≥ M1.0`（即级别秩 ≥ 3.1，含恰好 M1.0 的 6,607 个窗口，全部 label_max=1）与 `cumulative_index ≥ 10`；与原始两列 100% 自洽（已核对，无冲突行） |
| 容差 | 从冻结数据可 100% 重算一致；agent 报告任何不一致行均属错误 |

## 锚 A3 — 核心结果：test 期二分类基线技能包络（核心结果锚，判 A 维度）

| 项 | 值 |
|---|---|
| 指标名 | test 期二分类（≥M1.0）预测的 TSS / HSS / CSS / F1-macro |
| 论文数值 | 5 个 CNN 基线（Table 3b，on test data）：**TSS ∈ [0.261, 0.359]**；HSS ∈ [0.281, 0.354]；CSS ∈ [0.271, 0.356]；F1 ∈ [0.627, 0.679] |
| 出处 | §4 Technical Validation + Table 3(b)（"Baseline performance for … solar flare classification using common deep learning models on test data"）；各模型行：AlexNet 0.359/0.354/0.356/0.679，MobileNet 0.326/0.312/0.319/0.662，ResNet18 0.320/0.317/0.318/0.660，ResNet34 0.290/0.289/0.289/0.645，ResNet50 0.261/0.281/0.271/0.627 |
| 定义口径 | 输入为 SDO AIA/HMI 影像（ML-ready 预处理图）的 CNN 分类器；标签为 DS4 二进制标签（≥M1.0）；评测期为官方 test 划分（2020–2024，活动周 25 上升期） |
| 容差（判分用） | 见 SCORE_RUBRIC.md A 维度分段：满分带 [0.20, 0.42]（论文包络 ±~0.06 扩展）；半满带 [0.10, 0.20) ∪ (0.42, 0.70]；TSS<0.10 或 >0.70 → 0 分 |
| 重要注记 | 冻结数据**不含影像**，仅 GOES 派生标签序列；纯 GOES 历史特征（含强 persistence 型信息）可达 TSS≈0.9，与论文影像基线（0.26–0.36）**不同源**。因此 >0.70 的 TSS 不被视为"复现论文结果"（A 判 0），B/C 维度仍按证据与方法给分——这是本卡固有难度（满分在冻结数据约束下不可达），已在 CALIBRATION.md 记录 |

## 辅助数据事实（裁判 B 维度抽查基准；均从冻结数据算出，非论文数值）

| 字段 | 冻结值 | 出处（冻结文件） |
|---|---|---|
| train 期 label_max 正类率 | 0.1211（9,051 / 74,760） | `data/train.csv` |
| test 期 label_max 正类率 | 0.2943（12,903 / 43,848） | `data/test.csv` |
| test 期样本量 | 43,848 | `data/test.csv` |
| validation 期正类率 | 0.1089（400 / 3,672） | `data/validation.csv` |
| 全量正类率 | 0.1812（23,255 / 128,328） | `data/data.csv` |
| 分年 test 期正类率 | 2020: 0.0055；2021: 0.0613；2022: 0.2638；2023: 0.4435；2024: 0.6969 | `data/test.csv`（按年聚合） |

## 判分对照速查（judge 用）

- 复现数据规模（128,328 / 四分裂之和）✓ → A1 口径正确（并入 B 维度核查）。
- test 期 TSS 落在 [0.20, 0.42] 且报告漂移+阈值敏感性 → A=60。
- test 期 TSS 落在 [0.10, 0.20)∪(0.42, 0.70] → A=30。
- test 期 TSS <0.10 或 >0.70 → A=0（>0.70 说明模型依赖 GOES 历史 persistence 信息，与论文影像基线不同源，非论文结果复现；见 A3 注记）。
- B 抽查两数：test 期 base rate 0.2943（n=43,848）；test 期 TSS（由 agent 提交代码从冻结数据重算，须与 agent 报告一致）。