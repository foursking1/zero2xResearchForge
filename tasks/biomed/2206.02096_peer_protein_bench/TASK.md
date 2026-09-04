# 科研任务：PEER「溶解度预测中预训练蛋白语言模型全面优势」关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2206.02096_peer_protein_bench`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：PEER: A Comprehensive and Multi-Task Benchmark for Protein Sequence Understanding（arXiv:2206.02096；NeurIPS 2022 Datasets and Benchmarks Track）
- 领域：biomed / 蛋白质序列理解 / 溶解度预测

## 问题（可证伪）

PEER 提出 17 个蛋白质序列理解任务的统一基准，核心论断（摘要 + §5.2 单任务学习结果，Table 3）：

1. **预训练蛋白语言模型全面最优**：在多数单个任务上，大规模预训练蛋白语言模型（ESM-1b）取得最佳性能（论文摘要）；在溶解度预测（Solubility）任务上，ESM-1b 准确率 **70.23±0.75%**，为单任务设置下最佳（除文献 SOTA DeepSol 77.0 外）。
2. **从零训练的序列编码器优于特征工程**：在溶解度任务上，从零训练的 LSTM **70.18±0.63%**、CNN **64.43±0.25%** 显著优于特征工程 DDE **59.77±1.21%** 与 Moran **57.73±1.33%**（Table 3，Sol 行）。

请基于冻结数据回答：

1. **数据装配**：解析冻结的 PEER Solubility 数据集（train/valid/test CSV），统计样本数、正负类比例、序列长度分布，说明与论文 Table 1 口径（62,478 / 6,942 / 1,999）的关系。
2. **锚复现**：实现至少 2 个模型（建议：特征工程 DDE + 从零训练的 CNN 或 LSTM；可选加一个轻量预训练蛋白语言模型如 ESM-2 8M/35M 或其特征提取），在冻结测试集上报告分类准确率（accuracy，百分比），与论文对照（DDE 59.77 / Moran 57.73 / CNN 64.43 / LSTM 70.18 / ESM-1b 70.23）。
3. **论断判定**：基于实测结果判定「预训练 PLM ≥ 从零训练编码器 > 特征工程」的排序在冻结数据上是否成立，并给定量差距。

- 结论标签（四档之一）：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结，来源/许可/checksum 见 `data/README.md`）
  - `solubility_train.csv`：62,478 条（列：`sequence,label`，label∈{0,1}，1=可溶）
  - `solubility_valid.csv`：6,942 条
  - `solubility_test.csv`：1,999 条（测试集，禁止用于训练/调参）
- 来源：PEER 官方数据集（TorchProtein / PEER_Benchmark 仓库的 `Solubility` 数据集，原始 S3 压缩包 `peerdata/solubility.tar.gz`，MD5 8a8612b7bfa2ed80375db6e465ccf77e）；本包为无损转换为 CSV 的官方 LMDB 内容
- 许可：PEER 官方仓库 LICENSE 为 Apache-2.0；数据为学术公开研究数据（论文引用要求）；详见 `data/README.md`
- SHA-256（固定）：train `7236c5c98bfbf621fa14256d6ebf8731037f26a55458778dc57ab6a31f018f76`；valid `1b01ec51e1bc625078b48307adee54a3853fb97cf8c3e55fae35c86317be179c`；test `ab535824c06d6bea13da3d9d4332ca5e26ffa00fe54260a00a21ba644beab4c8`

## 方向提示（协议建议，按此口径才能与论文锚对齐）

1. **任务定义**：二分类（可溶/不可溶），指标 accuracy（%），论文 Table 3 口径（×100 表示）。
2. **DDE 特征工程**：2-gram 二肽组成 + 期望值偏差（Dipeptide Deviation from Expected mean），配逻辑回归/GBDT 或小 MLP；固定种子。
3. **从零训练编码器**：一维 CNN（embedding/one-hot → conv → pool → MLP）或 LSTM 序列编码，交叉熵损失，Adam；序列长度截断/填充策略需说明。
4. **预训练 PLM（可选）**：可加载 `facebook/esm2_t6_8M_UR50D` 或 `esm2_t12_35M_UR50D` 提取特征/微调（CPU 可跑小模型）；若用 ESM-1b 需 GPU，非必需。
5. **评估**：只用 `data/solubility_test.csv` 评估；验证集（valid）用于早停/选超参；固定种子并写入代码；可报告 3 次重复 mean±std。

## 输出要求（提交物）

1. **`claim.md`**：三问判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从 `data/` 读取并训练/评估。
3. **`results/evidence_table.csv`**：至少含列 `model,accuracy`（每模型一行，accuracy 为测试集百分比）。
4. **`results/metrics.json`**：样本统计（train/valid/test 数、正类比例、序列长度 min/median/max）；各模型 accuracy；论文锚对照；结论标签。
5. **`report.md`**：方法（特征/模型/预处理）、结果、局限（实现与论文管线差异、未用 ESM-1b 时的代表性说明）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成/模拟数据替代。
- 禁止手工抄写论文数字作为"实测结果"；所有指标必须运行代码得到。
- 论文数值（DDE 59.77 / CNN 64.43 / LSTM 70.18 / ESM-1b 70.23 等）只能用于对照讨论。
- 测试集（1,999 条）不得参与训练、特征统计或超参选择；统计量（如 DDE 期望值）只由训练集拟合。