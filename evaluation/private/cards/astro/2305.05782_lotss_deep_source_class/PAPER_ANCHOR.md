# PAPER_ANCHOR（私有，仅裁判/编译者可见）— 2305.05782_lotss_deep_source_class

> 用途：LLM judge 的判分基准。禁止向作答 agent 暴露本文件与 SCORE_RUBRIC.md。
> 所有论文数值均从 arXiv:2305.05782（MNRAS, 2021/2023）Abstract/§7/Table 2 抽取，禁止臆造。
> 编译器探针数值基于本卡冻结数据（F:\dataset\astro\2305.05782_lotss_deep_source_class\），仅供判分校准。

## 锚 A1 — 目录规模（口径锚，判 A 维度）

| 项 | 值 |
|---|---|
| 指标名 | LoTSS-Deep DR1 分类源总数（逐场） |
| 论文数值 | Table 2：ELAIS-N1 31,610 / Lockman 31,162 / Boötes 19,179 / **合计 81,951**（Abstract "~80,000 radio sources"） |
| 冻结数据对应 | 三场 FITS 行数 31,610 / 31,162 / 19,179 = **81,951**（编译器实测，与 Table 2 完全一致） |
| 容差（判分用） | 满分带：三场行数与总计精确一致（±3） |

## 锚 A2 — 核心结果：Table 2 逐类计数（核心结果锚，判 A 维度）

| 项 | 值 |
|---|---|
| 指标名 | 每场五类源计数（Overall_class） |
| 论文数值 | Table 2：ELAIS-N1 SFG 22,720 / RQAGN 2,779 / LERG 4,287 / HERG 510 / Unc 1,314；Lockman 21,044 / 2,633 / 5,304 / 710 / 1,471；Boötes 11,916 / 2,030 / 3,158 / 524 / 1,551；总计 55,680 / 7,442 / 12,749 / 1,744 / 4,336 |
| 冻结数据对应 | 三场 `Overall_class` 计数与 Table 2 **逐类完全一致**（编译器实测）；百分比 SFG 67.9% / RQAGN 9.1% / LERG 15.6% / HERG 2.1% / Unc 5.3% |
| 容差（判分用） | 满分带：五类 × 三场全部精确一致（±5）；百分比 ±0.5pt |

## 锚 A3 — 子论断：可靠分类率与 SFG 主导（可证伪子论断）

| 项 | 值 |
|---|---|
| 指标名 | 可靠分类率 / SFG 占比 / RQAGN 占比 |
| 论文数值 | "Ninety-five per cent of the sources can be reliably classified, of which more than two-thirds are star-forming galaxies"（Abstract）；"star-forming galaxies: these comprise just over two-thirds of the total population, rising to over 70 per cent in the deepest field, ELAIS-N1"（§7）；"Radio-quiet AGN contribute nearly 10 per cent of the total" |
| 冻结数据对应 | 可靠分类率 94.7%（1 − 4,336/81,951）；SFG 67.9%（总计）/ 71.9%（ELAIS-N1）；RQAGN 9.1%（编译器实测，与论文一致） |
| 容差（判分用） | 满分带：可靠分类率 ∈ [93%, 96%]；SFG 总计占比 ∈ [65%, 71%]；RQAGN ∈ [8%, 10.5%]；ELAIS-N1 SFG ∈ [68%, 75%] |

## 锚 A4 — 次级锚：低流量 SFG 主导（讨论用，B/C 维度）

| 项 | 值 |
|---|---|
| 指标名 | SFG 占比随 S_150MHz 的单调性与开关点 |
| 论文数值 | "at lower flux densities... star-forming galaxies take over... accounting for over 90 per cent of sources at the limiting flux density reached in ELAIS-N1"; "The switch between a star-formation dominated population and a radio-loud AGN dominated population occurs at around S_150MHz ~ 1.5 mJy"（§7） |
| 冻结数据对应 | ELAIS-N1：S<100 μJy SFG 84.1%、0.1–0.3 mJy 79.2%、0.3–1 mJy 66.0%、1–1.5 mJy 41.4%、>1.5 mJy 19.2%；50% 交叉 ~1 mJy（编译器实测；与论文「>90% 极限流量」差异源于完整性修正/极限流量定义，需 agent 讨论） |
| 容差（判分用） | 满分带：SFG 占比随流量单调下降；S<100 μJy 占比 ∈ [70%, 95%]；S>1.5 mJy 占比 ∈ [5%, 35%]；50% 交叉 ∈ [0.5, 2.5] mJy；agent 对论文「>90%」与实测 84% 的差异做归因讨论 |

## 编译器探针（冻结数据，2026-08-13）

- 行数：en1 31,610 / lockman 31,162 / bootes 19,179 = 81,951
- 逐类计数与 Table 2 完全一致（见 source_manifest.json probe_checks）
- 百分比：SFG 67.9% / RQAGN 9.1% / LERG 15.6% / HERG 2.1% / Unc 5.3%；可靠分类率 94.7%
- ELAIS-N1 流量分箱 SFG 占比：<100 μJy 84.1%；0.1–0.3 mJy 79.2%；0.3–1 mJy 66.0%；1–1.5 mJy 41.4%；>1.5 mJy 19.2%；50% 交叉 ~1 mJy

> 论文内部一致性提示：Abstract「over 90 per cent at the limiting flux density」与目录实测（S<100 μJy 84.1%）差异源于论文使用了检测完整性/极限流量修正与更细的最暗端定义；agent 若如实报告并归因，判分时视为正确做法。Table 2 计数为精确可复现锚。
