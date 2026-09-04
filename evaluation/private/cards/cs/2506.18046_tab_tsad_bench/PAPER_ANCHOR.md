# PAPER_ANCHOR（私有，仅裁判/编译者可见）：2506.18046_tab_tsad_bench

> 用途：LLM judge 判分基准。本卡为 L2（RCBench 端到端科研再发现，目标论文隐藏——TASK.md 不给论文标题/编号；锚值仅见本文件）。数值从 arXiv:2506.18046v1（PVLDB 2025, "TAB: Unified Benchmarking of Time Series Anomaly Detection Methods"）§5.1.2/§5.1.3、Table 7 抽出（已用 PyMuPDF 从 PDF 原文核对），禁止臆造。

## 目标论文与协议

- Qiu et al. (2025), "TAB: Unified Benchmarking of Time Series Anomaly Detection Methods"（arXiv:2506.18046，PVLDB）。
- 协议（§5.1.2）：划分优先用原始自带划分；无则 train+val=50%、test=50%、val=train+val 末 20%；放弃 drop-last 与 point adjustment；阈值网格 {0.1,0.5,1,2,3,5,10,15,20,25}（百分比）逐方法取最佳；统一超参与 ADAM/L2 训练。
- 后处理（§5.1.3）：比较窗口重叠与非重叠两种后处理；"in most cases, the two post-processing methods do not affect the performance of the method, but there are still a small number of cases where the performance of the method is affected"；TAB 最终统一采用 **non-overlapping**（部分传统方法无法用重叠窗口）。
- 数据（§4.1）：29 个多变量数据集 + 1,635 条单变量序列；本卡冻结 **Table 7 的 6 个多变量数据集**（CalIt2 / Daphnet / MSL / PSM / SKAB / SMAP）。

## 锚 A1 — Table 7：6 多变量数据集的 6 方法 × 2 后处理数值（§5.1.3 Table 7，判 A2 排名/数值）

方法缩写：ATrans=Anomaly Transformer，DC=DCdetector，DLin=DLinear，NLin=NLinear，Patch=PatchTST，TsNet=TimesNet。

| 数据集 | 后处理 | ATrans | DC | DLin | NLin | Patch | TsNet |
|---|---|---|---|---|---|---|---|
| CalIt2 | Overlap | 0.483 | 0.499 | 0.761 | 0.694 | 0.791 | 0.798 |
| CalIt2 | Non-overlap | 0.491 | 0.527 | 0.752 | 0.695 | 0.808 | 0.771 |
| Daphnet | Overlap | 0.469 | 0.486 | 0.727 | 0.715 | 0.739 | 0.773 |
| Daphnet | Non-overlap | 0.489 | 0.501 | 0.728 | 0.715 | 0.741 | 0.754 |
| MSL | Overlap | 0.494 | 0.502 | 0.626 | 0.594 | 0.637 | 0.615 |
| MSL | Non-overlap | 0.508 | 0.504 | 0.624 | 0.592 | 0.637 | 0.613 |
| PSM | Overlap | 0.496 | 0.499 | 0.581 | 0.586 | 0.578 | 0.589 |
| PSM | Non-overlap | 0.498 | 0.499 | 0.580 | 0.585 | 0.586 | 0.592 |
| SKAB | Overlap | 0.495 | 0.532 | 0.563 | 0.558 | 0.555 | 0.592 |
| SKAB | Non-overlap | 0.513 | 0.522 | 0.593 | 0.583 | 0.597 | 0.620 |
| SMAP | Overlap | 0.504 | 0.499 | 0.398 | 0.434 | 0.449 | 0.455 |
| SMAP | Non-overlap | 0.504 | 0.516 | 0.397 | 0.434 | 0.448 | 0.453 |

- 表注："Bold represents the best result (AUC-ROC)"。判分口径：agent 若实现了与上表方法同族的方法（Transformer 关联重建 / 对比双注意力 / 线性单层 / patch 化 Transformer / 多周期 CNN），对照相应数值；实现族外方法则对照模式。

## 锚 A2 — 数据集依赖的排名模式（判 Q1 方向）

- SMAP：Transformer/注意力类（ATrans 0.504、DC 0.516）显著优于线性类（DLin 0.397、NLin 0.434）；差距 ~0.08-0.12。
- CalIt2：Patch/TsNet/DLin 最优（0.75-0.81），ATrans/DC 最差（0.48-0.53）——与 SMAP 相反（线性 DLin 在 CalIt2 上很好）。
- Daphnet/MSL/PSM/SKAB：方法间差距较小（约 0.02-0.15），DLin 在 MSL/PSM/SKAB 上中等偏上。
- 结论模式：**深度/Transformer 方法并非在所有数据集上一致占优；排名数据集依赖强**。

## 锚 A3 — 后处理影响模式（判 Q2 方向）

- 大多数（数据集 × 方法）上 |Δ(overlap−non-overlap)| ≤ 0.03（表内最大 |Δ| = 0.030，CalIt2 DC 0.499→0.527 与 SKAB TsNet 0.592→0.620 = 0.028）；
- 少数单元格差异 > 0.01（如 MSL ATrans 0.494→0.508、Daphnet ATrans 0.469→0.489、CalIt2 DC、CalIt2 Patch 0.791→0.808、SKAB 多数）；
- 两种后处理下**排名基本稳定**（大多数数据集 Top 方法不变）。
- 论文据此统一采用 non-overlapping。

## 锚 A4 — 评测设置口径（判 A1 数据/协议正确性）

- 阈值网格：[0.1, 0.5, 1, 2, 3, 5, 10, 15, 20, 25]（百分比），逐方法取最优（§5.1.2）。
- 划分：优先原始自带划分；无则 train+val=50% / test=50%、val=train+val 末 20%。
- 放弃 drop-last 与 point adjustment；统一窗口滚动（非重叠）。
- 冻结数据应含与上述一致的 train/val/test 与 label。

## 辅助数据事实（裁判 B 维度抽查基准；从冻结数据直接核验）

| 字段 | 冻结参考值 | 备注 |
|---|---|---|
| 数据集数量 | 6（CalIt2/Daphnet/MSL/PSM/SKAB/SMAP） | 冻结目录 |
| SMAP 通道数/行数 | 25 通道；train≈108,146 / test≈427,617 行（长表） | 以冻结文件为准 |
| MSL 通道数/行数 | 55 通道；train≈58,317 / test≈73,729 行 | 以冻结文件为准 |
| label 列 | 逐点 0/1，异常率低（如 SMAP ~13%） | 冻结文件直接核验 |
| 长表结构 | 每文件列：{date?, value, cols, label?}；`cols` 含通道名 | utils.py read_data 兼容 |

## 判分对照速查（judge 用）

- A1（数据/协议）满分：6 数据集正确解析、划分与 label 使用正确、阈值网格与两种后处理均实现。
- A2（排名模式）满分：agent 复现 ≥2/3 关键模式——(i) SMAP 上注意力/Transformer 类 > 线性类；(ii) CalIt2 上线性/Patch 类 > 注意力类（排名反转）；(iii) 其余数据集差距较小。
- A3（后处理）满分：复现「多数 |Δ|≤0.03、少数 >0.01、排名基本稳定」模式；若 agent 得到差异普遍巨大（|Δ|>0.1）需解释。
- A4（设置敏感性）：若 agent 做了固定阈值 vs 最优阈值的对比并报告排名变化 → 加分/满分参考。
- B 抽查两数：(1) 冻结数据事实（6 数据集、长表结构、SMAP 通道/行数、label 异常率）；(2) 重跑 agent 代码核对某（数据集×方法×后处理）的 AUC-ROC 与 evidence_table 一致。
- 容差说明：方法实现由 agent 自选（族内方法可简化），绝对数值不强求逐值复现；同族方法对照时数值带 ±0.05，跨族对照以**排序方向**为准。