# 科研任务：MedMNIST v2「轻量医学图像基准」关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2110.14795_medmnist_v2`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Yang et al., "MedMNIST v2: A Large-Scale Lightweight Benchmark for 2D and 3D Biomedical Image Classification", Scientific Data 2023（arXiv:2110.14795）
- 领域：biomed / 医学图像分类 / 轻量基准

## 问题（可证伪）

MedMNIST v2 论文提出标准化轻量医学图像分类基准（28×28，2D 12 数据集 + 3D 6 数据集），并报告 ResNet-18 等基线在 AUC/ACC 上的性能。核心论断：**轻量（28×28）医学图像分类任务上，标准 CNN（ResNet 等）能达到高性能（多数数据集 AUC≥0.90），不同数据集难度差异巨大（如 BloodMNIST AUC 0.998 vs RetinaMNIST 0.717）**；AutoML 与 ResNet 基线性能接近。

请基于冻结数据回答：

1. **数据与任务**：解析冻结的 5 个 MedMNIST2D 数据集（BloodMNIST 8 类、BreastMNIST 2 类、DermaMNIST 7 类、PneumoniaMNIST 2 类、RetinaMNIST 5 类；各含 train/val/test 的 28×28 图像与标签），统计各类别样本数。
2. **分类模型**：实现并训练一个标准 CNN（ResNet-18 或更小 CNN，如 2-3 卷积块 + MLP）在 5 个数据集上（各任务独立训练），报告 test AUC 与 ACC。
3. **验证论断**：各数据集 AUC 是否与论文量级一致（Blood≥0.99、Breast≥0.90、Derma≥0.90、Pneumonia≥0.94、Retina 0.70-0.75）？数据集间难度排序是否与论文一致？给出对照表与四档结论。

- 结论标签：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结）→ 物理位置 `$PAPER_BENCH_DATA_DIR`（来源/许可/逐文件 SHA-256 见 `data/SOURCE.md` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 文件（npz，键 `train_images/train_labels/val_images/val_labels/test_images/test_labels`）：
  - `bloodmnist.npz`（8 类，train 11,959 / val 1,712 / test 3,421，28×28×3）
  - `breastmnist.npz`（2 类，train 546 / val 78 / test 156，28×28）
  - `dermamnist.npz`（7 类，train 7,007 / val 1,003 / test 2,005，28×28×3）
  - `pneumoniamnist.npz`（2 类，train 4,708 / val 524 / test 624，28×28）
  - `retinamnist.npz`（5 类，train 1,080 / val 120 / test 400，28×28×3）
- 来源：MedMNIST v2 官方（Zenodo/HF medmnist）；许可：CC BY 4.0（官方声明）。原始数据来自公开医学数据集（Blood Cell Count、BREAST、DermaMNIST、Pediatric Pneumonia Chest X-ray、Retina）。
- 规模：~60MB；5 个独立小任务 CPU 可完成（每任务 10-30 epoch）。

## 方向提示（协议建议）

1. **读取**：`numpy.load` npz；图像归一化到 [0,1]（或按数据集均值/方差）。
2. **模型**：ResNet-18 或小 CNN（Conv-BN-ReLU ×2-3 + 全局池化 + 分类头）；Adam + CrossEntropy；early stopping 按 val AUC；测试集只评估一次。
3. **指标**：多类用 macro-averaged one-vs-rest AUC（MedMNIST 官方口径）与 ACC。
4. **对照**：论文 Table 3 ResNet-18@28（BloodMNIST AUC 0.998/ACC 0.958；BreastMNIST 0.901/0.863；DermaMNIST 0.917/0.735；PneumoniaMNIST 0.944/0.854；RetinaMNIST 0.717/0.524）——只能对照讨论，禁止抄为实测。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从冻结 npz 读取并完成训练与评估。
3. **`results/evidence_table.csv`**：至少含列 `dataset,n_classes,train_size,test_size,model,auc,acc`（每数据集一行）。
4. **`results/metrics.json`**：各类别计数、各数据集 AUC/ACC、vs 论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（模型/超参差异 vs 论文、多类 AUC 口径）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用 MedMNIST 在线下载的其他版本或合成图像。
- 禁止手工抄写论文数字作为「实测结果」。
- 测试集禁止参与训练/调参/早停。
