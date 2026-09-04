# PAPER_ANCHOR（私有）：2410.06922 系外行星质量估计

来源：arXiv:2410.06922（Lalande, Tasker, Doya 2024, AJ, "Estimating Exoplanet Mass Using Machine Learning on Incomplete Datasets"）。全部数值摘自论文 §4 与 Fig 3/7/11、Table 1（论文全文：candidate-papers/astro/2410.06922.pdf）。

## 锚 A1 — 完整属性数据集（六属性，凌星测试 150 颗）各算法误差（核心结果）

| 项 | 值 |
|---|---|
| 指标名 | ϵ = RMS(ln(m_obs/m_imp))，150 颗测试行星，隐藏质量按凌星观测插补 |
| 论文数值 | mBM(TLG2020)=0.980；kNN-Imputer=0.876；MissForest=0.885；GAIN=1.253；MICE=0.968；kNN×KDE=0.886 |
| 出处 | §4.1.1 + Fig 3 图注（"four out of the five new imputation techniques surpass the original result"；"best results ... error of around ϵ = 0.88 that corresponds to a factor of 2.4"） |
| 定义口径 | 完整属性子集 = 550 颗行星六属性齐全（TLG2020 数据集）；150 颗测试；ϵ 为 150 颗行星的平均（RMS） |
| 容差 | 判分以**排名模式**为主：kNN×KDE/MissForest/kNN-Imputer 为最优组（ϵ≈0.85–0.95）、MICE 次之（≈0.95–1.0）、GAIN 最差（>1.2）；4/5 新算法 ≤ mBM |

## 锚 A2 — 全档案（六属性，不完备）各算法误差（核心结果）

| 项 | 值 |
|---|---|
| 指标名 | ϵ：1,426 颗有质量观测的行星（全档案）；同 150 测试子集 |
| 论文数值 | kNN×KDE=1.510（150 子集 0.846）；kNN-Imputer=1.628（1.258）；MissForest=1.701（0.835）；GAIN=2.552（1.942）；MICE=1.728（0.918）；PS-CP(Chen&Kipping)=2.566（3.094） |
| 出处 | §4.2.1 + Fig 7 图注（"The algorithm with the lowest overall error is the kNN×KDE, with the GAIN once again performing most poorly"） |
| 容差 | 判分以**排名模式**为主：kNN×KDE 最低、GAIN 最差；全档案对 150 子集的改善方向（kNN×KDE/MissForest/MICE 改善，kNN-Imputer/GAIN 变差） |

## 锚 A3 — 扩展八属性的小幅提升（第三发现）

| 项 | 值 |
|---|---|
| 指标名 | kNN×KDE 全档案 ϵ（六属性 vs 八属性：+恒星金属丰度、轨道离心率） |
| 论文数值 | 六属性 ϵ=1.510（150 子集 0.846）→ 八属性 ϵ=1.502（150 子集 0.840），"small overall improvement when adding additional information" |
| 出处 | §4.3.1 + Fig 11 图注 |
| 容差 | 方向性：ϵ(8属性) ≤ ϵ(6属性)（或相当，差异 <0.05 内视为持平） |

## 锚 A4 — GAIN 一贯最差 + kNN×KDE 概率分布价值（第三发现）

| 项 | 值 |
|---|---|
| 指标名 | 算法排名稳健性；kNN×KDE 分布形状（单峰=高置信，双峰/宽=低置信） |
| 论文数值 | "The GAIN algorithm consistently gave the worst"（§5 摘要性结论）；kNN×KDE 返回概率分布（§4.1.2/4.2.2，HAT-P-57b 窄单峰 vs Kepler-9c/Kepler-30c 双峰） |
| 出处 | 摘要 + §5 + Fig 4/8 |

## 辅助事实（数据定义，供判分与复现参考）

- 数据：NASA Exoplanet Archive 默认数据集（PSCompPars）；论文快照 2023-02-02（5,251 颗）；本包冻结 2026-08-13 快照（6,336 颗），质量缺失率 61.7% vs 论文 72.8%。
- 8 属性缺失率（论文 Table 1）：半径 30.4%、质量 72.8%、周期 3.7%、离心率 70.1%、平衡温度 13.5%、恒星质量 0.5%、金属丰度 10.1%、行星数 0.0%。
- 训练/测试协议：完整子集 550 颗（400 训练 + 150 测试）；全档案用逐行星隐藏（每颗有质量观测的行星逐一隐藏插补，1,426 颗）；RV 测试 1,081 颗（kNN×KDE 卷积最小质量）。
- 许可：NASA Exoplanet Archive 公开；论文代码 GitHub `DeltaFloflo/exoplanet_imputation`（开源）。