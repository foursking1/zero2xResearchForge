# 科研任务：BenchECG「xECG 超越既往 ECG 基础模型」关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2509.10151_benchecg_xecg`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：BenchECG and xECG: a benchmark and baseline for ECG foundation models（arXiv:2509.10151）
- 领域：biomed / 心电图（ECG）/ 基础模型评测

## 问题（可证伪）

BenchECG 是统一的多数据集 ECG 基础模型基准（8 个公开数据集、10 个任务）。论文提出 xECG（xLSTM 循环模型 + SimDINOv2 自监督），核心论断：

1. **xECG 在 PTB-XL 分类任务上显著优于公开 SOTA 基础模型**：xECG AUROC 0.853±0.022 vs ST-MEM 0.702±0.020（p=0.000004）；F1 0.674±0.013 vs ST-MEM 0.436±0.036（p=0.000032）。
2. **xECG 是唯一在所有数据集/任务上都表现强的公开模型**（BenchECG score 最优，mean rank 1.2）。

请基于冻结数据回答：

1. **数据与标签**：解析冻结的 PTB-XL 数据（train/validation parquet），统计样本数、导联数、标签结构（诊断超类/子类），说明与论文 PTB-XL 任务口径（如 SCP 诊断分类）的对应。
2. **分类复现**：训练一个 ECG 分类器（建议 1D CNN / 或基于 frozen 特征 + 线性探测），在冻结测试划分上报告 AUROC 与 F1，与论文 xECG（0.853 / 0.674）及 ST-MEM（0.702 / 0.436）对照。
3. **结论判定**：在你实现的模型规模上，"先进 ECG 模型可达到 AUROC ≥0.8 / F1 ≥0.5 量级"与"此前方法（ST-MEM 等）明显更低"的差距格局是否可复现。

- 结论标签（四档之一）：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结，来源/许可/checksum 见 `data/README.md`）
  - `ptbxl_train.parquet`：PTB-XL 训练分片（约 98MB；含 12 导联信号与标签字段）
  - `ptbxl_validation.parquet`：PTB-XL 验证分片（约 99MB）
- 来源：PTB-XL（Wagner et al. 2020，公开 ECG 数据库，PhysioNet）；本包为 HuggingFace 镜像 `liyongsea/PTB-XL-small` 的 parquet 版本
- 许可：PTB-XL 为 CC BY 4.0（PhysioNet 发布）；镜像无额外许可
- SHA-256（固定）：
  - `ptbxl_train.parquet` = （下载完成后填写，见 `data/README.md`）
  - `ptbxl_validation.parquet` = （同上）

## 方向提示（协议建议）

1. **标签口径**：论文 PTB-XL 任务为多标签诊断分类（SCP 语句超类：NORM/MI/STTC/CD/HYP 等），指标用宏平均 AUROC 与 F1；冻结 parquet 的标签字段以实际 schema 为准。
2. **信号预处理**：PTB-XL 为 100Hz、10 秒、12 导联；降采样/归一化按常规做法并写入代码。
3. **模型**：轻量 1D CNN 或 RNN 即可（无需复刻 xLSTM）；重点是评估口径与论文一致（macro AUROC / F1）。
4. **评估**：在冻结验证分片上评估（论文用 5 次重复训练报 mean±std；可只跑 1-3 次并说明）。

## 输出要求（提交物）

1. **`claim.md`**：三问判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从 `data/` 读取并训练/评估。
3. **`results/evidence_table.csv`**：至少含列 `model,metric,value`（AUROC/F1，可含重复次数）。
4. **`results/metrics.json`**：样本/标签统计；模型指标；论文锚对照（绝对差）；结论标签。
5. **`report.md`**：方法（预处理/模型/指标口径）、结果、局限（冻结子集、模型规模、与 xLSTM 差异）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成/模拟信号替代。
- 禁止手工抄写论文数字作为"实测结果"；所有指标必须运行代码得到。
- 论文数值（xECG AUROC 0.853 / F1 0.674、ST-MEM 0.702 / 0.436）只能用于对照讨论。
- 信号处理统计量（归一化均值/方差）只允许由训练划分拟合。