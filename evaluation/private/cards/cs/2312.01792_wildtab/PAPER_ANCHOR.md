# PAPER_ANCHOR：论文核心结果锚（私有，禁止外泄到 TASK.md 之外的公开面）

论文：Wild-Tab: A Benchmark For Out-Of-Distribution Generalization In Tabular Regression（arXiv:2312.01792，Sergey Kolesnikov, Tinkoff，2023-12）。以下数值全部摘自论文正文/表格，禁止臆造。

## 锚 A1 — Weather 数据集 ERM 测试 OOD MAE
- 数值：**1.741 ± 0.008**（°C）
- 出处：Table 3（OOD generalization methods performance on Wild-Tab benchmark），Data=Weather、Data split=Test、Objective=Out、方法=ERM；正文 §4.1 Benchmark Results。
- 定义口径：Weather 数据集（Shifts Weather Prediction 规范划分，Test/Out = canonical eval_out）；模型 = MLP 基线（§3.2，dropout + weight decay）；超参 = DomainBed 随机搜索 20 配置 × 3 复制（§3.4）；模型选择 = average-out-domain validation（WILDS 建议，§3.4）；主指标 = MAE（°C，§3.4）。
- 容差（判分用）：相对差 ≤5% 满分档；≤15% 半档；≤30% 低档；>30% 不达标（详见 SCORE_RUBRIC.md）。

## 锚 A2 — Weather 数据集 ERM 测试 ID MAE
- 数值：**1.353 ± 0.024**（°C）
- 出处：Table 2（Generalization gap，Data=Weather，MAE ID 列）与 Table 3（Test/In，ERM 列）；正文 §4.1。
- 定义口径：同上，Test/In = canonical eval_in。
- 容差：相对差 ≤5% 满分档；≤15% 半档；≤30% 低档。

## 锚 A3 — ERM 泛化差距（相对 gap）
- 数值：**28.6%**
- 出处：Table 2 的 Gap (%) 列（Data=Weather）；正文 §4.1 "Benchmarked datasets have a significant generalization gap"。
- 定义口径：gap = (OOD_MAE − ID_MAE) / ID_MAE × 100%，基于 ERM 的 ID/OOD 测试 MAE（1.353 → 1.741）。
- 容差：绝对差 ≤5 个百分点满分档；≤15pp 半档。

## 锚 A4（定性辅助）— 无方法显著优于 ERM
- 数值：Weather Test/Out 各方法 OOD MAE 区间 **1.734–1.77**，ERM = 1.741 处于区间中位
- 出处：Table 3（Test/Out，Weather 列，10 种方法）；正文 §4.1 "When all conditions are equal, no algorithm outperforms ERM by a significant margin"。
- 定义口径：CORAL/DANN/EQRM/ERM/GroupDRO/IB_ERM/IB_IRM/IRM/MMD/VREx 在 Weather eval_out 上的 MAE。
- 用途：辅助判断 agent 结论；若 agent 声称某方法显著优于 ERM，必须给出显著性证据。

## 判分一致性提醒
- 锚 A3 可由 A1/A2 推出（一致性）；判分以 A1/A2 数值为主，A3 用于交叉核对（rubric A 部分一致性系数 ×0.9）。
- 锚数值的 ± 为论文 3 次复制的标准差；冻结子集评估的抽样噪声已并入 rubric 容差设计。