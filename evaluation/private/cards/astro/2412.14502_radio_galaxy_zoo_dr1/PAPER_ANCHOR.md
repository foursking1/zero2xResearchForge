# PAPER_ANCHOR.md（私有，仅裁判/编译者可见）— 2412.14502_radio_galaxy_zoo_dr1

> 锚必须真实来自论文；冻结数据实测为编译器探针（2026-08-14）。容差用于判分（见 SCORE_RUBRIC）。

## 锚 A1 — 核心结果：目录规模（核心结果锚，判 A 维度）

| 项 | 值 |
|---|---|
| 指标名 | DR1 分类总数 / FIRST 唯一源数 / ATLAS 源数 |
| 论文数值 | **100,185 classifications**（标题/Abstract）；**99,146 FIRST 源**（来自 **99,602 catalogue entries**）；**583 ATLAS 源**（Abstract/§1/§5.4） |
| 出处 | Abstract；§1 Introduction；§5.4 Limitations |
| 冻结数据对应 | FIRST 行 **99,602** / 唯一 RGZID **99,146** / 重复源 414（多余行 456）；ATLAS **583** 行；合计 **100,185**（编译器实测，与论文一致） |
| 容差（判分用） | 满分带：FIRST 99,602±3；ATLAS 583±2；合计 100,185±5；唯一源 99,146±10 |

## 锚 A2 — 核心结果：共识阈值与可靠性（核心结果锚，判 A 维度）

| 项 | 值 |
|---|---|
| 指标名 | consensus 收录阈值 / 平均 reliability |
| 论文数值 | 收录标准 **consensus ≥ 0.65**（§3.3/§5.4："classification consensus levels greater than or equal to 0.65"）；平均 **reliability 0.83**（Abstract，基于加权 consensus，§3.3.1 专家标定） |
| 冻结数据对应 | `CL` min = **0.65**、Q1 0.92、median 1.0、mean 0.942、`CL<1` 占比 30.1%（编译器实测；全部 ≥ 0.65 ✓）；0.83 reliability 需专家子集，不可从本包重算 |
| 容差（判分用） | 满分带：min=0.65（±0.01）；median=1.0；mean ∈ [0.90, 0.98]；agent 须说明 0.83 的不可重算性 |

## 锚 A3 — 子论断：多分量射电源占比（可证伪子论断，判 A/C 维度）

| 项 | 值 |
|---|---|
| 指标名 | FIRST 多分量源数量与占比 |
| 论文数值 | **16,354 个 FIRST 源由多于一个分量组成**（§5.1："Of the 99,146 FIRST radio sources (from 99,602 catalogue entries) presented, 16,354 DR1 radio sources are composed of more than one component"），即 ~16.5% |
| 冻结数据对应 | `N_comp>1` 行级 **16,531** / 唯一源级 **16,334**；`N_peaks>1` 唯一源级 34,741；ATLAS `N_comp>1` = 1（编译器实测） |
| 容差（判分用） | 满分带：唯一源级 ∈ [16,334±150] 或行级 ∈ [16,531±150]；agent 对与论文 16,354 的差异（Δ20/Δ177，版本与口径）做归因 |

## 锚 A4 — 附带（B/C 维度用）

| 项 | 值 |
|---|---|
| 指标名 | 宿主星系表规模 / N_votes 分布 |
| 论文数值 | 每源两条表：radio classification + host galaxy（§4） |
| 冻结数据对应 | 宿主表 FIRST 99,602 行 × 23 列、ATLAS 583 行 × 19 列；`N_votes` FIRST mean 33.1 / max 9,412（编译器实测） |
| 容差（判分用） | 宿主表行数与分类表一致（99,602/583） |

## 编译器探针（冻结数据，2026-08-14）

- FIRST 分类表 99,602 行；ATLAS 583 行；合计 100,185（= 论文 100,185 ✓）
- 唯一 RGZID：FIRST 99,146（= 论文 99,146 ✓）/ ATLAS 583
- 重复源：414 个 RGZID 出现 >1 次，多余行 456（= 99,602 − 99,146）
- `CL`：min 0.65 / Q1 0.92 / median 1.0 / mean 0.9416 / CL<1 占 30.1%
- `N_comp>1`：行级 16,531 / 唯一源级 16,334（论文 16,354，Δ20 版本差）；`N_peaks>1` 唯一源级 34,741
- ATLAS：583 行，`N_comp>1` = 1；宿主表 FIRST 99,602 / ATLAS 583
- 论文对照结论：规模与共识阈值声称完全成立；多分量占比 ~16.4–16.5%（口径相关）成立

> 边界提示：Zenodo v1 目录与论文版本存在微小差异（16,334 vs 16,354）；「平均 reliability 0.83」依赖论文的专家标定子集，CSV 中无此列；agent 若正确说明这两点视为正确做法。
