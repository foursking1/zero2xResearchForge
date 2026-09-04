# solution.md — 方法说明与结果

任务：验证 BenchECG 论文「xECG 在 PTB-XL 分类上超越既往 ECG 基础模型」的关键论断（L1，task `2509.10151_benchecg_xecg`）。
结论标签：**`inconclusive`**（理由见下：冻结数据无诊断标签）。

## 一句话结论

冻结的 PTB-XL-small 数据（train/val 各 1,000 条 12 导联 ECG, 10 s @500 Hz）**实际 schema 中没有任何诊断标签列**，无法按论文口径（SCP 超类多标签分类，macro AUROC / F1）做监督复现；xECG 0.853/0.674 vs ST-MEM 0.702/0.436 的差距因此在本冻结包内无法重新验证 → 判定 **inconclusive**。为交付可复现、可核查的实质工作，我们在同批冻结信号上、对冻结包内真实存在的标签（sex、age≥65）跑通了完整的多标签评估管线（CNN vs 浅层基线），所有数字均为脚本实测。

## 数据与预处理

- 解析 `ptbxl_train.parquet` / `ptbxl_validation.parquet`（SHA-256 已核对冻结）。
- 信号张量 `[1000, 5000, 12]` float32，无 NaN，训练/验证 ecg_id 零重叠。
- 预处理：500 Hz → 100 Hz 降采样（box-car 均值滤波，因子 5），逐导联 z-score；**均值/方差只由训练划分拟合**（防泄漏，见 `results/preprocessing.json` 中的拟合统计量）。
- 标签：冻结 schema 无诊断标签列（`label_like_columns_found=[]`）；辅助目标构造 sex（binary）与 age≥65（binary），正类计数见 `results/metrics.json`。

## 模型与评估（辅助目标口径，均 CPU、固定种子 42/2024/7）

| 模型 | macro AUROC | macro F1@0.5 | 实现 |
|---|---|---|---|
| Simple1DCNN（12→64→128→128，GELU+BN+MaxPool+AdaptiveAvgPool，2 个 BCE 头） | **0.8171 ± 0.0029** | **0.7104 ± 0.0205** | `code/common.py::Simple1DCNN`，30 epochs, AdamW lr=1e-3 |
| 逻辑回归（每导联 mean/std/min/max/RMS 手工特征, 60 维） | 0.7237 | 0.6377 | `sklearn.LogisticRegression C=1.0` |

- 指标口径：与论文一致的多标签 **macro AUROC**（per-class one-vs-rest 均值）与 **macro F1（阈值 0.5）**；另附 Youden 最优阈值 F1 作次级视角。
- 评估：固定冻结验证划分（不在冻结训练划分上过拟合选择）；报告 3 seeds 均值±std。

## 与论文锚的对照（仅讨论，不作实测值）

| 指标 | xECG（论文） | ST-MEM（论文） | 本实验 |
|---|---|---|---|
| PTB-XL 诊断 macro AUROC | 0.853±0.022 | 0.702±0.020 | **NA**（无诊断标签） |
| PTB-XL 诊断 macro F1 | 0.674±0.013 | 0.436±0.036 | **NA**（无诊断标签） |
| 辅助目标 macro AUROC（self-check） | — | — | CNN 0.8171±0.0029 vs LR 0.7237 |

「深度模型 (0.817) > 浅层基线 (0.724)」的格局与论文「先进模型 >> 先前方法」的**结构方向一致**，但辅助目标≠诊断任务，不构成支持性证据；同时本子集远小于论文口径，故结论为 **inconclusive**。

## 复现

见 `code/README.md`（运行顺序：`01_audit_data.py → 02_preprocess.py → 03_train_models.py → 04_figures.py → 05_export_evidence.py`）。全部代码只读取冻结数据，纯 CPU，约 5 分钟跑完。