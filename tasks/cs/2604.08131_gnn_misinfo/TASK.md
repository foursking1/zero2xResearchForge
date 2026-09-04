# 科研任务：谣言/虚假信息检测中 GNN vs 传统基线（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id: `2604.08131_gnn_misinfo`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Graph Neural Networks for Misinformation Detection: Performance–Efficiency Trade-offs（arXiv:2604.08131，ICCS 2026）
- 领域：CS / 图神经网络 / 虚假信息检测

## 问题（可证伪）

在论文使用的真实谣言检测数据集 WELFake（平衡中英文混合语料，72K 条）上，验证论文的核心结论之一：

**GNN 显著优于强非线性传统基线 claim**：在相同 TF-IDF 特征与相同数据划分下，经典图神经网络 GraphSAGE 的 F1 显著高于多层感知机（MLP）。论文报告（Table 2/3）：WELFake 上 GraphSAGE F1 = **91.9 ± 0.2%**，MLP F1 = **66.8 ± 29.1%**，差距约 25 个百分点。

可证伪表述：基于冻结数据，(a) "GraphSAGE 测试 F1 落在 91.9% 附近（±5pp 内）" 是否成立；(b) "GraphSAGE 相对 MLP 的优势 ≥15pp" 是否成立；(c) "优势方向为 GNN 优于 MLP（而非相反）" 是否成立。

## 方向提示（非方法步骤）

- 指标：F1（%），越高越好（论文主指标，§3.5 Evaluation Metrics / §4.1）。
- 划分：论文统一管线为分层抽样 80% train / 10% val / 10% test（§3.2 Data Preprocessing），复现仓库用 `train_test_split(test_size=0.1, random_state=42, stratify=label)` 再对剩余做 `test_size=0.2222`；先用 10% test 分离，再切 val。只用 train 训练，val 做早停/选模，test 只评估一次。
- 特征：TF-IDF（max 5,000 特征），全词表拟合仅限 train 语料（§3.2）。
- 图构建（GNN 用）：k-NN 相似图（`torch_geometric.nn.knn_graph`，K=5 或 K=2），节点特征 = TF-IDF 向量（§3.4）。
- 模型：GraphSAGE 对比 MLP（2 隐层 256/128，ReLU，早停，最多 200 迭代，§3.3）。MLP 可用 sklearn `MLPClassifier`；GraphSAGE 可用 PyG `SAGEConv`。
- 防泄漏：任何归一化/统计量只能由 train 拟合；test 不得参与调参、早停或特征选择；k-NN 图只能基于 train（或 train+val 的已训练表示），不得把 test 节点特征用于建图信息外泄。

## 数据说明

- 数据包：`$PAPER_BENCH_DATA_DIR/data/welfake/WELFake_Dataset.csv`（WELFake 官方 Zenodo 发布，245MB，72,134 行；含 39 行 `text` 为空的记录，复现管线先 `dropna(subset=['text'])` 得 72,095 条可用样本）。
- schema：`Unnamed: 0`（原索引）、`title`（标题）、`text`（正文）、`label`（1 = 假新闻 fake，0 = 真实新闻 real）。
- 来源：Zenodo record 4561253（https://zenodo.org/records/4561253 ，WELFake dataset for fake news detection in text data），CC BY 4.0。
- checksum（sha256）：`WELFake_Dataset.csv` = `665331424230FC452E9482C3547A6A199A2C29745ADE8D236950D1D105223773`（245,086,152 字节）。
- 逐文件 SHA-256 登记：`$PAPER_BENCH_DATA_ROOT/checksums.sha256`。

## 输出要求（提交物）

1. **结论**：对上述三个 claim 分别给出 `supported / partially_supported / contradicted / inconclusive`，并说明数据支持的强度。
2. **证据表**：`results/evidence_table.csv`（或等价表格），至少含列：`model`（graphsage / mlp）、`split`（test）、`n`、`f1`、`precision`、`recall`；另报告 `f1_gap_pp`（GraphSAGE − MLP）。
3. **代码**：完整可复现的训练/评估脚本（含固定随机种子），从冻结 CSV 读取数据。
4. **报告**：`report.md`：方法（预处理、TF-IDF、图构建、模型与超参）、防泄漏说明、局限性（WELFake 子集=全量、3 种子平均 vs 单次运行差异）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成/模拟数据替代。
- test 集只用于最终评估；禁止用于训练、验证、早停、调参或特征选择。
- TF-IDF 词表与图结构只能由 train 拟合/构建；禁止使用全量统计（数据泄漏）。
- 报告中必须说明与论文全量实验（3 次种子平均、500 轮训练等）的差异。
