# Solution Report — 2511.22885_mech_props_mlip

**Task**: 独立重算并验证 arXiv:2511.22885v1 *Evaluating Mechanical Property Prediction across Material Classes using Molecular Dynamics Simulations with Universal Machine-Learned Interatomic Potentials*（Evans 课题组，Univ. Adelaide）的核心声明。

**数据来源**: 论文官方 Zenodo 记录 10.5281/zenodo.17730688 的冻结派生数据包（CC-BY-4.0，`data/LICENSE_CCBY4.txt`）。本报告仅使用 `data/4-data/` 下的派生表与逐模型汇总文件，**未重跑任何 MD 模拟、未使用任何模型权重、未下载 13.26 GB 原始时间序列**。

**核心数据文件**: `4-data/all_metrics_deltas_from_reference.xlsx`（Deltas 表，215 行 = 13 材料 × 6 模型 × 3 指标，含 Reference/Predicted/Delta/Absolute_Error/Percent_Error 五列官方产物）；交叉核对文件：`bulk_NVT/<model>/bulk_modulus_results_stress.xlsx`、`nte_results_ref.xlsx`、`stability_results.xlsx`、`bulk_NPT/bulk_moduli_multimethod_results.npz`。

**数据完整性**: 全部 70 个冻结文件 SHA-256 与 `data/CHECKSUMS_SHA256.tsv` 逐一比对通过（本机数据物理位置 `F:\dataset\materials\2511.22885_mech_props_mlip\`，见 `data/DATA_LOCATION.md`）。Deltas 表内 `Delta = Predicted − Reference`、`Percent_Error = 100×|Delta|/|Reference|` 的内部一致性断言全部通过。

**执行环境**: Windows 11，Python 3.13.14，pandas 3.0.5 / numpy 2.5.2 / openpyxl 3.1.5。本任务为派生表聚合，**CPU 即可完成，未使用 GPU**。

---

## 总体结论

| 问题 | 结论 | 判定 |
|---|---|---|
| Q1 方向性（6 模型全部低估 KT、全部高估 αV） | 完全复现 | **复现** |
| Q2 模型排序（前三 = MACE-1 / fairchem_OMAT / Orb-v3，≈41/44/47%） | 完全复现（排序一致；数值 40.0/40.7/43.7 vs 论文 41/44/47，差 ≤3.3 pp） | **复现** |
| Q3 指标级精度（KT MAE 43.8±6.9、CTE 76.2±25.2、偏差中位数 −6.92/+11.38/+18.50） | 部分复现（KT/CTE MAE 与两指标中位数在容差内；Tdecomp 中位数对参考口径敏感，见 §3.3） | **部分复现** |
| Q4 加分（fairchem_ODAC 任务特异精度 66%/23%；CaMn7O12 NPT 9.3 vs NVT 197.8 vs 实验 190 GPa） | 完全复现 | **复现** |

---

## 1. 聚合口径（与官方脚本 `data/3-analysis/score_methods.py`、`data/2-calculate/calculate_all_deltas.py` 一致）

1. **每行 MAE%** = `100 × |Delta| / |Reference|`（与 Deltas 表 `Percent_Error` 列一致）。
2. **每模型 × 每指标 MAE%** = 对 `(Method, Metric)` 分组内全部材料行求 MAE% 均值（`score_methods.py::compute_mae_percent`）。
3. **指标级 MAE**（论文 "43.8% ± 6.9%" 口径）= 对 6 个模型的方法级 MAE% 求均值 ± 样本标准差（numpy `ddof=1`，与论文/校准值一致）。
4. **模型总体平均误差**（论文 "average error across metrics and materials of 41/44/47%"）= 该模型**全部数据行**（13 Bulk + 11 NTE + 13 Stability 等）MAE% 的均值，即逐行等权（下文称 View B）。同时报告**三指标 MAE% 的等权均值**（View A）作为第二种口径；两种口径下模型排序完全一致。
5. **偏差中位数** 两种口径均报告：
   - View 1：该指标全体 Delta 中位数；
   - View 2（论文 "median deviations ... averaged across all models"）：每模型先取 Delta 中位数、再对 6 模型求均值。
6. **材料筛选**：主结果使用 Deltas 表全部材料（macemof 天然缺 CaMn7O12 / Zr-WO4-2 行）。另按论文口径给出剔除 CaMn7O12 与 Zr-WO4-2 的敏感性结果（见 §3.4）——**剔除与否不改变模型前三排序**。
7. **模型名映射**（数据列名 → 论文名）：`orbital`→Orb-v3，`mace-mp-0`→MACE-1，`mace2.0`→MACE-2，`macemof`→MACE-MOF，`fairchem_omat`→fairchem_OMAT，`fairchem_odac`→fairchem_ODAC。

**Predicted ↔ 原始 xlsx 交叉核对**（`code/crosscheck_raw.py`）：Deltas 表全部 215 行 `Predicted` 与
`bulk_NVT/*/bulk_modulus_results_stress.xlsx`（Bulk）、`nte_results_ref.xlsx`（NTE）、`stability_results.xlsx`（Stability，数值按官方管线 clip 到 [50,1000]，忽略 SevenNet-MF-ompa 列）**逐一精确一致**。派生表与原始汇总文件无任何出入。

---

## 2. Q1 — 方向性（PES 软化）: 复现

由 Deltas 表对每个模型计算 Bulk（KT）与 NTE（αV）的 Delta 中位数：

| 模型 | KT 偏差中位数 (GPa) | αV 偏差中位数 (MK⁻¹) | KT<0? | αV>0? |
|---|---|---|---|---|
| MACE-1 | **−4.94** | **+12.54** | ✓ | ✓ |
| MACE-2 | **−8.79** | **+13.71** | ✓ | ✓ |
| MACE-MOF | **−4.87** | **+11.58** | ✓ | ✓ |
| fairchem_OMAT | **−4.88** | **+21.52** | ✓ | ✓ |
| fairchem_ODAC | **−10.97** | **+11.21** | ✓ | ✓ |
| Orb-v3 | **−5.28** | **+19.22** | ✓ | ✓ |

**6 个模型的 KT 偏差中位数全部为负、αV 偏差中位数全部为正**，与论文"systematic underestimation of bulk modulus and overestimation of thermal expansion across all models"完全一致。这与 **PES 软化**机制一致：势能面过软 → 应力/压力偏低 → 拟合 P–V 得到的体模量系统性偏小；体积涨落偏大 → 热膨胀系数系统性偏大。

**对模型平均的中位数**（View 2）：

| 指标 | 本报告 | 论文 | 判定 |
|---|---|---|---|
| KT | −6.62 GPa | −6.92 GPa | 复现（差 0.30，容差 ±2.5） |
| αV | +14.96 MK⁻¹ | +11.38 MK⁻¹ | 复现（差 3.58，容差 ±5） |
| Tdecomp | +4.50 K（Deltas 参考）／ +18.50 K（论文 Table 3 参考） | +18.50 K | 见 §3.3 口径说明 |

注：论文正文给出的 Delta 范围（KT −11.21~243.02、CTE −64.10~152.09、Tdecomp 200~1000）无法由 Deltas 表的 Delta 分布直接复现（本表 KT Delta 范围 −161.0~+53.0、αV −91.7~+153.9、Tdecomp −500~+475），疑为论文基于原始时间序列或不同子集的口径，不影响方向性判定。

---

## 3. Q2/Q3 — 模型排序与指标级精度

### 3.1 每模型×每指标 MAE%（证据表核心）

| 排名 | 模型 | Bulk MAE% | CTE MAE% | Stability MAE% | 总体误差 (View B) | View A |
|---|---|---|---|---|---|---|
| 1 | **MACE-1** | 42.63 | 52.40 | 26.75 | **39.95** | 40.59 |
| 2 | **fairchem_OMAT** | 31.24 | 67.40 | 27.70 | **40.75** | 42.11 |
| 3 | **Orb-v3** | 36.53 | 67.20 | 31.04 | **43.72** | 44.92 |
| 4 | MACE-2 | 48.89 | 63.81 | 31.88 | 47.35 | 48.19 |
| 5 | MACE-MOF | 43.16 | 86.08 | 25.42 | 49.33 | 51.56 |
| 6 | fairchem_ODAC | 52.33 | 122.56 | 22.62 | 63.89 | 65.84 |

（完整列见 `results/evidence_table.csv`。）

### 3.2 Q2 — 模型排序：复现

按总体平均误差（View B，"across metrics and materials"）前三名 = **MACE-1 (40.0%) < fairchem_OMAT (40.7%) < Orb-v3 (43.7%)**，与论文 Abstract "41 %, 44 %, and 47 %" 的**排序与集合完全一致**，数值差 ≤ 3.3 pp（MACE-1 +1.05、fairchem_OMAT +3.25、Orb-v3 +3.28 pp），均在容差内。论文"top performers averaging at MAE of 44 %"（≈(41+44+47)/3=44）亦对应前三级别的均值。

### 3.3 Q3 — 指标级精度

| 指标 | 本报告（对 6 模型方法级 MAE% 均值±样本 std） | 论文 | 判定 |
|---|---|---|---|
| NVT 体模量 (KT) | **42.46% ± 7.75%** | 43.8% ± 6.9% | 复现（均值差 1.34 pp、std 差 0.85 pp，容差 ±4/±3） |
| 热膨胀 (αV) | **76.58% ± 25.00%** | 76.2% ± 25.2% | 复现（差 0.38/0.20 pp） |
| 分解温度 (Tdecomp) | 27.57% ± 3.48% | （论文未给出此口径） | — |

**偏差中位数**（两口径）：

| 指标 | View 1（全体行中位数） | View 2（对模型平均中位数） | 论文 |
|---|---|---|---|
| KT | −5.50 GPa | **−6.62 GPa** | −6.92 GPa |
| αV | +14.54 MK⁻¹ | **+14.96 MK⁻¹** | +11.38 MK⁻¹ |
| Tdecomp | 0.00 K | **+4.50 K**（Deltas 参考）／ **+18.50 K**（论文 Table 3 参考） | +18.50 K |

**Tdecomp 中位数的口径说明**：Deltas 表 `Reference` 列对分解温度采用官方管线口径，将若干材料封顶/设为 1000 K（CaMn7O12=1000、Zr-WO4-2=1000、SiO2=1000；UiO-67=680），与论文 Table 3 参考值（CaMn7O12=550、Zr-WO4-2=1050、UiO-67=670）不同。若以论文 Table 3 参考重算 Stability 的 Delta，每模型 Stability 中位数为 fairchem_ODAC +11、fairchem_OMAT +50、MACE-1 0、MACE-2 0、MACE-MOF 0、Orb-v3 +50，对模型平均 = **+18.50 K，与论文完全一致**。Tdecomp 中位数对参考口径敏感（±14 K），但对模型前三排序、方向性（KT/αV）与所有 MAE 指标无影响。按 TASK 要求"聚合时直接使用该列"，主表采用 Deltas 参考口径（+4.50 K），并附论文参考口径（+18.50 K）作敏感性对照。

### 3.4 材料筛选敏感性

剔除 CaMn7O12 与 Zr-WO4-2 后（对应论文 MAE 比较的筛选口径，MACE-MOF 不含 Ca/W）：

| 模型 | 全材料 (View B) | 剔除后 |
|---|---|---|
| MACE-1 | 39.95% | 37.44% |
| fairchem_OMAT | 40.75% | 41.29% |
| Orb-v3 | 43.72% | 44.24% |
| MACE-2 | 47.35% | 48.71% |
| MACE-MOF | 49.33% | 49.33% |
| fairchem_ODAC | 63.89% | 52.31% |

**前三排序（MACE-1 < fairchem_OMAT < Orb-v3）在两种口径下均不变**，与论文"剔除与否不改变模型排序结论"一致。

---

## 4. Q4 — 加分项：任务特异精度 与 CaMn7O12 例子

### 4.1 fairchem_ODAC 任务特异精度：复现

fairchem_ODAC（在 ODAC 数据上训练的模型）对分解温度表现出明显更优的精度，而总体误差最差：

| 指标 | 本报告 | 论文 |
|---|---|---|
| 总体平均误差 (View B) | **63.9%** | 66% |
| 分解温度 (Stability) MAE | **22.6%** | 23% |
| （参考：Bulk MAE 52.3%、CTE MAE 122.6%） | | |

总体误差差 2.1 pp、分解温度差 0.4 pp，均复现"任务特异精度"结论：模型在与其训练数据域相关的属性（分解温度）上精度显著高于无关属性（热膨胀）。

### 4.2 CaMn7O12 NPT vs NVT：复现

| 来源 | 本报告 | 论文 | 判定 |
|---|---|---|---|
| NPT（300 K，对 4 个可用模型平均） | **9.34 GPa** | 9.3 GPa | ✓ |
| NVT（剔除 fairchem_odac 异常值，4 模型平均） | **197.79 GPa** | 197.8 GPa | ✓ |
| 实验值 | 190 GPa | 190 GPa | ✓ |

NPT 各模型 300 K 值：MACE-1 4.22、MACE-2 3.79、fairchem_OMAT 9.16、Orb-v3 20.19 GPa（fairchem_ODAC 与 MACE-MOF 无 CaMn7O12 数据）。NVT 各模型值：MACE-1 243.02、MACE-2 154.54、fairchem_OMAT 170.88、Orb-v3 222.72、fairchem_ODAC 29.00 GPa（异常值，剔除）。NVT 平均（不含 fairchem_ODAC）= 197.79 GPa，接近实验 190 GPa，而 NPT 平均 9.34 GPa 严重低估——复现论文"CaMn7O12 的 NPT 模拟系统性失效、NVT 更接近实验"的例子。该例子同时印证 Q1 的 PES 软化/欠采样机制（NPT 允许体积涨落导致结构过软甚至失稳）。

---

## 5. 与论文数值的偏差及可能原因

| 项目 | 论文 | 本报告 | 差异 | 可能原因 |
|---|---|---|---|---|
| 前三模型总体 MAE | 41/44/47% | 40.0/40.7/43.7% | ≤3.3 pp | 论文数据版本/聚合轮次差异；本报告用冻结 Deltas 表全材料 |
| KT 指标级 MAE | 43.8±6.9% | 42.46±7.75% | 1.34/0.85 pp | 同上（冻结数据版本 vs 论文投稿版本）；std 采用样本标准差 ddof=1 |
| CTE 指标级 MAE | 76.2±25.2% | 76.58±25.00% | 0.38/0.20 pp | 几乎一致 |
| KT 中位数 | −6.92 GPa | −6.62 GPa | 0.30 GPa | 小；数据版本/中位数口径微差 |
| αV 中位数 | +11.38 MK⁻¹ | +14.96 MK⁻¹ | 3.58 MK⁻¹ | 冻结数据与论文数字的已知差异（校准卡已吸收） |
| Tdecomp 中位数 | +18.50 K | +4.50/+18.50 K | 0（论文参考口径）或 14 K（Deltas 参考口径） | **参考口径差异**：Deltas 表对分解温度参考封顶 1000 K（CaMn7O12=1000、Zr-WO4-2=1000、UiO-67=680）vs 论文 Table 3（550/1050/670）；用论文参考即精确复现 +18.50 |
| KT/αV 范围 | −11.21~243.02 / −64.10~152.09 | −161.0~+53.0 / −91.7~+153.9 | 范围不重合 | 论文范围可能基于原始时间序列/不同子集，派生表无法复现（不影响其余结论） |

总体：**论文的方向性、排序、指标级 MAE、任务特异精度、CaMn7O12 例子全部由冻结数据独立复现**；数值差异集中在 ±几个百分点内，可归因于冻结数据版本（Zenodo 派生产物）与论文投稿数字的口径差异，以及分解温度参考值的封顶方式。所有本报告数值均可由 `data/` 冻结数据重算复现。

---

## 6. 局限性

1. **本任务为"重算验证"而非"重跑 MD"**：所有结论基于官方派生的 Deltas 表与逐模型汇总文件；未验证 MD 本身（如系综、步长、barostat 参数）的正确性，也未检查原始压力/体积时间序列（13.26 GB npz 未包含在冻结包内）。
2. **参考值取自 Deltas 表 `Reference` 列**（官方口径），未混用其他参考集；分解温度参考的封顶方式（1000 K）与论文 Table 3 的差异是 Tdecomp 中位数分歧的根因，已在 §3.3 说明。
3. **模型效率/运行时间**（`job_runtimes.tsv`）未纳入本验证范围（非核心可证伪声明）。
4. 材料子集有限（13 种：9 MOF + 4 无机），结论外推到更大材料空间需谨慎；macemof/fairchem_odac 缺少数材料（Ca/W 体系）行，由官方管线跳过。

---

## 7. 复现指南

```bash
# 1) 主重算（生成 evidence_table.csv 与 metrics.json）
python code/recompute_claims.py        # 自动定位 data 根目录（./data 或 F:\dataset\materials\2511.22885_mech_props_mlip）
# 2) 交叉核对（Predicted ↔ 原始 xlsx，215 行逐一对齐）
python code/crosscheck_raw.py
# 3) 图形（可选）
python code/make_figures.py
```

- **代码**：`code/recompute_claims.py`（主聚合与证据表）、`code/crosscheck_raw.py`（交叉核对）、`code/make_figures.py`（图形）。
- **结果**：`results/evidence_table.csv`（每模型×每指标 MAE%、总体误差、排名、方向性）、`results/metrics.json`（全部关键数值，含两种中位数口径、剔除敏感性、CaMn7O12 明细）、`results/fig_delta_violins.png`（Delta 分布小提琴图）、`results/fig_pred_vs_ref.png`（预测 vs 参考散点图）。
- 数据许可：CC-BY-4.0（Zenodo 10.5281/zenodo.17730688）。引用需署论文与 DOI。

**设备**：CPU（Intel/Windows 11）；未使用 GPU，无训练步骤。
