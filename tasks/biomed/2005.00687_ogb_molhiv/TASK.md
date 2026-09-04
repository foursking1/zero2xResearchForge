# 科研任务：OGB「ogbg-molhiv 图神经网络分子性质预测基准」关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2005.00687_ogb_molhiv`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Hu et al., "Open Graph Benchmark: Datasets for Machine Learning on Graphs", NeurIPS 2020（arXiv:2005.00687）
- 领域：biomed / 图机器学习 / 分子性质预测（HIV 抑制活性）

## 问题（可证伪）

OGB 论文对 ogbg-molhiv（来自 MoleculeNet 的 HIV 分子活性数据，41,127 个分子图，scaffold 划分 80/10/10，ROC-AUC 评估）报告了基准：**图神经网络（GIN/GCN）显著优于 MLP 等非图基线，且加入虚拟节点/额外特征能进一步提升**（Table 15：MLP 未列但 GCN 74.18±1.22、GIN 75.20±1.30、GIN+virtual node 77.07±1.49，均远高于随机 50）。scaffold 划分（按分子骨架）比随机划分更难，是评估分布外泛化的关键。

请基于冻结数据回答：

1. **数据与基准**：解析冻结的 ogbg-molhiv 数据（train/valid/test jsonl，41,127 个分子图：原子特征、键特征、二部图邻接、标签；划分已在文件层面固定）。说明图统计（节点/边数分布、正例率）。
2. **模型对比**：实现并训练
   - **图神经网络**（GCN 或 GIN，2-5 层 + 平均池化 + MLP 读出头，按论文做法可加虚拟节点）；
   - **非图基线**（MLP：仅用原子特征平均池化 + MLP；或分子指纹 + 逻辑回归/RF）。
   在官方 train/valid/test 划分上训练，报告 test ROC-AUC。
3. **验证论断**：GNN 的 test ROC-AUC 是否显著高于非图基线？是否落在论文报告区间（GIN 75.2±1.3、GCN 74.2±1.2）附近？加虚拟节点是否提升？给出对照表与四档结论。

- 结论标签：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结）→ 物理位置 `$PAPER_BENCH_DATA_DIR`（来源/许可/逐文件 SHA-256 见 `data/SOURCE.md` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 文件：`train.jsonl`（32,901 图）、`valid.jsonl`（4,113 图）、`test.jsonl`（4,113 图）。每行一个 JSON：`num_nodes`、`node_feat`（9 维原子特征）、`edge_index`、`edge_attr`（3 维键特征）、`y`（0/1 标签）。
- 来源：OGB 官方（图数据由 RDKit 从 MoleculeNet HIV 预处理）；许可：OGB 数据集许可（MIT；原始 HIV 数据来自 MoleculeNet）。
- 规模：~71MB；GNN 训练需 GPU（可选 10,000 图子集，固定种子并声明）。

## 方向提示（协议建议）

1. **读取**：可直接 `pip install ogb` 用 `PyG` 的 `OGBG-MOLHIV`（但注意本卡要求用**冻结文件**——写解析器读 jsonl 转 PyG/自建图对象，禁止从 ogb 在线下载重新拉数据）。
2. **模型**：GIN（可参考 OGB 官方示例）或 GCN；5 层、hidden 256-300、dropout 0-0.5、平均池化；训练 30-100 epoch，early stopping 按 valid AUC。
3. **虚拟节点**：在图中加一个连接到所有节点的虚拟节点（加分项，对照有无）。
4. **非图基线**：原子特征（或 ECFP）平均 + MLP/RF/逻辑回归。
5. **对照**：论文 Table 15（GCN 74.18±1.22、GIN 75.20±1.30、GIN+virtual 77.07±1.49）——只能对照讨论，禁止抄为实测。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从冻结 jsonl 读取并完成训练与评估。
3. **`results/evidence_table.csv`**：至少含列 `model,virtual_node,test_roc_auc,valid_roc_auc`（每模型一行）。
4. **`results/metrics.json`**：图统计、各模型 AUC、vs 论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（子集/实现差异 vs 论文、scaffold 划分）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止从 OGB 在线重新下载数据或使用其他版本。
- 禁止合成分子或模拟数据。
- 禁止手工抄写论文数字作为「实测结果」。
- 划分固定（文件层面已分好）；测试集禁止参与训练/调参。
