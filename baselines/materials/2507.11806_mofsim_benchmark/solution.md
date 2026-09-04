# MOFSimBench DFT 参考体弹模量（B0）数据集 — 独立复算报告

**任务**：2507.11806_mofsim_benchmark（L1 critical claim）
**论文**：H. Kraß, J. Huang, S. M. Moosavi, *MOFSimBench: Evaluating Universal Machine Learning Interatomic Potentials In Metal–Organic Framework Molecular Modeling*, arXiv:2507.11806 (2025)。
**数据来源**：论文官方 GitHub 仓库 [AI4ChemS/mofsim-bench](https://github.com/AI4ChemS/mofsim-bench)（MIT License，main 分支 2026-08-13 快照）+ 论文 arXiv 版 SI Table S.1（人工提取 CSV）。冻结文件见 `data/`。
**执行设备**：CPU（本任务为解析/拟合，无 GPU 训练）。

---

## 0. 数据完整性与来源校验

使用前对所有冻结文件做 SHA-256 校验（`data/checksums.sha256`，CRLF 已用 `tr -d '\r'` 处理）：

```
bulk_modulus_eos_dft_reference.csv: OK    heat_capacity_cv_300k_dft_reference.csv: OK
opt_{MOF-5,IRMOF-10,UiO-66,HKUST-1}_primitive.cif: OK    SI_Table_S1_bulk_modulus_GPa.csv: OK
...（9/9 全部 OK）
```

未修改任何冻结文件；未引入任何外部数据。复算脚本：`code/analyze_mofsim.py`（独立实现，仅用 `numpy`/`scipy`/`pandas`）。

---

## 1. 方法与口径

### 1.1 EOS 形式
论文 Methods："The bulk modulus was computed from a fitted Birch-Murnaghan equation of state." 采用**三阶 Birch–Murnaghan EOS**（Eulerian 有限应变形式，与任务给出公式代数等价）：

```
E(V) = E0 + (9/16)·V0·B0·[ (η−1)³·B1 + (η−1)²·(6−4η) ],   η = (V0/V)^(2/3)
```

拟合单位：E 用 hartree、V 用 Å³，得到 B0（hartree/Å³）后乘以换算系数：

```
1 hartree/Å³ = 4359.7447222071 GPa
```

### 1.2 拟合细节（可复现）
- **V0 初值**：取 `energies_au` 最低点对应的体积。
- **能量中心化**：拟合前减去 `E.min()`，再拟合相对能量偏移 E0′（总 E0 = E0′ + E.min()）。这是为了超大胞（总能量 ≈ 1e5 Ha，如 `IPAQOI_full`、`AVAKEP02_full`、`GUPCEA_full`）的数值尺度稳健性——绝对能量 1e5 Ha 下，若直接拟合 4 参数会严重病态。
- **多初值 + 显式参数尺度**：B0 初值网格 {0.5,1,2,5,10,20,50,100,200} GPa × B1 初值网格 {2,3,4,5,6}，共 45 组起点；`scipy.optimize.least_squares`，`x_scale=[max(1,E_range), V0, 50, 1]`（E0′、V0、B0、B1 各自的自然尺度）。
- **解的选择**：取**代价最小**的解，并要求 `|B1| ≤ 15`（B1 为体弹模量的压强导数，物理上通常在 3–6 附近；`|B1|>15` 的"全局最优"解是近平坦 E(V) 曲线上的退化解）。若无满足物理界的解，则回退到全局最小代价解。同时记录**不约束 B1 的纯最小代价解**作为敏感性（见 §3.2）。
- **B1 处理**：自由拟合（论文未指定固定值；编译期核验亦为 B1 自由）。

### 1.3 与论文口径的差异/说明
- 论文/仓库未公开其拟合程序；本报告按论文 Methods 描述与任务方向提示独立实现。
- 数据表中 `strains` 列为体积缩放因子，拟合直接用 `volumes_A3`–`energies_au` 点，不使用 strain 列作为自变量。
- 本任务**不要求**复算 uMLIP 预测类数值（Figure 6 MAE 与 Table S.1 UFF 行），它们需要 SI 中的 uMLIP/UFF 模拟输出，冻结数据不可复算（见 §6）。

---

## 2. C1 — 四个原型 MOF 的 DFT B0（主锚，Table S.1 DFT 行）

对 `bulk_modulus_eos_dft_reference.csv` 中 `structure ∈ {MOF-5, IRMOF-10, UiO-66, HKUST-1}` 行的 (V,E) 点做上述三阶 BM 拟合。结果（证据表 `results/evidence_table_prototypes.csv`，metrics 见 `results/metrics.json`）：

| 结构 | 论文 Table S.1 (GPa) | CSV `B0_GPa` (GPa) | 拟合 B0 (GPa) | Δ vs 论文 (GPa) | Δ vs CSV (GPa) | V0 (Å³) | E0 (hartree) | B1 | 应变点数 |
|---|---|---|---|---|---|---|---|---|---|
| MOF-5 | 16.06 | 16.0623 | 16.0622 | +0.0022 | −0.0001 | 4441.52 | −1188.97296 | 3.83 | 5 |
| IRMOF-10 | 9.40 | 9.3993 | 9.3991 | −0.0009 | −0.0002 | 10552.10 | −1408.08907 | 3.64 | 5 |
| UiO-66 | 37.50 | 37.4997 | 37.4999 | −0.0001 | +0.0002 | 2279.06 | −1087.26881 | 2.19 | 11 |
| HKUST-1 | 23.58 | 23.5815 | 23.5812 | +0.0012 | −0.0003 | 4675.11 | −1771.10099 | 2.52 | 5 |

**判定：C1 复现（reproduced）**。四个拟合 B0 与 Table S.1 DFT 行（16.06/9.4/37.5/23.58 GPa）偏差均 ≤ 0.003 GPa（容差 ±0.5 GPa），与 CSV `B0_GPa` 列偏差均 ≤ 0.0003 GPa（容差 ±0.05 GPa）。拟合 E0 与数据最低能量一致（±5e-6 Ha），V0 落在采样范围内。

---

## 3. C2 — 数据集规模与全 100 结构拟合一致性

### 3.1 规模
- 冻结 `bulk_modulus_eos_dft_reference.csv` 行数 = **100**，`structure` 唯一名 = 100，`cif_name` 唯一 = 100。
- 应变点数：99 个结构各 5 个应变点，UiO-66 为 11 个 → **全部 ≥ 5 个应变点**。
- 与论文正文 "a larger set of 100 MOFs, COFs, and zeolites" 完全一致。

### 3.2 全 100 结构拟合偏差统计（vs CSV `B0_GPa` 列）

| 指标 | 数值 |
|---|---|
| 行数 / 唯一结构数 | 100 / 100 |
| \|fit−CSV\| 中位偏差 | 0.0008 GPa |
| \|fit−CSV\| 平均偏差 | 5.94 GPa |
| \|fit−CSV\| 最大偏差 | 266.36 GPa |
| ≤ 0.5 GPa 的结构数（占比） | **95 / 100（95%）** |
| ≤ 0.1 GPa 的结构数（占比） | 93 / 100（93%） |
| > 0.5 GPa 的结构数 | 5 |

**敏感性（B1 不约束、纯最小代价）**：≤0.5 GPa 为 94/100、≤0.1 GPa 为 92/100。两种选择规则差异仅体现在 1–2 个近退化拟合结构上（见下），结论不变。

### 3.3 偏差 > 0.5 GPa 的结构清单（如实列出，不静默丢弃）

| 结构 | CSV B0 | 拟合 B0 | 偏差 | 拟合 B1 | 可能原因 |
|---|---|---|---|---|---|
| IPAQOI_full | 10.16 | 276.52 | 266.36 | 0.96 | **巨型超胞**（\|E\|≈1.1e5 Ha）：存储的 (V,E) 局部曲率对应 B0≈276 GPa，与 CSV 值（10 GPa）矛盾 → 论文 Methods 承认的"不稳定拟合，被排除" |
| AVAKEP02_full | 6.87 | 187.00 | 180.13 | 2.04 | 巨型超胞（\|E\|≈1.0e5 Ha）：同上，局部曲率 B0≈187 GPa |
| GUPCEA_full | 5.54 | 150.64 | 145.10 | 2.17 | 巨型超胞（\|E\|≈9.9e4 Ha）：同上，局部曲率 B0≈151 GPa |
| Zn-MOF-74 | 20.48 | 19.07 | 1.41 | 4.76 | 近扁平 E(V)（范围 1.9e-3 Ha）：CSV 值只对应全局最小代价解（B1=−85，非物理）；在物理 B1 约束下偏离 |
| boydwoo_str_m3_o7_o27_pcu_sym_8 | 6.79 | 7.40 | 0.61 | 65.24 | 近扁平 E(V)（范围 4.5e-4 Ha）：B1 自由拟合病态（全部收敛于 B1≈65 退化解），CSV 值无法由自由 V0 的 BM 拟合复现 |

**对前三个巨型超胞的进一步核验**：直接由数据局部曲率估计 B0 = V0·d²E/dV²（能量最低点附近）得到 IPAQOI≈275、AVAKEP02≈185、GUPCEA≈145 GPa，与我的拟合一致，而 CSV 列（5–10 GPa）无法由任何 V0 在采样范围内的 BM 拟合产生——即 CSV 值来自**退化/不稳定拟合**（V0 外推至采样范围之外）。这正对应论文 Methods 所述："The volume at the energy minimum deviating by more than 1% from the optimized volume indicates an unstable fit and those structures were excluded"。因此这三个结构属于论文自认的不稳定拟合，不能由冻结 (V,E) 点重算。

### 3.4 C2 结论
**支持（supported）"100 结构 DFT 体弹模量参考集" claim**：
- 行数恰好 100、结构名唯一、每结构 ≥5 应变点；
- 同一三阶 BM 拟合可复现 **95/100** 的 `B0_GPa` 列（≤0.5 GPa），其中 93/100 ≤0.1 GPa；
- 其余 5 个偏差结构均可用"论文 Methods 自认的不稳定/病态拟合"解释（3 个巨型超胞 + 2 个近平坦曲线），不构成对数据集存在的反驳。

---

## 4. C3 — 佐证

### 4.1 (a) 4 个原型 CIF 与 EOS 表 `structure` 名的对应（`results/cif_correspondence.csv`）

| 结构 | CIF 文件 | EOS 表 `cif_name` | CIF 胞体积 (Å³) | 表 V(应变=1) (Å³) | 相对差 | 原子数 | 组成 |
|---|---|---|---|---|---|---|---|
| MOF-5 | opt_MOF-5_primitive.cif | opt_MOF-5_primitive | 4440.261 | 4440.261 | ≈0 | 106 | Zn8C48O26H24 |
| IRMOF-10 | opt_IRMOF-10_primitive.cif | opt_IRMOF-10_primitive | 10552.157 | 10552.157 | ≈0 | 166 | Zn8C84O26H48 |
| UiO-66 | opt_UiO-66_primitive.cif | **opt_AW_UiO-66** | 8986.793 | 2278.984 | **+294%** | 432 | Zr24C192O120H96 |
| HKUST-1 | opt_HKUST-1_primitive.cif | opt_HKUST-1_primitive | 4675.715 | 4675.715 | ≈0 | 156 | Cu12C72O48H24 |

- **MOF-5 / IRMOF-10 / HKUST-1**：CIF 文件名与 EOS 表 `cif_name` 完全一致，且 CIF 胞体积与表内 V(应变=1.0) 逐位一致（相对差 < 1e-5 %），一一对应成立。
- **UiO-66（注意）**：CIF 文件名 `opt_UiO-66_primitive.cif` 对应 `structure=UiO-66`（组成含 Zr24，确为 UiO-66 框架，名称对应成立）；但 EOS 表该行 `cif_name` 是 `opt_AW_UiO-66`，且 CIF 胞体积 8986.8 Å³（近立方 ~432 原子胞）与 EOS 表 V(应变=1)=2279.0 Å³（菱面体原胞）差 ~3.94 倍。**即 UiO-66 的 EOS 参考计算用的是 `opt_AW_UiO-66` 原胞，而非随附的 `opt_UiO-66_primitive.cif`**（后者是同一框架的另一种（更大）表示）。名称级一一对应成立，但细胞级对应在 UiO-66 上不成立，已如实报告。

### 4.2 (b) 热容参考表（`results/heat_capacity_stats.json`）

- 冻结 `heat_capacity_cv_300k_dft_reference.csv`：**232 行，232 个唯一框架**。
- `cv_300K_JperKperg` 分布：**中位数 0.7944**，四分位 [0.7233, 0.8658]，范围 [0.4288, 1.0943]，均值 0.7941（单位 J/K/g）。
- 论文 Figure 7 及正文称 DFT 热容参考覆盖 **231 个 MOF/COF/沸石**（源自 Ref. 57 数据集）。冻结表为 **232 行，比论文多 1 行**。
- **差异说明**：本任务不裁决该 1 行差异。可能解释包括：(i) 论文统计口径（如排除某个重复/异常框架）与仓库表内容不同；(ii) 论文写成 231 时未计入后来补入的 1 个框架；(iii) 仓库 `collect_cv_300k.csv` 中某个条目在论文分析时被剔除。复算方仅能如实报告：冻结数据 232 行，论文声明 231，差 1。

---

## 5. 结论总表

| Claim | 判定 | 依据 |
|---|---|---|
| C1：四原型 DFT B0 = 16.06 / 9.4 / 37.5 / 23.58 GPa 可复算 | **复现** | 拟合 16.0622 / 9.3991 / 37.4999 / 23.5812 GPa，vs 论文 ≤0.002 GPa，vs CSV ≤0.0003 GPa |
| C2：100 结构 DFT 体弹模量参考集（100 行、≥5 应变点） | **支持** | 恰 100 行、结构名唯一、≥5 点；同口径拟合复现 95/100（≤0.5 GPa）、93/100（≤0.1 GPa）；5 个偏差结构均符合论文 Methods"不稳定拟合被排除" |
| C3a：4 个原型 CIF 与 structure 名一一对应 | **基本支持（1 项需注明）** | 3/4 CIF 与 EOS 行细胞逐位一致；UiO-66 名称对应但细胞不同（EOS 用 opt_AW_UiO-66，CIF 为另一胞） |
| C3b：热容参考表覆盖 231 框架 | **如实报告差异** | 冻结表 232 行（唯一框架 232）；中位 cv(300 K)/g=0.7944，范围 [0.429, 1.094]；与论文 231 差 1，不裁决 |

**总体结论**：论文核心 claim（DFT 参考 B0 数据集真实、可复算、覆盖 100 个 MOF/COF/沸石，且四原型 B0 为 16.06/9.4/37.5/23.58 GPa）**得到支持（supported）**。C1 精确复现；C2 在 100 结构规模与 ≥95% 可复现性上成立，剩余偏差结构与论文 Methods 自述的不稳定拟合一致；C3 的 231 vs 232 差异如实报告。

---

## 6. 局限性

1. **未复算项**：Figure 6 的 uMLIP MAE（如 MACE-MP-MOF0=3.14、SevenNet-mf-ompa=3.35、eSEN-OAM=2.64、orb-d3-v2=72.29 GPa）与 Table S.1 UFF 行（14.5/7.6/28.7/42.4 GPa）需要 SI 中的 uMLIP/UFF 模拟输出，冻结数据不含，**未复算**；论文正文这些数值仅作背景引用，不作本报告证据。
2. **拟合方法不确定性**：论文未公开拟合程序；B1 自由 + 物理约束解的选择是独立实现，与仓库原始程序可能存在的局部极小差异主要体现在 1–2 个近平坦 E(V) 结构（94 vs 95/100 的敏感性区间）。
3. **UiO-66 CIF 细胞不匹配**：随附 `opt_UiO-66_primitive.cif` 与 EOS 表 `opt_AW_UiO-66` 非同一细胞，C3a 的名称级对应不受影响，但细胞级核对对 UiO-66 不适用。
4. **超大胞 CSV B0 不可重算**：IPAQOI_full / AVAKEP02_full / GUPCEA_full 三个巨型超胞的 CSV `B0_GPa` 值（5–10 GPa）与冻结 (V,E) 点的局部曲率（145–276 GPa）不一致，按论文 Methods 判定为不稳定拟合；若这些值在论文后续分析中被使用，其可靠性值得注意。

## 7. 复现命令

```bash
python agent_solution/code/analyze_mofsim.py
```

脚本自动：校验 `data/checksums.sha256` → 读取冻结 CSV/CIF → 三阶 BM 拟合（C1+C2）→ CIF 对应与热容统计（C3）→ 写出 `results/*.csv`、`results/*.json`。
