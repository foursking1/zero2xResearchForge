# 科研任务：物理感知 GNN「OOD 泛化提升」关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2606.12651_physics_aware_gnn_ood`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：物理感知图神经网络在分布外分子上的泛化（Physics-Aware GNN for Out-of-Distribution Molecular Property Prediction，arXiv:2606.12651）
- 领域：biomed / AI4Science / 分子性质预测 OOD

## 问题（可证伪）

论文的核心论断是：在由 HIV/Tox21/COCONUT 构成的 65,177 分子语料（按 SAScore 阈值标注 easy/hard）上，向 GINE 基座模型加入「复杂度（complexity）与分子应变（strain）物理感知辅助损失」的三种变体（+complexity、+strain、+both），在单源 OOD 测试划分（以 COCONUT 天然产物为目标语料）上的 ROC-AUC 均显著高于基线（mean OOD AUC 0.9774），且每个配对 bootstrap 置信区间不包含 0：

- +complexity：Δ=+0.0060（95% CI [+0.0023, +0.0102]）
- +strain：Δ=+0.0032（95% CI [+0.0008, +0.0052]）
- +both：Δ=+0.0066（95% CI [+0.0038, +0.0093]，组合最优）

请基于冻结数据回答：

1. **基线复现**：在冻结的 HIV/Tox21 训练语料与 COCONUT OOD 测试语料上，训练 GINE 基线（分子图二分类 easy/hard），报告 OOD 测试 AUC，与论文基线 0.9774 对照。
2. **消融对比**：实现至少一个物理感知变体（如 +both 或 +complexity），在相同 OOD 划分下报告 AUC 差 Δ 与配对 bootstrap 置信区间（5 个种子），验证「显著提升且 CI 不含 0」。
3. **标签忠实性**：用 SAScore 阈值（<4 → easy，>5 → hard，中间带丢弃）验证冻结数据的标签分布（easy/hard 比例），与论文 53,159/12,018（82/18）对照。

- 结论标签（四档之一）：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结，来源/许可/checksum 见 `data/README.md`）
  - `HIV.csv`：MoleculeNet HIV 数据（41,127 行；含 SMILES 与标签列，已按论文口径标注 easy/hard 或提供 SAScore 供自标注）
  - `tox21.csv.gz`：MoleculeNet Tox21 数据（7,831 行）
  - `COCONUT_30k_seed42.csv`：COCONUT 天然产物库按 seed=42 抽样的 30,000 分子子集（官方 2026-08 lite 全库 738,827；此处为固定种子子样本，用于 OOD 测试语料）
- 来源：MoleculeNet（HIV/Tox21）官方发布 + COCONUT（natural products）官方数据库（`coconut.naturalproducts.net`）；标签管线为论文 SAScore 阈值法
- 许可：MoleculeNet 数据为学术公开数据（DeepChem 发布）；COCONUT 为开放数据库（CC BY 4.0 / 学术公开条款，见 `data/README.md`）
- SHA-256（固定）：
  - `HIV.csv` = `9FFA7FE57DC86C342627EE1D5255E937E2AB812393C73C4D16C697022F6E1D22`
  - `tox21.csv.gz` = `45D09792492CE049039DD24AA27B07FC79CE20C573187D4D90BCD178C0C0D360`
  - `COCONUT_30k_seed42.csv` = `223CD29C86B0DE426652A3BCC9446439DE28ACCFCA7416EC7DE5CD42082ED5A0`

## 方向提示（协议建议）

1. **标签**：SAScore < 4 → easy（label 1），> 5 → hard（label 0），4-5 之间丢弃；若冻结 CSV 已含 `label`/SAScore 列请直接核对（RDKit 的 SAScore 可用 `sascorer` 计算，需 RDKit）。
2. **划分**：训练/验证 = HIV+Tox21（按论文随机 80/10 或 80/20，固定种子）；OOD 测试 = COCONUT 子集（论文口径：COCONUT 天然产物为"hard"分布，单源 OOD）。论文 COCONUT 测试规模 5,026（easy 1,326 / hard 3,700），以冻结子集实际可划分样本为准。
3. **模型**：GINE（图同构网络 + 边特征）或等价的图神经网络；5 个随机种子；评估 ROC-AUC。
4. **统计**：配对 bootstrap（对 5 个同种子 Δ 重采样 10,000 次）给出 95% CI；报告是否排除 0。
5. **标注口径差异**：论文将 hard 阈值从常规 6 放宽到 5（原因：严格阈值只剩 ~1,158 个 hard 分子）；报告中说明你的口径。

## 输出要求（提交物）

1. **`claim.md`**：三问判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从 `data/` 读取并重算标签、AUC、Δ、CI。
3. **`results/evidence_table.csv`**：至少含列 `variant,seed,ood_auc,delta,ci_low,ci_high`（基线 + 每个实现的变体）。
4. **`results/metrics.json`**：语料规模与标签分布；基线 OOD AUC；各变体 Δ 与 CI；论文锚对照（相对差/区间包含）；结论标签。
5. **`report.md`**：方法（标签/划分/模型/统计）、结果、局限（SAScore 口径、子集规模、是否用 +both 等）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成/模拟数据替代（SAScore 计算为确定性闭式打分，允许用于标签复现）。
- 禁止手工抄写论文数字作为"实测结果"；所有指标必须运行代码得到。
- OOD 测试语料（COCONUT）不得进入训练/验证；禁止用 COCONUT 做超参选择。
- 论文数值（基线 0.9774、Δ 与 CI）只能用于对照讨论。