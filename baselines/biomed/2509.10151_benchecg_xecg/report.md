# Report — BenchECG / xECG「PTB-XL 分类超越」论断验证

- task_id：`2509.10151_benchecg_xecg`
- 论文：BenchECG and xECG: a benchmark and baseline for ECG foundation models（arXiv:2509.10151）
- 核心论断：xECG（xLSTM+SimDINOv2）在 PTB-XL 诊断分类上显著优于公开 SOTA（ST-MEM）：AUROC 0.853±0.022 vs 0.702±0.020（p=0.000004）；F1 0.674±0.013 vs 0.436±0.036（p=0.000032）。
- 本报告结论：**`inconclusive`**。

---

## 1. 背景与目标

按任务书要求，基于冻结数据回答三问：

1. 数据与标签：样本数、导联数、标签结构，及其与论文 PTB-XL 诊断任务口径的对应；
2. 分类复现：训练 ECG 分类器，在冻结验证划分上报告 AUROC 与 F1，对照 xECG（0.853/0.674）与 ST-MEM（0.702/0.436）；
3. 结论判定：四档标签（supported / partially_supported / contradicted / inconclusive）。

## 2. 方法

### 2.1 数据审计

- 读取冻结 parquet（`ptbxl_train.parquet` 98,529,320 B；`ptbxl_validation.parquet` 99,278,438 B），SHA-256 与 `data/README.md` 完全一致。
- **关键发现：实际 schema 为 `[ecg_id (int64), age (int32), sex (string), ecg_array (list<list<float>>)]`，不含任何标签列。** `ecg_array` 逐条解析为 `[5000, 12]` float32（5000 采样 × 12 导联；10 s @ 500 Hz，即 PTB-XL 原生采样率）。两分片之间无 ecg_id 重叠。
- 因此论文任务描述中的「SCP 语句超类（NORM/MI/STTC/CD/HYP）标签字段」在本冻结包内**不存在**；诊断超类/子类监督目标无法从冻结数据重构。这是全部后续判断的事实基础。

### 2.2 预处理（防泄漏）

1. 500 Hz → 100 Hz：按 5 倍 box-car 均值降采样（官方 100 Hz 版本等价设置）。
2. 逐导联 z-score 归一化，**均值/方差仅在训练划分上拟合**（`results/preprocessing.json` 记录拟合统计量），再应用于训练与验证两划分。
3. 全流程固定种子（`SEED=42`），辅助目标（sex、age≥65）在冻结 schema 内直接构造。

### 2.3 模型与训练

由于诊断标签缺失，任何「诊断分类」模型都无从训练/评估。为满足「给出可验证、可复算的实质结果」，我们在同一冻结信号与划分上，对冻结包内唯一真实的两个标签构造了两个模型：

- **Model A — Simple1DCNN**（`code/common.py`）：`Conv1d(9)→GELU→BN→MaxPool(4)→Conv1d(7)→GELU→BN→MaxPool(4)→Conv1d(5)→GELU→BN→MaxPool(4)→AdaptiveAvgPool→Linear(2)`，2 个独立 BCE 头（sex、age≥65），batch=32，AdamW(lr=1e-3, wd=1e-4)，30 epochs，纯 CPU，3 个种子（42/2024/7）重复。
- **Model B — 手工特征逻辑回归**：每导联 mean/std/min/max/RMS（12×5=60 维）→ `LogisticRegression(C=1.0)`，同一训练/验证划分，作为浅层基线。

### 2.4 评估口径（与论文对齐的机制）

- 多标签 **macro AUROC**：per-class one-vs-rest AUROC 的均值（`sklearn.metrics.roc_auc_score`）。
- **macro F1**：per-class F1（阈值 0.5）均值；另附 per-class Youden 最优阈值 F1 作为次级视角。
- 评估只在冻结验证划分上进行；重复次数与种子如实记录。

## 3. 结果

### 3.1 数据（Q1）

| 指标 | 训练 | 验证 |
|---|---|---|
| 记录数 | 1000 | 1000 |
| 导联 | 12 | 12 |
| 采样/导联 | 5000（100 Hz 后 1000） | 5000（100 Hz 后 1000） |
| 诊断标签列 | **无** | **无** |
| 可用列 | ecg_id, age, sex, ecg_array | 同 |

### 3.2 模型指标（Q2，辅助目标口径；`results/model_metrics.json`）

| 模型 | macro AUROC | macro F1@0.5 | sex AUROC | age≥65 AUROC |
|---|---|---|---|---|
| Simple1DCNN（3 seeds） | **0.8171 ± 0.0029** | **0.7104 ± 0.0205** | 0.8338 ± 0.0038 | 0.8004 ± 0.0021 |
| LogReg（手工特征） | 0.7237 | 0.6377 | 0.7156 | 0.7318 |

（跨类 F1 为 two-label macro；`results/evidence_table.csv` 给出逐模型逐指标。）

### 3.3 与论文锚的对照（Q2/Q3）

| | 论文锚（诊断超类，Table 2） | 本实验（辅助目标，不可直接比较） |
|---|---|---|
| xECG AUROC / F1 | 0.853±0.022 / 0.674±0.013 | —（无法计算） |
| ST-MEM AUROC / F1 | 0.702±0.020 / 0.436±0.036 | —（无法计算） |
| 本实验 CNN / LR（self-check） | — | 0.8171±0.0029 / 0.7237 |

- 论文诊断任务的 AUROC/F1 与显著性检验（p 值）**无法在当前冻结数据上重算**：没有诊断标签，无法训练分类器、无法计算任何诊断口径指标，更无从比较两个模型。
- 结构对照：同一冻结数据上深度模型（0.817）也高于浅层基线（0.724），与论文「先进模型 >> 先前方法」的**结构方向**一致；但目标不同（性别/年龄 vs 诊断），故仅作方向性说明，不作为支持证据。

## 4. 结论判定

**`inconclusive`。** 依据（逐条对应任务书三问）：

1. 数据与标签：样本 2000（1000/1000）、12 导联、10 s；**诊断超类/子类标签在冻结 schema 中缺失**，与论文 SCP 超类分类口径无法对应。
2. 分类复现：诊断口径 AUROC/F1 不可得；仅辅助目标上可端到端复算（CNN 0.817/0.710，LR 0.724/0.638），且它们与 0.853/0.674、0.702/0.436 **非同任务、不可比**。
3. 判定：既无证据支持、也无证据反驳论文论断；证据不足即为 inconclusive。

## 5. 局限

1. **标签缺失（首要）**：冻结包无诊断标签，监督诊断任务不可行；这是比「模型规模」更硬性的限制。
2. 子集规模：train+val 仅 2,000 条（PTB-XL 全量 21,837 条的 <10%），与论文数据规模/难度差异很大。
3. 模型差异：提交的是轻量 1D-CNN 与逻辑回归，非论文的 xLSTM+SimDINOv2 预训练模型；即使有标签，也预期与 0.853 有差距。
4. 重复次数：CNN 3 seeds（论文为 5 次），std 略高属正常；辅助目标无需更多重复。
5. 未尝试联网获取 PTB-XL 官方 label 元数据（违反「只使用冻结数据」约束），故不提供任何外部标签注入。

## 6. 补充说明（数据铁律遵守情况）

- 全部数值来自脚本实测（`code/`），未手工抄写论文数字作为实测值；
- 未使用合成/模拟信号；
- 归一化统计量仅由训练划分拟合并在代码中固化；
- 冻结包 SHA-256 与 `data/README.md` 一致（附于 `results/data_audit.json`）。

## 7. 复现入口

`code/README.md` 提供逐步命令；从原始 parquet 到指标、图表的全链路约 5 分钟（CPU）。关键产物：

- `results/data_audit.json`（Q1）
- `results/model_metrics.json`、`results/evidence_table.csv`、`results/metrics.json`（Q2/Q3 + B 抽查字段）
- `results/preprocessing.json`（归一化统计量，防泄漏凭证）
- `results/fig_ecg_example.png`、`results/fig_roc_curves.png`、`results/fig_model_compare.png`（图）