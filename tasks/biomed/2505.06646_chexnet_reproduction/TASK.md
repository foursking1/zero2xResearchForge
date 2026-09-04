# 科研任务：胸部 X 光 14 类疾病多标签分类（L2 端到端科研再发现）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2505.06646_chexnet_reproduction`
- 层级：L2（端到端科研再发现，RCBench 三段式：input / output / scientific goal；目标论文隐藏）
- 论文线索：arXiv:2505.06646（一篇关于经典胸部 X 光疾病分类模型的**开源复现与增强**研究）
- 领域：biomed / 医学影像 / 多标签分类

## 任务描述（input / output / scientific goal）

- **Input**：NIH ChestX-ray14 胸部 X 光图像冻结子集（`data/`）。每张图像可同时含 14 种胸部疾病标签中的任意组合（多标签二分类），另有 `No Finding` 类（约 50% 图像无异常）。冻结包含一个测试 parquet（约 1,279 样本中的一个分片）与一个训练 parquet（约 4,326 样本中的一个分片），以图像+标签列存储。
- **Output**：训练一个基于 ImageNet 预训练 DenseNet-121 的多标签分类模型（复现经典 CheXNet 架构：全局平均池化 + 14 个 sigmoid 输出），在冻结测试集上输出 14 类各自的 ROC-AUC 与 F1（含阈值优化），以及平均 AUC / 平均 F1。
- **Scientific goal**：复现并验证该论文的核心论断——**在 NIH ChestX-ray14 上，基于 DenseNet-121 的复现模型能达到较高平均 AUC（约 0.8 量级），但由于类别极不平衡与标注噪声，平均 F1 明显偏低（约 0.1-0.4 量级）**；并对比「仅复现」与「加入现代训练技巧（如 Focal Loss、AdamW、数据增强、逐类 F1 阈值优化）」两种设置的表现差异。

## 数据说明

- 数据包：`data/`（冻结，来源/许可/checksum 见 `data/README.md`）
  - `nih_train-00000.parquet`：训练分片（NIH ChestX-ray14 小镜像的 train 分片之一；字段含 `image`（图像字节）与 `labels`（14 类多标签序列））
  - `nih_test-00000.parquet`：测试分片（同上，test 分片之一）
- 来源：NIH ChestX-ray14（美国国立卫生研究院临床中心公开数据集，Wang et al. 2017）；本包为 HuggingFace 公开镜像 `Sohaibsoussi/NIH-Chest-X-ray-dataset-small` 的 parquet 分片（原数据集官方还托管于 Kaggle/NIH Box）
- 许可：NIH ChestX-ray14 为 NIH 公开发布的研究用途数据集（无正式 OSS 许可证，公开下载、研究使用）；HF 镜像无额外许可声明。使用需注明出处与 NIH 数据条款
- SHA-256（固定，下载完成后核对）：
  - `nih_train-00000.parquet` 与 `nih_test-00000.parquet` 见 `data/README.md`

## 方向提示（协议建议）

1. **标签**：14 类多标签（Atelectasis, Cardiomegaly, Effusion, Infiltration, Mass, Nodule, Pneumonia, Pneumothorax, Consolidation, Edema, Emphysema, Fibrosis, Pleural_Thickening, Hernia）；以 `labels` 列为目标。
2. **模型**：ImageNet 预训练 DenseNet-121，替换分类头为 14 输出 sigmoid；输入 224×224。
3. **训练**：建议 AdamW + BCE（或 Focal Loss）微调若干 epoch；固定随机种子并写入代码；报告 train/val/test 划分（冻结包内已有官方 test 分片，训练可从 train 分片内再切 val）。
4. **评估**：每类 ROC-AUC；每类 F1 在最优（或 0.5）阈值下；报告 14 类平均。类别不平衡下注意稀有类（如 Hernia）的 F1 极低是预期现象。
5. **增强（可选对照）**：Focal Loss、ColorJitter 等增强、逐类阈值优化——用于回答"现代技巧是否提升 F1"。

## 输出要求（提交物）

1. **`claim.md`**：论断判定（`supported` / `partially_supported` / `contradicted` / `inconclusive`）与关键数字（平均 AUC / 平均 F1；复现版 vs 增强版）。
2. **`code/`**：完整可复现脚本（固定种子），从 `data/` 读取图像与标签并训练/评估。
3. **`results/evidence_table.csv`**：至少含列 `model,class,auc,f1`（每模型×每类一行），并附 `mean_auc,mean_f1` 汇总行。
4. **`results/metrics.json`**：测试样本数；14 类平均 AUC/F1；复现版与增强版对照；结论标签。
5. **`report.md`**：方法（模型/训练/阈值/划分）、结果、局限（冻结子集与全量数据差异、图像分辨率、训练时长）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成/模拟图像替代。
- 禁止手工抄写论文数字作为"实测结果"；所有指标必须运行代码得到。
- 测试分片不得参与训练或阈值优化（阈值优化只能用 val；若只用 test 评估则固定 0.5 阈值并说明）。
- 本任务目标论文不公开提供全文；请以冻结数据自行完成端到端再发现。