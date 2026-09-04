# PAPER_ANCHOR（私有，仅裁判/编译者可见）：2505.03385 — Solar Flare Forecast: A Comparative Analysis of ML Algorithms

> 用途：LLM judge 判分基准。目标论文隐藏（TASK.md 不给标题/编号）。所有数值从 arXiv:2505.03385v1（Bringewald, 2025, arXiv:2505.03385）正文/Table 4 抽出；代码仓库 `github.com/juliabringewald/Solar-Flare-Forecast`（仅有 notebook，无数据文件）。
> 论文核心协议：13 个 SHARP 参数 → 标准化 → 交互特征 → PCA（8 PC / 100 PC）→ 平衡采样（多分类 128/142/142/23、二分类 165/165，100 次重复）→ 10 折分层 CV + GridSearch。**本卡协议（TASK.md）按此构造，但允许 R≥10 次重复（论文用 100），PCA 特征由本数据重建。**

## 锚 A1 — 数据事实（判 A1 数据/协议正确性）

| 项 | 论文值 | 冻结数据实测 |
|---|---|---|
| 总样本 | 845（§3.3："552 C-class, 23 X-class, 142 M-class, 128 B-class"） | 845（B=128, C=552, M=142, X=23）✓ |
| 平衡集多分类 | 128 B + 142 C + 142 M + 23 X = 435 | 协议一致 |
| 平衡集二分类 | 165 B/C + 165 M/X = 330 | 协议一致 |
| 交互特征 | 论文未给维度；官方 notebook 用 `PolynomialFeatures(interaction_only=True)`（91 维） | 本卡用 degree=2 → 104 维（支持 100 PC 设置） |

## 锚 A2 — PCA 方差声称（判 Q0 / A2；**论文声称不可复现**）

| 声称 | 论文表述 | 出处 | 冻结数据实测（本卡协议：StandardScaler → degree=2 → PCA 全量 845） |
|---|---|---|---|
| 95% 方差所需 PC | "a threshold of 95% was used, resulting in a total number of n=8 components" | §3.1.1 / Fig 2 | **6 个**（cum=0.9501）→ 声称不符 |
| 97.5% 方差所需 PC | "the use of 100 components was analyzed, capturing 97.5% of the variance" | §3.1.1 / Fig 3 | **10 个**（cum=0.9755）→ 声称不符 |
| 8 PC 捕获方差 | 隐含 95% | — | ≈0.964 |
| 100 PC 捕获方差 | 97.5% | — | 1.000（104 维全空间） |

> 注意：官方 notebook 的 interaction_only 变体（91 维）同样给 6（95%）/ 10（97.5%）、8 PC ≈ 0.967；「100 PC」在任何 ≤100 维空间下都只能取 min(100, dim)。论文的 8/100 与 95%/97.5% 对应关系在真实数据上不成立——这是本卡 Q0 的核心发现，judge 依据 agent 如实报告与否打分（见 rubric A2）。

## 锚 A3 — Table 4 性能表（判 Q1/Q2 方向一致性；列顺序 = RF-8PC, RF-100PC, KNN-8PC, KNN-100PC, XGB-8PC, XGB-100PC）

**Multiclass**（出处：Table 4 "Multiclass Classification"）：

| 指标 | RF 8/100 | KNN 8/100 | XGB 8/100 |
|---|---|---|---|
| Accuracy | 0.541 / 0.623 | 0.561 / 0.638 | 0.570 / 0.624 |
| ROC AUC | 0.855 / 0.839 | 0.754 / 0.817 | 0.770 / 0.846 |
| PR AUC | 0.557 / 0.668 | 0.567 / 0.647 | 0.562 / 0.673 |
| F1 | 0.530 / 0.610 | 0.538 / 0.603 | 0.554 / 0.606 |

**Binary**（出处：Table 4 "Binary Classification"）：

| 指标 | RF 8/100 | KNN 8/100 | XGB 8/100 |
|---|---|---|---|
| Accuracy | 0.679 / 0.738 | 0.680 / 0.594 | 0.690 / 0.733 |
| ROC AUC | 0.743 / 0.804 | 0.735 / 0.625 | 0.758 / 0.811 |
| PR AUC | 0.790 / 0.790 | 0.758 / 0.636 | 0.787 / 0.834 |
| F1 | 0.671 / 0.735 | 0.640 / 0.373 | 0.680 / 0.723 |

## 锚 A4 — 论文发现（判方向一致性的模式定义）

| 发现 | 论文表述 | 出处 |
|---|---|---|
| F1 RF/XGB 随维度提升 | "Random Forest and XGBoost consistently demonstrate strong performance across all metrics, benefiting significantly from increased dimensionality" | 摘要 / §4 |
| F2 KNN 二分类 100PC 退化 | KNN binary 100PC 全指标下滑（acc 0.680→0.594、F1 0.640→0.373） | Table 4 |
| F3 KNN 多分类随维度提升 | KNN multiclass 8PC→100PC 上升（acc 0.561→0.638、F1 0.538→0.603） | Table 4 |
| F4 排名 | 多分类 XGB 8PC acc 最高 0.570；100PC KNN acc 最高 0.638；二分类整体 RF/XGB 优于 KNN | Table 4 |

## 判分对照速查（judge 用）

- A1（15）：数据事实正确（845、128/552/142/23、无缺失、104 维交互特征）+ 协议无泄漏。
- A2（10）：agent 报告 n95∈[5,7] 与 n97.5∈[9,11]、8 PC 方差 ∈[0.95,0.98]、100 PC 方差 ≥0.995，并指出「论文 8PC≈95% / 100PC≈97.5% 声称与实测不符」→ 满分；只抄论文数字（8/100、95%/97.5%）→ 0–3。
- A3（35）：方向一致性（F1–F4），详见 SCORE_RUBRIC A3 分段。
- B 抽查：数据事实（845/类分布）与任一算法-任务-降维档指标（运行 agent 代码 + 其声明的种子从冻结数据重算，与 evidence_table 一致）。
- 容差：agent 数值与 Table 4 不必一致（重复次数、PCA 重建、库版本不同）；判分以**方向 + 相对排序**为主。
