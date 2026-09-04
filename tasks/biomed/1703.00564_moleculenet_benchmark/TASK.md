# 科研任务：MoleculeNet「可学习分子表示优于传统指纹特征」关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`1703.00564_moleculenet_benchmark`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Wu et al., "MoleculeNet: A Benchmark for Molecular Machine Learning", Chem. Sci. 9:513-530, 2018（arXiv:1703.00564）
- 领域：biomed / 化学信息学 / 分子性质预测基准

## 问题（可证伪）

MoleculeNet 论文的核心论断：**可学习分子表示（图神经网络等）在分子性质预测上"总体上"优于传统指纹/手工特征基线，但在数据稀缺与类别高度不平衡的任务上仍吃力；对量子力学与生物物理类数据集，物理感知特征的重要性可能超过算法选择**。论文在 HIV、BACE、BBBP、ClinTox 等分类任务上用 ROC-AUC 评估，在 ESOL/FreeSolv/Lipophilicity 等回归任务上用 RMSE 评估。

请基于冻结数据回答：

1. **数据与基准**：解析冻结的 7 个 MoleculeNet 数据集（HIV/BACE/BBBP/ClinTox 分类 + ESOL/FreeSolv/Lipophilicity 回归，均为真实实验/文献数据），统计各数据集样本数与正例比例。
2. **两类方法对比**：实现并训练
   - **图模型**（GCN/GraphConv/MPNN/GIN 任一，用 RDKit 从 SMILES 建图）；
   - **指纹基线**（ECFP4 + 随机森林/逻辑回归）与（可选）RDKit 手工特征。
   在相同划分协议下（论文：HIV/BACE 用 scaffold 划分，其余 random；本包 hiv/bace 请按 scaffold 划分或用官方提供的 ESOL/FreeSolv/Lipophilicity OGB 划分）比较 AUC-ROC（分类）/ RMSE（回归）。
3. **验证论断**：图模型 vs 指纹基线在多数数据集上是否持平或更优？在数据量小/不平衡的数据集（如 ClinTox 正例少、ESOL 仅 1128 条）上优势是否消失或反转？给出对照表并给出四档结论。

- 结论标签：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结）→ 物理位置 `$PAPER_BENCH_DATA_DIR`（来源/许可/逐文件 SHA-256 见 `data/SOURCE.md` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 文件：`hiv.csv`（41,127 分子，SMILES+label）、`bace.csv`（1,513）、`bbbp.csv`（2,039）、`clintox.csv`（1,477）、`esol.csv`（1,128）、`freesolv.csv`（642）、`lipophilicity.csv`（4,200），均为 `SMILES,label` 格式；`ogb_splits_*.json` 为 ESOL/FreeSolv/Lipophilicity 的 OGB 官方 train/valid/test 划分。
- 来源：DeepChem MoleculeNet（原始来源 BACE/BBBP/ClinTox/ESOL/FreeSolv/HIV/Lipophilicity 数据集）；许可：各子数据集来自公开文献，DeepChem 以 MIT 许可发布，本包用于学术评测。
- 规模：全部 ~5MB；训练图模型与指纹基线 CPU 可完成（HIV 41k 分子可用子集，需固定种子）。

## 方向提示（协议建议）

1. **划分**：HIV/BACE 建议按分子 scaffold（Bemis-Murcko）划分训练/验证/测试（如 80/10/10），与论文一致；ESOL/FreeSolv/Lipophilicity 直接用包内 OGB 划分。
2. **图模型**：RDKit 建图（原子特征 + 键特征），GIN/GCN 2-5 层 + 全局池化 + MLP 读出头；训练用 Adam + BCE（分类）/MSE（回归）。若资源受限，HIV 可随机冻结 5,000 训练分子（固定种子）并在报告声明。
3. **指纹基线**：ECFP4（半径 2，2048 位）或 ECFP6；RF 300-500 棵树或逻辑回归；回归用 RF/KRR。
4. **指标**：分类 ROC-AUC（正例率 <2% 时建议同时报 PRC-AUC，论文口径）；回归 RMSE + R²。
5. **对照**：论文 Table 5/6（HIV scaffold：GraphConv 0.763、KernelSVM 0.792、XGBoost 0.756；BACE：Logreg 0.781、KernelSVM 0.862）——这些是论文数值，只能用于对照讨论，禁止抄为实测。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从冻结数据读取并完成训练与评估。
3. **`results/evidence_table.csv`**：至少含列 `dataset,method,split,metric,value`（每数据集 × 每方法 × 每指标一行）。
4. **`results/metrics.json`**：样本统计、各方法各数据集指标、图模型 vs 指纹差值、论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（子集/实现差异 vs 论文、划分差异）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止合成分子或模拟数据。
- 禁止手工抄写论文数字作为「实测结果」；所有指标必须运行代码得到。
- 论文数值只能用于对照讨论。
- 两种方法必须同一划分、同一评估协议。
