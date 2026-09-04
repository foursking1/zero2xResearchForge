# 科研任务：QU-BraTS「不确定性量化评分与分割排名解耦」关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2112.10074_qubrats_uncertainty_seg`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：QU-BraTS: MICCAI BraTS 2020 Challenge on Quantifying Uncertainty in Brain Tumor Segmentation（MELBA 2022:026）
- 领域：biomed / 医学影像 / 脑肿瘤分割不确定性

## 问题（可证伪）

QU-BraTS 2020 挑战（14 支队伍参与）提出不确定性评估分数：对每个肿瘤分区（ET/TC/WT）在预设不确定性阈值下计算
score = AUC1 + (1 − AUC2) + (1 − AUC3)，其中 AUC1/AUC2/AUC3 分别为"分割质量保持度（DSC AUC）、过滤真阳性保持度（FTP AUC）、过滤真阴性保持度（FTN AUC）"。核心论断：

1. **不确定性排名与分割精度排名显著不同**：QU-BraTS 排名第 1 的队伍（Team SCAN，全患者 NRS ≈ 0.14）在 BraTS 2020 分割任务（78 队）中仅排第 4；排名提供分割精度之外"互补信息"（论文 Table 2 / Figure 3）。
2. **好的不确定性应当能通过阈值过滤掉错误预测**：不确定性过滤应在保持真阳性的同时清除假阳性/假阴性（FTP/FTN 曲线）。

请基于冻结数据回答：

1. **数据与基准**：解析冻结的 BraTS 2021 mini 数据（10 例 NIFTI 多模态 MRI + 分割标注），说明与论文 BraTS 2020 队列（369 训练例）的关系。
2. **不确定性方法**：在冻结数据上实现至少一种不确定性量化方法（推荐 MC-Dropout 或 Deep Ensemble），训练/微调一个小型 3D U-Net 做肿瘤分割（可简化为 WT 二类或 3 类），输出每体素不确定性图。
3. **QU-BraTS 分数**：按论文公式计算阈值过滤下的 AUC1/AUC2/AUC3 与 score，并报告：不确定性过滤是否提升"决策可靠性"（如在高不确定性阈值下 FPR 下降、TPR 保持）；给出至少两个模型（或两个种子）的排名对比，验证"不确定性排名 ≠ 分割精度排名"。

- 结论标签（四档之一）：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结，来源/许可/checksum 见 `data/README.md`）
  - `brats2021_mini.parquet`：BraTS 2021 训练数据 10 例子集（HF 镜像 `anhaltai/brats2021_mini`；含 `image`（NIFTI 多模态）与 `annotations`（NIFTI 分割）字段；约 24.8MB）
- 来源：BraTS 2021 数据（Zenodo 记录 19541844，CC-BY-4.0）；QU-BraTS 论文使用 BraTS 2020 数据（注册制），本任务以同源公开 BraTS 2021 数据为冻结替代
- 许可：BraTS 2021 zenodo 记录为 CC-BY-4.0（官方声明）；使用请遵守 BraTS 数据条款
- SHA-256（固定）：见 data/README.md（brats2021_mini.parquet 已固定）


## 方向提示（协议建议）

1. **数据解析**：parquet 中 `image`/NIFTI 可用 `nibabel` 读取（多模态 T1/T1ce/T2/FLAIR 4 通道或 4 个文件）；标注为 WT/TC/ET 三类（BraTS 惯例：ET=4、TC=1+4、WT=1+2+4，以实际标注为准）。
2. **简化口径**：10 例数据规模小——可用 2D 切片训练或 patch 训练；建议以 WT（whole tumor）二类为主口径报告，3 类为加分项。
3. **不确定性**：MC-Dropout（推理时多次随机失活取方差/熵）实现简单；Deep Ensemble 为加分项。不确定性需归一化到 0-100（论文口径）。
4. **评分**：按论文 §3 公式在测试切片上计算阈值 τ（如 100/75/50/25）下的 DSC、FTP、FTN，画曲线求 AUC1/AUC2/AUC3 并合成 score。
5. **排名对比**：用分割 DSC 排名 vs QU-BraTS score 排名对比两个模型/两个种子。

## 输出要求（提交物）

1. **`claim.md`**：三问判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从 `data/` 读取并训练/评估。
3. **`results/evidence_table.csv`**：至少含列 `model,auc1,auc2,auc3,score,dice`（每模型/种子一行）。
4. **`results/metrics.json`**：样本统计；各模型 score 与 DSC；不确定性排名 vs 分割排名；论文锚对照；结论标签。
5. **`report.md`**：方法（预处理/模型/不确定性/阈值过滤）、结果、局限（BraTS2021 子集 vs BraTS2020、2D/3D 口径、简化分区）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成/模拟图像替代。
- 禁止手工抄写论文数字作为"实测结果"；所有指标必须运行代码得到。
- 论文数值（SCAN NRS ≈0.14、排名结构等）只能用于对照讨论。
- 测试与训练划分需固定；不确定性阈值只在测试集上评估，不得用于训练。