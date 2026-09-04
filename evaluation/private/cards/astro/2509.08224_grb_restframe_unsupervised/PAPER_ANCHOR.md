# PAPER_ANCHOR（私有，仅裁判/编译者可见）— 2509.08224_grb_restframe_unsupervised

> 用途：LLM judge 的判分基准。禁止向作答 agent 暴露本文件与 SCORE_RUBRIC.md。
> 所有论文数值均从 arXiv:2509.08224（A&A, 2025）Abstract/§2.2/§3 与 M20 目录 ReadMe 抽取，禁止臆造。
> 编译器探针数值基于本卡冻结数据（F:\dataset\astro\2509.08224_grb_restframe_unsupervised\），仅供判分校准。

## 锚 A1 — 目录规模与 Type 计数（口径锚，判 A 维度）

| 项 | 值 |
|---|---|
| 指标名 | M20 GRB 目录规模与 Type I/II 计数 |
| 论文数值 | 论文 §2.2：M20 共 **314**，剔除 14 个红移不准 → 取 **300**；样本合计 **370**（+70 新 GRB）。M20 ReadMe：**45 type I and 275 type II**（"registered up to 2019, January"） |
| 冻结数据对应 | tablea1.dat **320 行**；Type I（I+I+EE）= **45（14.06%）**、Type II = **275（85.94%）**（编译器实测，与 ReadMe 完全一致） |
| 容差（判分用） | 满分带：总行 320±2；Type I = 45±2；Type II = 275±3 |

## 锚 A2 — 核心结果：GRBs-I 占比与两族中位数（核心结果锚，判 A 维度）

| 项 | 值 |
|---|---|
| 指标名 | GRBs-I 人口占比 / 两族 rest-frame 参数中位数 |
| 论文数值 | **t-SNE 54 GRBs-I（14.59%）**、**UMAP 53（14.32%）**（§3）；中位数 GRBs-I：**T90z 0.31 s、Epz 523.83 keV、Eiso 0.28 ×10⁵¹ erg**；GRBs-II：**13.84 s、407.94 keV、75.19 ×10⁵¹ erg** |
| 冻结数据对应 | M20 Type I 占比 **14.06%**（≈论文 14.3–14.6%）；Type I 中位数 T90z **0.27 s** / Epz 706 keV / Eiso 0.69；Type II 14.50 s / 446 keV / 100.0（编译器实测；T90z 与 Eiso 量级一致，Epz 有 ~30% 差异源于样本与方法差异） |
| 容差（判分用） | 满分带：Type I 占比 ∈ [12%, 17%]；Type I T90z 中位数 ∈ [0.1, 0.6] s；Type II T90z 中位数 ∈ [8, 22] s；Type I Eiso 中位数 ∈ [0.1, 1.5]；Type II Eiso ∈ [50, 150]；agent 对 Epz 差异做归因讨论 |

## 锚 A3 — 子论断：T90 双峰与「仅靠 T90 不可靠」（可证伪子论断）

| 项 | 值 |
|---|---|
| 指标名 | T90,z < 2 s 占比 / Type I 与 Type II 的短暴重叠 |
| 论文数值 | 论文动机：SGRB/LGRB 二分（T90=2 s）被 GRB 200826A（短暴+SN）、060614/211211A/230307A（长暴+KN）打破（§1），故 T90 单独分类不可靠 |
| 冻结数据对应 | T90,z < 2 s = **64/320（20.0%）**；Type I 中 42/45（93.3%）为短暴；Type II 中也有 **22** 个 T90,z<2 s（编译器实测）——短暴不全是 Type I，支持论文动机 |
| 容差（判分用） | 满分带：短暴总数 ∈ [55, 75]；Type I 短暴占比 ∈ [85%, 100%]；Type II 中短暴 ≥10 个；agent 讨论「T90 单独分类不可靠」 |

## 锚 A4 — 特定事件交叉验证（B/C 维度用）

| 项 | 值 |
|---|---|
| 指标名 | 论文点名 GRB 的归属与目录 Type 对照 |
| 论文数值 | GRB 060614 → GRBs-I（合并起源，§3/§4.1）；GRB 980425 / 171205A → GRBs-II（SN 关联，§4.2.2）；GRB 110402A → t-SNE GRBs-I / UMAP GRBs-II（两方法唯一不一致，§3） |
| 冻结数据对应 | GRB 060614A：Type=**I+EE**（与 GRBs-I 一致）；GRB 980425B / 171205A：Type=**II+SNsp**（与 GRBs-II 一致）；GRB 110402A：Type=**I+EE**（T90z=2.8 s、Epz=1924 keV、Eiso=15.2；与「边界案例」一致）（编译器实测） |
| 容差（判分用） | 用于 B 抽查与 C2 讨论；三事件 Type 查询须与上述一致 |

## 编译器探针（冻结数据，2026-08-13）

- rows=320；Type：II 235 / II+SNph 19 / II+SNsp 21 / I 34 / I+EE 11
- Type I=45（14.06%）；Type II=275（85.94%）
- Type I 中位数：T90z 0.27 s / Epz 706 keV / Eiso 0.69（×10⁵¹）；Type II：14.50 s / 446 keV / 100.0
- T90,z<2 s：64（20.0%）；Type I 短暴 42/45（93.3%）；Type II 短暴 22
- 事件：060614A=I+EE；980425B=II+SNsp；171205A=II+SNsp；110402A=I+EE（T90z 2.8 s）
- 论文对照：M20 Type I 占比 14.06% vs 论文 GRBs-I 14.32–14.59%（一致）；Type I T90z 0.27 vs 0.31 s（一致）；Eiso 0.69 vs 0.28（量级一致）；Epz 706 vs 523.83 keV（~35% 差异，归因于 370 样本中 70 个新 GRB 与聚类方法）

> 边界提示：论文的 370 样本、t-SNE/UMAP 嵌入（Table A.2 全表为机器可读，arXiv 仅部分）不在冻结包；agent 若正确说明「嵌入结果不可逐点重算，故验证目录层面的两族人口结构」视为正确做法。GRB 200826A（2020 年事件）在 Table A.1（新 GRB），不在 M20 目录；agent 若查询不到应如实说明。
