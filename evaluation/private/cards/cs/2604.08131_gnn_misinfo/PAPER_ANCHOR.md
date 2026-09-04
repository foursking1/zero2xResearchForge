# PAPER_ANCHOR：论文核心结果锚（私有，禁止外泄到 TASK.md 之外的公开面）

论文：Graph Neural Networks for Misinformation Detection: Performance–Efficiency Trade-offs（arXiv:2604.08131，S. Kuntur, M. Krzywda 等，ICCS 2026）。以下数值全部摘自论文正文/表格，禁止臆造。

## 锚 A1 — WELFake 上 GraphSAGE 测试 F1
- 数值：**91.9 ± 0.2%**
- 出处：Table 2（Performance comparison across datasets，WELFake 行 GraphSAGE 列 F1）与 Table 3（Best-performing classic GNN per dataset，WELFake 行）；正文 §4.1。
- 定义口径：WELFake 数据集（Zenodo 4561253 原始 CSV，dropna(text) 后 72,095 条）；统一管线分层 80/10/10（seed 42）；TF-IDF max 5,000 特征；k-NN 图 K=5（§3.4）；预训练 5 epochs + 主训练 ≤500 epochs、Adam lr=0.001、early stopping patience=10；结果 = 3 个随机种子平均（§3.4）。
- 容差（判分用）：相对差 ≤5% 满分档；≤10% 半档；≤20% 低档（详见 SCORE_RUBRIC.md）。

## 锚 A2 — WELFake 上 MLP 测试 F1
- 数值：**66.8 ± 29.1%**
- 出处：Table 2（WELFake 行 MLP 列 F1）；正文 §4.1。
- 定义口径：同一特征/划分；MLP = 2 隐层 256/128、ReLU、early stopping、max 200 迭代（§3.3）；3 种子平均。
- 注意：该基线标准差极大（29.1），因部分种子训练不稳定；判分带宽按绝对差设计（见 rubric）。
- 容差（判分用）：绝对差 ≤8pp 满分档；≤15pp 半档；≤25pp 低档。

## 锚 A3（方向性/幅度）— GNN 相对 MLP 的 F1 优势
- 数值：WELFake 上 GraphSAGE − MLP = **+25.1pp**（91.9 − 66.8）
- 出处：由 Table 2 两行推出；正文 §4.1 "compared to MLPs ... classic GNNs improve F1 scores by approximately 12 to 30 percentage points"。
- 定义口径：同数据集同划分下两模型测试 F1 之差。
- 用途：方向性校验（若报告 GraphSAGE ≤ MLP，claim 不成立）；幅度作为辅助判分。

## 锚 A4（定性辅助）— 低资源鲁棒性
- 数值：WELFake F1@10%=87.5、F1@20%=89.9、F1@30%=91.9、Drop=4.8%（Table 4）
- 出处：Table 4（Effect of training data size），正文 §4.3 "F1 drop between 30% and 10% training data remains below 7 percentage points for all datasets"。
- 用途：辅助判断 agent 结论；不作主判分锚。

## 判分一致性提醒
- 锚 A3 可由 A1/A2 推出（一致性）；判分以 A1/A2 数值为主，A3 用于方向性与幅度校验（rubric 方向性校验）。
- 锚数值的 ± 为论文 3 次运行的标准差；单次运行复现存在训练噪声，带宽设计已考虑（GraphSAGE 窄带、MLP 宽带）。
