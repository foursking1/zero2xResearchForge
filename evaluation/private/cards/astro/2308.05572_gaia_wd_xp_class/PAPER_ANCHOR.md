# PAPER_ANCHOR（私有，仅裁判/编译者可见）— 2308.05572_gaia_wd_xp_class

> 用途：LLM judge 的判分基准。禁止向作答 agent 暴露本文件与 SCORE_RUBRIC.md。
> 所有论文数值均从 arXiv:2308.05572（A&A 682, A5, 2024）正文/表格抽取，禁止臆造。
> 编译器探针数值基于本卡冻结数据（F:\dataset\astro\2308.05572_gaia_wd_xp_class\），仅供判分校准。

## 锚 A1 — 样本规模（口径锚，判 A 维度）

| 项 | 值 |
|---|---|
| 指标名 | GSPC-WD 高置信白矮星候选总数 |
| 论文数值 | **100,886** |
| 出处 | §3.2："We select high-confidence white dwarf candidates with XP spectra by applying a PWD > 0.9 cut and a standard deviation limit of 0.02 on PWD, retaining a total of 100,886 objects."；ReadMe Records=100886 |
| 冻结数据对应 | catalog.dat 解压 100,886 行，GaiaDR3 唯一 100,886（编译器实测） |

## 锚 A2 — 核心结果：high-confidence 逐类计数（核心结果锚，判 A 维度）

| 项 | 值 |
|---|---|
| 指标名 | Table 2 high-confidence white dwarfs per class |
| 论文数值 | **DA 77,330 / DB 5,688 / DC 4,082 / DO 215 / DQ 601 / DZ 1,272（合计 89,188）**；uncertain 11,698 |
| 出处 | §3.2："we obtain 89,188 high-confidence classifications, while 11,698 objects remained with uncertain classifications"；Table 2 |
| 定义口径 | high-confidence = 分类概率 ≥ 0.65（"Objects with probabilities below 0.65 ... labeled as uncertain by adding a colon annotation (e.g., 'DA:')"，§3.2）；阈值 0.65 由 Fig.3 均值 F-score 最大化选定 |
| 冻结数据对应 | SpType 无冒号口径逐类计数 = DA 77,330 / DB 5,688 / DC 4,082 / DO 215 / DQ 601 / DZ 1,272，总数 89,188；带冒号 11,698（编译器实测，**与 Table 2 完全一致**） |
| 容差（判分用） | 满分带：六类全部 ±50、总数 ±10（见 SCORE_RUBRIC A） |

## 锚 A3 — 子论断：DA 主导（可证伪子论断）

| 项 | 值 |
|---|---|
| 指标名 | DA 占比 / high-confidence 占比 |
| 论文数值 | DA 77,330/100,886 = **76.65%**；high-confidence 89,188/100,886 = **88.40%** |
| 出处 | Table 2 + §3.2（"The number of high-confidence classified objects per spectral type is presented in Table 2"） |
| 冻结数据对应 | 与锚 A2 相同口径（编译器实测 76.65% / 88.40%） |

## 锚 A4 — 参数化完整性（次级锚，含版本漂移提示）

| 项 | 值 |
|---|---|
| 指标名 | 拟合未收敛对象数 / 极端热 DA 数 |
| 论文数值 | **1,080** 个对象拟合未收敛；**34** 个 DA Teff > 300,000 K（其中 14 个 MWDD 确认 DAO/热 DA） |
| 出处 | §4.2："The fitting procedure did not converge for 1080 objects"；"We find 34 DA with extremely high temperatures (Teff > 300, 000 K)" |
| 冻结数据对应 | Teff=-999 行数 = **1,396**；DA 且 Teff>300,000 K = **68**（编译器实测）——与论文数值存在发布版本漂移（目录为发布版重跑/筛选结果），裁判重算以冻结数据为准；agent 需如实报告并讨论漂移 |
| 容差（判分用） | 该锚用于 B 抽查重算与 C2 漂移讨论；A 维度不按论文数值卡分 |

## 编译器探针（冻结数据，2026-08-13）

- rows=100,886；unique GaiaDR3=100,886
- SpType 无冒号（high-confidence）：DA 77330 / DB 5688 / DC 4082 / DO 215 / DQ 601 / DZ 1272 → 89,188
- SpType 带冒号（uncertain）：11,698
- argmax(PDA..PDZ)：DA 83,963 / DB 6,395 / DC 7,592 / DO 261 / DQ 824 / DZ 1,851（≠ Table 2，因含 low-confidence 对象）
- max(P)≥0.65 与无冒号不完全等价（目录概率两位小数舍入；冒号判定基于未舍入概率）
- Teff=-999 = 1,396；DA Teff>300,000 K = 68

> 论文内部一致性提示：§3.2 出现 "Feeding the 101,783 objects" 与 100,886 矛盾（笔误），以目录行数 100,886 与 ReadMe 为准。
