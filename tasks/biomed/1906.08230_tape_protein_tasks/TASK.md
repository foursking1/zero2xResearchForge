# 科研任务：TAPE「自监督预训练提升蛋白质工程任务性能」关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`1906.08230_tape_protein_tasks`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Rao et al., "Evaluating Protein Transfer Learning with TAPE", NeurIPS 2019（arXiv:1906.08230）
- 领域：biomed / 蛋白质机器学习 / 预训练表示

## 问题（可证伪）

TAPE 论文的核心论断：**自监督预训练的蛋白质表示（相比 one-hot 等手工编码）能显著提升下游蛋白质工程任务的预测性能**。论文在 Fluorescence（预测 GFP 突变体荧光，Spearman ρ）与 Stability（预测蛋白稳定性，Spearman ρ）两个任务上报告：one-hot 基线 Fluorescence ρ=0.14 / Stability ρ=0.19；预训练 Transformer/LSTM/UniRep 等达到 Fluorescence 0.67-0.68、Stability 0.69-0.73。

请基于冻结数据回答：

1. **数据与任务**：解析冻结的 TAPE Fluorescence（51,715 条，GFP 突变体，标签为 log 荧光）与 Stability（68,977 条，蛋白突变体稳定性）数据，说明 train/test 划分结构（荧光任务：训练靠近野生型的小邻域、测试更远突变；稳定性任务：训练广谱蛋白、测试最佳蛋白的单突变邻域）。
2. **两类表示对比**：实现并训练
   - **预训练/可学习表示**（推荐：冻结的 ESM-2 或 ESM-1b 蛋白质语言模型嵌入 + 回归头；或自训一个小型掩码语言模型）；
   - **手工编码基线**（one-hot 序列 + 线性/MLP，或氨基酸组成特征 + RF/GBDT）。
   用 Spearman ρ 评估测试集。
3. **验证论断**：预训练表示是否在 Fluorescence 与 Stability 上都显著优于 one-hot 基线？给出两任务的 ρ 对照与四档结论。

- 结论标签：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结）→ 物理位置 `$PAPER_BENCH_DATA_DIR`（来源/许可/逐文件 SHA-256 见 `data/SOURCE.md` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 文件：`fluorescence_dataset.csv`（列 `protein,label,stage`，stage=train/test；label 为 log 荧光）、`stability_dataset.csv`（列 `protein,label,stage`；label 为稳定性分数）、`*_metadata.json`。
- 来源：TAPE 官方数据集（GitHub songlab-cal/tape，从原始实验文献整理）；许可：TAPE 仓库 MIT（数据来自公开文献：Sarkisyan et al. 2016 荧光、Rocklin et al. 2017 稳定性）。
- 规模：两 CSV 共 ~17MB；嵌入 + 回归头 CPU 可完成（若用 ESM 嵌入需下载模型权重，允许；若资源受限可用 5,000-10,000 条子集，固定种子并声明）。

## 方向提示（协议建议）

1. **预训练表示**：用 HuggingFace `facebook/esm2_t6_8M_UR50D` 或 `esm2_t33_650M_UR50D` 提取每序列最后一层嵌入（平均池化），接线性/2 层 MLP 回归头（训练 5-30 epoch，早停按验证或测试前的小验证集）。也可用 `TAPE` 原库的 `bepler`/`unirep` 嵌入。
2. **one-hot 基线**：one-hot（20 维/位点）+ 序列平均或 CNN 1D；或氨基酸组成 + Ridge/GBDT。与预训练表示同一数据、同一评估（Spearman ρ on test）。
3. **评估**：Spearman rank correlation（scipy）；报告 Fluorescence 与 Stability 各自的 ρ。
4. **对照**：论文 Table 2（Fluorescence：one-hot 0.14、no-pretrain ResNet -0.28、pretrain Transformer 0.68/LSTM 0.67、UniRep 0.67；Stability：one-hot 0.19、pretrain Transformer 0.73/LSTM 0.69/ResNet 0.73、UniRep 0.73）——只能对照讨论，禁止抄为实测。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从冻结数据读取并完成训练与评估。
3. **`results/evidence_table.csv`**：至少含列 `task,representation,model,spearman_rho,rmse`（每任务 × 每表示一行）。
4. **`results/metrics.json`**：样本统计、各方法 ρ、预训练 vs one-hot 差值、论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（子集/嵌入模型差异 vs 论文、train/test 结构与论文的一致性）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止合成蛋白质序列或模拟标签。
- 禁止手工抄写论文数字作为「实测结果」；所有指标必须运行代码得到。
- 论文数值（Table 2 的 ρ）只能用于对照讨论。
- 两种表示必须在同一 train/test 划分、同一评估协议下比较。
