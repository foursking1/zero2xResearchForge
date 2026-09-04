# PAPER_ANCHOR：论文核心结果锚（私有，禁止外泄到 TASK.md 之外的公开面）

论文：Rabbani, Medri & Samad, Attention versus Contrastive Learning of Tabular Data — A Data-centric Benchmarking（arXiv:2401.04266，2024）。以下数值摘自论文 Table 2/4/5/6 与 §5，禁止臆造。

## 锚 A1 — 难度划分定义与论文自身数值
- 定义（Table 2 表注）："A dataset is hard if gradient boosting classifier outperforms logistic regression by 4% or more, otherwise, it is easy."
- 论文自身 Table 6（LR/GBT 列）下 GBT−LR 差距：
  - Hard 组：4538: +21.2、40975: +6.0、40701: +8.8、1497: +29.7、1464: +5.7、23: **+3.5（例外）**、1475: +13.8、1067: +7.0、40982: +10.0、1068: +8.3、1050: +5.7、1049: **+3.8（例外）**、1487: +4.5、1485: +19.9 → **12/14 满足 ≥4pp**
  - Easy 组：469: −0.5、11: −1.6、50: +0.3、37: +0.6、1480: +1.1、46: +0.8、31: +0.9、54: −4.8、40994: +1.5、1494: +1.2、1063: +1.1、1510: −2.0、458: −1.7、4134: +2.4 → **14/14 <4pp**
- 含义：即使论文自己的数值也不能 100% 复现标签（Cmc/Pc4 为边界），判分按方向一致 + 容差（见 SCORE_RUBRIC A1）。

## 锚 A2 — Table 6 代表性数值（LR / GBT / DNN 列；F1）
- 4538 Gesture：LR 0.447 / GBT 0.659 / DNN 0.631（SAINT 0.716 最佳）
- 1067 Kc1：LR 0.761 / GBT 0.831 / DNN 0.836
- 1485 Madelon（高维 500 特征）：LR 0.612 / GBT 0.811 / DNN 0.567（对比学习 CutMix 0.812 最佳、RFC 0.607）
- 4134 Bioresponse（1776 特征）：LR 0.767 / GBT 0.791 / DNN 0.765
- 注意：论文 F1 与 sklearn **weighted-F1** 更接近（如 Kc1 GBT 0.831 ≈ weighted 口径）；任务要求 solver 报 macro-F1 并允许 ±5pp 差异。

## 锚 A3 — 平均秩（Table 4/5/6）
- Table 6（28 数据集总平均秩）：SAINT **3.58**（最佳）、DNN-AE 5.43、NPT 5.43、CutMix 6.75、RFC 6.96、GBT 7.07、LR **10.46**（最差）
- Table 4（14 hard 平均秩）：SAINT **1.69**（最佳）、NPT 3.75（attention/contrastive 中次佳）、GBT 5.79
- Table 5（14 easy 平均秩）：SAINT 5.46（最佳）、Pass 5.93、DNN-AE 4.64（easy 上深度/传统混合领先）、TabNet 11.92（最差）
- §5.2：attention-only 方法在 12/14 hard 数据集上取得最佳 F1，其中 NPT 在 7 个数据集领先；easy 上 attention-only 排名靠后（TabNet 9th / FTT 8th / NPT 4th，九方法内）。

## 锚 A4 — 方向性结论（§5.1/§5.3）
- "no best learning method exists for all tabular data sets"（摘要）。
- 对比学习方法中 CutMix（6.75）/ RFC（6.96）优于 Noise（8.89）/ Sample（7.11）；Pass（7.11）与 Sample 持平（§5.1）。
- GBT 在低 F-S ratio（tall 数据）上表现最好，在高 F-S ratio 上排名下滑（Table 7，§5.3）。
- 用途：辅助判断 agent 结论方向；若 agent 声称「MLP 全面优于 GBT on hard」或「GBT 全面优于 LR on easy」，需与上述锚核对。

## 判分一致性提醒
- 判分以 A1（难度划分方向一致率）与 A2（代表性 F1 数值、±5pp 容差）为主，A3 平均秩用于交叉核对 agent 报告（SAINT 3.58 最优、LR 10.46 最差必须自洽）。
- 任务协议与论文差异（30 次划分 vs ≥5 次；macro vs weighted；sklearn 实现）已在 rubric 带宽中考虑。
