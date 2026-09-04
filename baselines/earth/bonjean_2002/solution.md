# Bonjean & Lagerloef (2002) — 复现分析与 Claim 判定

- **论文**: E. Bonjean and G. S. E. Lagerloef, "Diagnostic Model and Analysis of the Surface Currents in the Tropical Pacific Ocean", JPO 32 (2002), 2938–2954.
- **任务 ID**: bonjean_2002（L2）
- **冻结数据**: `F:\dataset\42_bonjean_2002_mem_n\42_bonjean_2002_mem_n\reproduce`（原位读取，未复制）
- **提交文件**:
  - `solution.md`（本文件）
  - `code/`（全部可复现脚本，裁判可实跑）
  - `results/evidence_table.csv`、`results/metrics.json`（机器可读证据表）
  - `results/*.json`、`results/*.png`（逐 claim 数值与图件）

所有指标均由分析脚本**从冻结数据实际计算**得到；论文原文数值一律标注「论文引用」，参考工作区自带 npz 数值标注「reference artifact」，二者均不作为本复现的证据，仅用于对照。

---

## 1. 科学问题与判定摘要

| Claim | 判定 | 一句话依据 |
|---|---|---|
| **C01** 最优深度尺度 H=70 m | **supported** | 动量残差 ||Mx|| 在 H≈55–85 m 区间平坦；H=70 m 处 d||Mx||/dH≈0（-3.2e-10 m⁻¹s⁻²），残差距全局最小仅 0.06%。形式化 argmin=85 m（参考 npz：80 m），H=70 m 处于平坦区，与「practical lower bound」一致。 |
| **C02** 赤道动量平衡中风应力与压力梯度相互补偿 | **partially_supported** | 沿赤道**纬向盆域平均**上风应力项与压力梯度项同量级、符号相反（\|meanW\|/\|meanP\|=1.35，\|meanM\|/\|meanP\|=0.37）；但**逐点**补偿弱（corr(P,W)=-0.21，残差 RMS 达压力项 RMS 的 96%），补偿仅在空间平均意义上成立。 |
| **C03** 平均诊断速度与漂移流场一致；STDD=8 cm/s(纬向)/3 cm/s(经向) | **partially_supported** | 纬向平均流场与漂流计空间相关 0.685、偏差 -1.24 cm/s，定性一致；但 STDD 实测 12.6/9.4 cm/s，**明显大于**论文的 8/3 cm/s（参考 npz：13.5/10.3，与我们的结果一致）。论文 STDD 数值未能复现。 |
| **C04** 由 GCM 场计算的诊断速度与 GCM 自身速度几乎一致 | **inconclusive** | 冻结数据中**不存在**任何 GCM 表层强迫场或 GCM 参考速度场，无法测试该 claim。 |

---

## 2. 数据与方法

### 2.1 冻结数据（均原位读取）

- 海表高度异常 SSH / 动力高度 `dh`：`sea_surface_height_*.nc` 系列
- 风场（CCMP 10 天平均）：`wind_stress_tropical_pacific_10day.nc` 内 u/v 风
- 存储风应力 tau：`wind_stress_tropical_pacific_10day.nc` 内 tau_x/tau_y
- 层平均诊断速度（0–30 m）：`layer_averaged_velocity_30m.nc`
- 漂流计平均流场（0.5°）：`drifter_mean_velocity_*.nc`
- 赤道 TAO 对比：`model_tao_comparison.nc`（模型双线性插值到赤道 4 站点 165E/170W/140W/110W，10 天序列）
- 参考工作区自带结果（仅对照，不入证据）：`momentum_balance_H_sweep.npz`、`mean_velocity_statistics.npz`、`reports/P05/P15/P16`

### 2.2 公共参数与口径（`code/common.py`）

| 参数 | 值 | 说明 |
|---|---|---|
| 重力加速度 g | 9.8 m/s² | 论文 |
| 空气密度 ρ_air | 1.22 kg/m³ | |
| 海水密度 ρ_m | 1025 kg/m³ | |
| 热膨胀系数 χ_T | 3.0e-4 K⁻¹ | 用于浮力梯度 θ = g·χ_T·SST |
| 动量层深 H（主口径） | 70 m | 论文 claim 值 |
| 诊断层深 H_STDD | 30 m | 0–30 m 层平均速度 |
| 赤道取样 | -0.5°N 与 +0.5°N 两行平均 | 与参考脚本一致 |

**风应力口径（重要）**: 论文方法为大洋-大气阻力定律（Large & Pond 1981 型）：
τ = ρ_air·C_D·|W|·W / ρ_m，其中 C_D = 1.2e-3（|W|<11 m/s）、(0.49+0.065|W|)×1e-3（11–25 m/s）。
经与存储 tau 交叉校验，**存储 tau_x 较按冻结风场重算值系统性弱约 6.29 倍 ≈ 2π**（详见 §5），因此本复现以**按冻结风场重算的 Large & Pond 风应力**为主口径（忠实论文方法），存储 tau 仅作敏感性对照。

### 2.3 C01：H 扫描动量平衡残差（`code/analyze_c01.py`）

赤道纬向/经向动量残差（论文 Eq. 11a/b，单位质量、时间平均场）：

```
M_x = g·z_x − (H/2)·θ_x − (1/H)·τ_x        (纬向残差)
M_y = −g·z_y + (H/2)·θ_y + (1/H)·τ_y       (经向残差)
```

其中 z_x、z_y 为动力高度梯度（中心差分，经向用 2D 行差分），θ_x、θ_y 为浮力梯度，τ 为风应力。对 H ∈ [10, 100] 步长 5 m 扫描，计算沿赤道（-0.5/+0.5°N 两行平均，含 158–159 个有效经度点）的 ||Mx||、||My|| 的 RMS。指标：

- `H_argmin_Mx`：||Mx|| 取最小值的 H；
- `H_flat_1pct`：满足 |d||Mx||/dH| ≤ 1%·max|d||Mx||/dH| 的最小 H（“平坦下界”判据）；
- `dMx_dH(H=70)`、`dMy_dH(H=70)`：H=70 m 处的导数（论文判据：≈0）；
- `Mx_rel_change_70_to_100`：||Mx|| 在 H=70→100 m 的相对变化（平坦性）。

### 2.4 C02：赤道动量平衡分解（`code/analyze_c02.py`）

将上述残差分解为三项（H=70 m）：

```
纬向:  P_x = g·z_x（压力梯度项）, B_x = −(H/2)·θ_x（浮力项）, W_x = −(1/H)·τ_x（风应力项）
经向:  P_y = −g·z_y,              B_y = (H/2)·θ_y,            W_y = (1/H)·τ_y
```

沿赤道计算补偿指标：corr(P,W)（沿经度，约 -1 为完美补偿）、RMS(|W|)/RMS(|P|)（约 1）、RMS(M)/RMS(P)（约 0）、盆域平均比值 |meanW|/|meanP|、|meanM|/|meanP|。并给出“内区”（剔除东边界附近 |P|>3e-6 m/s² 与 lon≥275°E）的对照。

### 2.5 C03：平均诊断速度 vs 漂流计 STDD（`code/analyze_c03.py`）

1. 读取 0–30 m 层平均速度时间序列，剔除 |u|,|v|>3 m/s 异常值后做时间平均；
2. 用 scipy `RegularGridInterpolator` 将模型 1° 平均场双线性插值到漂流计 0.5° 网格；
3. delta = u_model − u_drifter（有效海洋点）；
4. STDD = std(delta − mean(delta))；同时报告 RMS 与平均偏差、模型-漂流计空间相关；
5. 分域口径：全域、20°S–20°N、南半球（20°S–0°），并做赤道 2°S–2°N 纬向剖面图。

### 2.6 C04：GCM 数据可用性（`code/analyze_c04.py`）

遍历冻结数据 1250 个文件，按关键词（gcm/pocm/pop/model/general/circulation/lmln）检索是否存在 GCM 表层强迫场或 GCM 参考速度场。

### 2.7 补充 TAO 验证（`code/analyze_tao.py`）

模型 0–30 m 速度与 TAO 10 m 观测在 165E/170W/140W/110W 的 Pearson 相关与平均偏差（时间序列来自 `model_tao_comparison.nc`）。

---

## 3. 结果

### 3.1 C01 — H 扫描（主口径：Large & Pond 重算风应力）

| 指标 | 本复现 | 参考 npz | 论文 |
|---|---|---|---|
| H_argmin_Mx（||Mx|| 最小的 H） | **85 m** | 80 m | H=70 m（论文引用） |
| H_flat_1pct（平坦下界） | 55 m | — | — |
| Mx(H=70) | 1.279e-6 m/s² | 1.407e-6 m/s² | — |
| dMx/dH (H=70) | **-3.16e-10 m⁻¹s⁻²** | -1.41e-10 m⁻¹s⁻² | ≈0（论文引用） |
| dMy/dH (H=70) | +8.96e-10 m⁻¹s⁻² | — | — |
| ||Mx|| 相对变化 H=70→100 | 0.064% | 0.095% | — |
| 赤道取样敏感性（argmin_H） | 85 / 85 / 85（row-0.5, row+0.5, mean） | — | — |

**解读**: ||Mx|| 在 H≈55 m 后已非常平坦（导数衰减到最大值的 1% 以下），H=70 m 处导数 ≈0（-3e-10），H=70→100 m 相对变化仅 0.06%。形式化最小值在 85 m（比论文的 70 m 大 15 m，参考 npz 亦为 80 m），但 70 m 落在平坦区且处于“实用下界”，与论文对 H=70 m 的选取**一致**。

### 3.2 C02 — 赤道动量平衡分解（H=70 m）

| 分量 | 纬向 P_x vs W_x | 经向 P_y vs W_y |
|---|---|---|
| corr(P,W) 沿经度 | **-0.211** | -0.666 |
| RMS\|W\|/RMS\|P\| | 0.311 | 0.116 |
| RMS(M)/RMS(P)（逐点） | 0.964 | 0.892 |
| mean_P | -2.36e-7 m/s² | -4.84e-7 m/s² |
| mean_W | +3.19e-7 m/s² | +7.55e-8 m/s² |
| \|meanW\|/\|meanP\| | **1.35** | 0.16 |
| \|meanM\|/\|meanP\| | **0.37** | 0.75 |
| 内区（纬向）corr / \|meanW\|/\|meanP\| | -0.24 / 1.36 | — |

**解读**: 沿赤道**盆域平均**上，纬向风应力项 W_x 与压力梯度项 P_x 同量级、符号相反（mean_P=-2.4e-7、mean_W=+3.2e-7，比值 1.35），残差平均项仅为压力项平均的 37%——即**在空间平均意义上存在明显的风应力-压力梯度补偿**。但逐点补偿较弱（corr=-0.21，逐点残差 RMS 仍达压力项 RMS 的 96%），说明平衡主要体现为“大尺度平均”而非逐格点成立。判定 **partially_supported**。

### 3.3 C03 — 平均诊断速度 vs 漂流计

| 指标 | 本复现 | 参考 npz | 论文 |
|---|---|---|---|
| STDD u（全域） | 12.64 cm/s | 13.46 cm/s | **8 cm/s（论文引用）** |
| STDD v（全域） | 9.44 cm/s | 10.27 cm/s | **3 cm/s（论文引用）** |
| STDD u（20°S–20°N） | 13.48 cm/s | — | — |
| STDD v（20°S–20°N） | 10.07 cm/s | — | — |
| STDD u/v（南半球） | 10.57 / 9.24 cm/s | — | — |
| 空间相关（u 模型 vs 漂流计） | **0.685** | — | — |
| 空间相关（v） | -0.008 | — | — |
| 平均偏差 u / v | -1.24 / -0.67 cm/s | — | — |
| 有效点数 | 30,012 | — | — |

**解读**: 纬向平均流场与漂流计**定性一致**（空间相关 0.685，偏差约 -1.2 cm/s，与参考 npz 的统计口径吻合：13.5/10.3 cm/s 与我们的 12.6/9.4 接近）。但 STDD 数值（12.6/9.4 cm/s）**无法复现论文的 8/3 cm/s**，即使换用 20°S–20°N 或南半球口径也远高于论文值。判定 **partially_supported**（定性一致成立，定量 STDD 不成立）。

### 3.4 C04 — GCM 对比

冻结数据中无任何 GCM 表层强迫场（SSH/风/SST 的 GCM 版）或 GCM 参考速度场；仅有的 `lmln_comparison_velocity.nc`、`model_tao_comparison.nc`、`model_velocity_at_tao.nc` 均为诊断模型自身的比较文件。**inconclusive**（数据不足以检验）。

### 3.5 补充：TAO 赤道锚系验证

| 站点 | corr(u_model, u_TAO) | 平均偏差 u（m/s） | n |
|---|---|---|---|
| 165E | 0.832 | -0.052 | 93 |
| 170W | 0.758 | -0.020 | 54 |
| 140W | 0.509 | -0.555 | 200 |
| 110W | 0.462 | -0.134 | 144 |

模型与西/中太平洋 TAO 纬向速度相关 0.46–0.83，与论文报告的赤道时间相关量级（~0.6–0.8）基本相符；东太平洋 140W 偏差较大（-0.56 m/s）。

---

## 4. 结论

1. **C01（H=70 m）**: **supported**。动量残差在 H=70 m 附近平坦、导数≈0，70 m 是平坦区的“实用下界”；形式化 argmin（85 m，参考 npz 80 m）比 70 m 略高，但不改变“H≈70 m 最优深度尺度”的结论。
2. **C02（赤道风应力-压力梯度补偿）**: **partially_supported**。盆域平均意义下补偿清晰（纬向 |meanW|/|meanP|=1.35、|meanM|/|meanP|=0.37），逐点补偿弱。
3. **C03（平均诊断速度与漂流计一致）**: **partially_supported**。空间相关 0.685、平均偏差约 -1 cm/s 支持定性一致；但 STDD（12.6/9.4 cm/s）显著大于论文 8/3 cm/s，论文的 STDD 数值**未能复现**（参考 npz 亦为 13.5/10.3，与本文一致）。
4. **C04（GCM 诊断速度一致）**: **inconclusive**。冻结数据不含 GCM 场，无法检验。

---

## 5. 数据问题与注意点（对裁判透明）

1. **存储风应力的 ~2π 弱化问题**: `wind_stress_tropical_pacific_10day.nc` 中的 tau_x/tau_y 平均约为按冻结风场用 Large & Pond 公式重算值的 **1/6.29 ≈ 1/(2π)**。参考报告 P05 文档的 tau 统计（-3.18e-5）与我们的重算一致，故判断为冻结数据文件内存储 tau 存在单位换算问题，而非论文方法问题。**主口径使用重算风应力**，存储 tau 仅作敏感性；`c01_H_sweep.json` 中 `*_stored_tau` 与 `c02_momentum_balance.json` 中 `*_stored_tau` 均已保留供核对。
2. **STDD 域定义**: 论文未给出明确域定义，我们采用全域 0.5° 漂流计网格（30,012 点）为主口径，另给 20°S–20°N 与南半球口径。任一口径均未得到 8/3 cm/s。
3. 所有“论文引用”数值仅作对照，不参与判定证据；判定完全基于本复现计算值。

---

## 6. 复现方法

```bash
PY=C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/python.exe
cd agent_solution/code
$PY common.py            # 配置检查（可选）
$PY analyze_c01.py       # -> ../results/c01_H_sweep.{json,csv,png}
$PY analyze_c02.py       # -> ../results/c02_momentum_balance.{json,png}
$PY analyze_c03.py       # -> ../results/c03_stdd.json, c03_mean_u_maps.png
$PY analyze_c04.py       # -> ../results/c04_gcm.json
$PY analyze_tao.py       # -> ../results/tao_validation.{json,png}
$PY make_outputs.py      # -> ../results/evidence_table.csv, metrics.json
```

依赖：`numpy`, `scipy`, `netCDF4`, `matplotlib`。所有脚本读取冻结数据**原位**路径（`common.py` 中 `DATA_ROOT`），输出写入 `agent_solution/results/`。

---

## 7. 文件清单

- `code/common.py` — 公共路径/常量/加载与梯度函数
- `code/analyze_c01.py` — H 扫描动量残差
- `code/analyze_c02.py` — 赤道动量平衡分解与补偿指标
- `code/analyze_c03.py` — 平均诊断速度 vs 漂流计 STDD
- `code/analyze_c04.py` — GCM 数据可用性
- `code/analyze_tao.py` — TAO 锚系验证（补充）
- `code/make_outputs.py` — 汇总生成 `results/evidence_table.csv`、`results/metrics.json`
- `results/evidence_table.csv` — 43 条指标证据表（指标名/数值/单位/口径/claim/来源）
- `results/metrics.json` — 机器可读指标（与 evidence 表一致）
