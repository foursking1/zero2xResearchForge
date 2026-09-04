# 科研任务：MIDOG2022「基础模型 + LoRA 有丝分裂分类」关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2508.04441_mitotic_benchmark`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Benchmarking Foundation Models for Mitotic Figure Classification（arXiv:2508.04441；MELBA 2026，DOI 10.59275/j.melba.2026-a3eb）
- 领域：biomed / 计算病理 / 有丝分裂图像分类

## 问题（可证伪）

论文在 MIDOG 2022 多肿瘤域有丝分裂图像数据集（9501 个有丝分裂图 + 11051 个难例）上评测多种基础模型（Phikon/UNI/Virchow/Virchow2/Prov-GigaPath/H-optimus-0 等）的迁移适配。核心论断：

1. **LoRA 适配优于线性探测（LinProb）**：在 MIDOG 2022 全量数据上，Virchow2-LoRA 达到 Weighted F1 0.81±0.014 / AUROC 0.89±0.011，优于同模型 LinProb（F1 0.78）与端到端 CNN（ResNet50 F1 0.78）。
2. **少量数据即接近全量性能**：LoRA/LinProb 在仅 10% 训练数据时即接近全量数据表现（如 Virchow2 LinProb 10% 时 F1 0.72，全量 0.78；论文核心主张"LoRA 用 10% 数据达到接近 100% 数据的性能"）。

请基于冻结数据回答：

1. **数据统计**：解析冻结的 MIDOG 2022 子集（4 张 PNG 图 + 官方 COCO 标注 JSON），统计有丝分裂（positive）与难例（hard negative）数量，说明与论文 9501/11051 口径的关系（本包为子集）。
2. **特征/分类实验**：用至少一个可获得的图像编码器（如 ImageNet 预训练 CNN、或任一公开病理基础模型）从冻结图像提取 patch 特征，训练一个轻量分类头（linear probe 或小 MLP），在冻结标注上报告 Balanced Accuracy 与 Weighted F1。
3. **数据效率对比（可选加分）**：比较用 10% 与 100% 冻结子集训练的分类性能差，验证"少量数据接近全量"趋势。

- 结论标签（四档之一）：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结，来源/许可/checksum 见 `data/README.md`）
  - `002.png`、`008.png`、`024.png`、`063.png`：MIDOG 2022 训练集 WSI 裁剪图（2mm² 区域，PNG，各约 65-85MB；每张含原始扫描 DPI 信息）
  - `MIDOG2022_training_png.json`：官方 MS COCO 格式标注（约 1.7MB，覆盖全部 405 例训练图：有丝分裂与难例边界框/关键点）
  - `MIDOG2022_training_png.sqlite`：官方 SlideRunner 格式标注（约 3.6MB，可选）
- 来源：Zenodo 记录 6547151（MIDOG 2022 挑战官方训练数据，PNG 版；MICCAI MIDOG 2022）
- 许可：CC-BY-4.0（Zenodo 记录元数据）
- SHA-256（固定）：见 `data/README.md`（下载完成后核对）

## 方向提示（协议建议）

1. **标注解析**：COCO JSON 结构含 `images`（file_name→id）、`annotations`（category_id：有丝分裂/难例，bbox 或关键点）；按冻结的 4 张图过滤标注。
2. **patch 提取**：每张图为 ~75MB PNG（约 10k×10k 或更高分辨率）；按标注 bbox 中心裁剪 patch（如 256×256）作为正负样本，或整图下采样 + 滑动窗口。
3. **分类器**：轻量线性探测（特征 + Logistic Regression）即可；有资源可尝试 LoRA 微调（加分项，不要求）。
4. **指标**：Balanced Accuracy、Weighted F1（论文 Table 4 口径）；报告 AUROC（可选）。

## 输出要求（提交物）

1. **`claim.md`**：三问判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本，从 `data/` 解析图像与标注并运行分类实验。
3. **`results/evidence_table.csv`**：至少含列 `model,data_fraction,balanced_acc,weighted_f1`。
4. **`results/metrics.json`**：子集正负样本统计；各模型指标；论文锚对照；结论标签。
5. **`report.md`**：方法（解析/特征/分类器）、结果、局限（4 张图子集、未用 LoRA/基础模型权重时说明）。

## 数据铁律提醒

- 只使用本包冻结数据（4 张图 + 官方标注）；禁止用合成/模拟图像替代。
- 禁止手工抄写论文数字作为"实测结果"；所有指标必须运行代码得到。
- 标注文件为官方提供（CC-BY-4.0），使用遵守署名条款。
- 论文数值（Table 4：Virchow2-LoRA F1 0.81 / AUROC 0.89 等）只能用于对照讨论。