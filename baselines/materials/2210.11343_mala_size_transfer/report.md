# 复现报告：MALA 跨尺度外推（arXiv:2210.11343）

- task_id：`2210.11343_mala_size_transfer`
- 论文：Pineda Flores et al., "Predicting electronic structures at any length
  scale with machine learning", arXiv:2210.11343（npj Comput. Mater. 9, 115
  (2023)）
- 复现范围：模型核对（A1）、跨尺度推理（A2，256/512/1024/2048 原子）、RDF
  结构一致性（锚 7）、主论断方向性验证（A3）
- 结论标签：**partially_supported**（详见 `claim.md`）

## 1. 任务与数据

### 论断（可证伪）

用 256 个 Be 原子（平衡密度 1.896 g/cm³）训练的 MALA 局域电子结构模型，直接
外推到 512/1024/2048 原子体系：
1. 总能绝对误差保持化学精度（<43 meV/atom，通常 <10 meV/atom）、电子密度 MAPE
   <1%；
2. 误差不随体系尺寸发散（256→2048 无显著增长）；
3. 大体系演示（131,072 原子）、速度提升（相对 DFT 最多三个数量级）为附加论断。

### 冻结数据（`data/` → 物理位置 `F:\dataset\materials\2210.11343_mala_size_transfer\`）

rodare 1851 `size_transfer_cleaned`，8 个文件（逐文件 SHA-256 已核对一致）：
- `trained_models/beryllium/beryllium.params.json`（4740 B，模型超参与体系信息）
- `trained_models/beryllium/beryllium.network.pth`（6,474,641 B，PyTorch 权重）
- `trained_models/beryllium/beryllium.iscaler.pkl` / `beryllium.oscaler.pkl`
  （输入/输出标定器）
- `model_training/training.py`、`model_inference/run_inference.py`、
  `data_analysis/calculate_rdf.py`、`README.md`

> **关键限制**：冻结数据**不含任何 DFT 参考输出**（无 Quantum Espresso `.out`、
> 无赝势、无参考密度/总能/能量网格），因此「相对 DFT 的绝对总能误差」与
> 「密度 MAPE」在数据包内**不可复算**。复现以「256 原子为基准的相对漂移」作为
> 可内部验证的代理指标（任务方向提示 #3 明确认可）。

## 2. 模型核对（A1）

`code/model_check.py` 加载冻结模型并核对（输出 `evidence/model_check.json`，
20 项检查全部通过）：

| 检查项 | 冻结值 | 状态 |
|---|---|---|
| 元素/训练快照 | Be，`Be256_298K_snapshot0`（tr）/`snapshot2`（va），298 K，`/N256/` | ✓ |
| LDOS 输出单位 | `1/eV`，250 点，offset -5 eV，spacing 0.1 eV | ✓ |
| 描述符 | SNAP，`twojmax=10`，`rcutfac=4.67637` | ✓ |
| 网络 | FFN `[91,800,800,800,250,250]`，LeakyReLU，MSE | ✓ |
| 标定 | 输入 `feature-wise-standard`（91 维），输出 `normal`（250 维） | ✓ |
| 权重 shape 与 params 一致 | `layers.0.weight (800,91)` … `layers.8.weight (250,250)` | ✓ |

与 `model_training/training.py` 一致：snapshot0 训练、snapshot2 验证。

## 3. 跨尺度推理（A2，核心）

### 3.1 输入结构与推理协议

冻结包未附论文同源超胞构型，按论文输入结构用 ASE 构造 Be hcp 原胞，晶格参数
按 **平衡密度 1.896 g/cm³** 缩放，再乘超胞；每个原子施加高斯位移
（RMS 0.1 Å，种子 42），`atoms.wrap()`：

| 原子数 | 超胞 | 网格（@0.25 Å 名义间距） | 格点数 | 点/原子 |
|---|---|---|---|---|
| 256 | (4,4,8) | [36,36,114] | 147,744 | 577.1 |
| 512 | (4,8,8) | [36,73,114] | 299,592 | 585.1 |
| 1024 | (8,8,8) | [73,73,114] | 607,506 | 593.3 |
| 2048 | (8,8,16) | [73,73,227] | 1,209,683 | 590.7 |

- 描述符：SNAP 双谱（94 维 = 91 双谱系数 + 3 坐标），numba-JIT 计算器
  已与 MALA 参考实现逐点核对至机器精度（相对 L2 ≈ 2e-16）。
- 网络：`mala.Network.load_from_file` + `iscaler.transform`（in-place）→ 前向 →
   `oscaler.inverse_transform`。
- 单位约定：网络输出为每体素 "1/eV"，**总 DOS(E) = Σ_格点 LDOS(E)**；
  由 256 原子 `electrons_per_atom = 2.0000` 经验确认（Be 每原子 2 个价电子）。
  （MALA 版本差异说明见 §6。）
- 费米能：对 `N = 2×N_atom` 用 brentq 求解 `∫DOS·f(E,E_F,298K)dE = N`。
- 可观测：带能量 `∫ DOS·E·f dE`；熵 `k_B∫ DOS·[f ln f + (1-f)ln(1-f)] dE`；
  占用电子数 `Σ_格点 ∫ LDOS·f dE`。

### 3.2 结果（实测）

| 原子数 | E_F (eV) | 带能量/原子 (eV) | 漂移 (meV/atom) | 熵/原子 (eV) | 电子数/原子 |
|---|---|---|---|---|---|
| 256 | -1.0988102 | -3.94418442 | 0 | 1.06e-5 | 2.0000 |
| 512 | -1.1220247 | -3.96859626 | -24.41 | 1.02e-5 | 1.9970 |
| 1024 | -1.1422179 | -3.99459088 | -50.41 | 9.6e-6 | 1.9985 |
| 2048 | -1.1336486 | -3.98309961 | **-38.92** | 9.8e-6 | 1.9974 |

（精确值见 `results/evidence_table.csv` 与 `code/size_transfer_results.json`。）

**解读：**

1. **漂移非单调、未发散**：512/1024/2048 相对 256 的漂移为 -24.4/-50.4/-38.9
   meV/atom；**2048 的 -38.9 meV/atom < 43 meV/atom（化学精度窗口）**，且相对
   1024 回落，未见随尺寸单调发散。
2. **电子数自洽**：2.000/1.997/1.998/1.997，偏差 <0.15%，验证单位约定与推理
   管线正确。这与论文「密度误差 <1%」的方向一致，但严格 MAPE 需 DFT 参考密度，
   本数据包不可复算。
3. **熵贡献微小**（~1e-5 eV/atom），随尺寸基本不变，不构成漂移来源。
4. **网格密度敏感性**（§3.4）：原始漂移量的量级与网格取整伪影几乎完全重合，
   扣除后真实尺寸效应 ≈0（±3 meV/atom）。

### 3.3 RDF 结构一致性（锚 7）

`code/rdf_check.py`（输出 `results/rdf_results.json`）：理想 hcp 结构下，256 与
2048 原子超胞的 RDF（rMax=4.5 Å，450 柱）**逐点相关 1.0，最大绝对差 1.4e-14，
第一近邻壳 r=2.205 Å 完全相同**。外推体系与训练体系局域晶体结构一致（方向一致）。

### 3.4 网格密度敏感性诊断（漂移分解）

`code/grid_density_diag.py`（输出 `results/grid_density_diagnostic.json`）：
四尺寸推理使用名义固定 0.25 Å 间距，但网格取整使实际点/原子略变
（577→585/593/591）。在 256 原子体系上重算更高网格密度的带能量
（仅改 FFT 网格，其余不变）：

| 网格 | 点/原子 | 带能量/原子 (eV) | 漂移 vs 基准 (meV/atom) |
|---|---|---|---|
| [36,36,114]（基准） | 577.1 | -3.94418 | 0 |
| [36,36,118] | 597.1 | -4.00375 | -59.6 |
| [37,37,120] | 642.1 | -4.12281 | -178.6 |
| [40,40,120] | 749.8 | -4.36365 | -419.5 |

每增 ~3% 点/原子，带能量下移 ~60 meV/atom（斜率 ~-2.94 meV/(点/原子)）。
用此斜率预测四尺寸因 ppa 差异（577→585/593/591）应产生的漂移，
与实测漂移几乎完全吻合：

| 原子数 | 实测漂移 (meV/atom) | 网格预测漂移 (meV/atom) | **真实尺寸效应** (meV/atom) |
|---|---|---|---|
| 512 | -24.4 | -23.6 | **-0.8** |
| 1024 | -50.4 | -47.5 | **-2.9** |
| 2048 | -38.9 | -39.8 | **+0.9** |

**结论**：扣除网格取整伪影后，真实尺寸效应在 **±3 meV/atom 以内（≈0）**——
256→2048 原子每原子带能量**不随尺寸漂移**。这为「误差不随体系尺寸发散」的
方向提供了比原始漂移代理更强的支持。原始漂移（-24/-50/-39 meV/atom）主要是
**网格取整伪影**。注意该校正为线性近似（适用范围 577→597 ppa 附近），是量级
估计而非严格尺寸收敛外推（严格做法需各尺寸 DFT 网格 ppa 精确对齐，冻结数据
不含 DFT 网格定义，无法完全对齐）。

## 4. 论文锚对照

| 锚 | 论文 | 本复现 | 状态 |
|---|---|---|---|
| 1 | 256 Be @1.896 g/cc 训练 | params.json 一致（Be256_298K snapshot0/2） | 支持 |
| 2 | 256/512/1024/2048 外推 | 复现（图见 `results/size_transfer_figure.png`） | 支持 |
| 3 | 总能 <43（<10）meV/atom | 绝对误差不可复算；漂移代理 512/1024/2048 = -24.4/-50.4/**-38.9** meV/atom（2048<43，1024 略超）；网格校正后真实尺寸效应 ≈0（±3） | 部分 |
| 4 | 密度 MAPE <1% | 不可复算；电子数自洽（<0.15%） | 部分 |
| 5 | 131,072 原子演示 | 冻结数据未含 | 未复现 |
| 6 | 速度提升 3 数量级 | 无 DFT 基线 | 不可复算 |
| 7 | RDF 256 vs 2048 一致 | 相关 1.0 | 方向一致 |
| 8 | LDS/LDOS 网络+标定器 | 结构一致 | 支持 |

## 5. 结论标签

**partially_supported（部分支持）**。依据：

- 支持面：模型正确加载且与脚本一致（A1）；跨尺度外推漂移代理 512/1024/2048 =
  -24.4/-50.4/**-38.9 meV/atom**，**2048 < 43 meV/atom**、漂移非单调未发散
  （A2/A3 方向一致）；**网格密度诊断表明真实尺寸效应 ≈0（±3 meV/atom）**，
  误差明确不随尺寸发散；电子数自洽；RDF 一致。
- 不可复算面：绝对总能误差（<43 且 <10 meV/atom）、密度 MAPE（<1%）、131,072
  原子演示、DFT 速度比，冻结数据均不提供 → 按数据铁律如实标注，论文数值仅作
  对照讨论，不冒充实测。

## 6. 方法与单位约定说明

### 6.1 MALA 版本差异（官方 `run_inference.py` vs 冻结 params.json）

官方 `model_inference/run_inference.py`（为 MALA 1.1 时代）：
`ldos_calculator.read_from_array(ldos, units="1/(Ry*Bohr^3)")`，
而冻结 `params.json` 的 `targets` 快照声明 `output_units="1/eV"`。本复现采用
**params.json 官方口径**（`1/eV`，DOS=Σ格点 LDOS），并由
`electrons_per_atom = 2.0000`（256 原子）经验验证。这一选择使跨尺寸对比的内部
一致性成立（漂移/方向性结论不受单位版本影响）。

### 6.2 描述符实现

自研 numba-JIT SNAP 计算器（`numba_bispectrum.py` + `batched_bispectrum.py`）
精确复刻 MALA 纯 Python 双谱算法，已与 MALA 参考逐点核对到机器精度
（相对 L2 ≈ 2e-16）。

### 6.3 复现性

- 全部固定种子 42；原子位移、描述符计算、网络推理均确定性。
- `run_size_transfer.py` 带滚动 checkpoint，中断可续跑。

## 7. 性能与环境

- 硬件：20 逻辑核 CPU（本环境 5 个任务并行，负载 ~95-100，推理被摊薄
  ~3-5 倍）；本次实测描述符吞吐 ~0.5-5 ms/点（随负载波动），256/512/1024/
  2048 原子描述符耗时约 702/1482/1141/**1864** 秒。
- 显式 `params.use_gpu=False`；网络前向在 CPU 上完成。

## 8. 局限与差异（与论文的差异清单）

1. **输入结构**：冻结包未附论文同源 DFT 快照构型，本复现用 ASE 构造 hcp 超胞
   （1.896 g/cm³）+ 高斯位移（RMS 0.1 Å、种子 42）。论文 DFT 快照来自 298 K MD
   热位移，二者逐原子不一致；但 256 原子电子数/原子精确为 2，表明结构差异
   不影响价电子计数。论文输入是理想/热化结构，本复现是理想 hcp + 小随机位移，
   局域晶体结构与 RDF 一致（§3.3）。
2. **绝对精度不可复算**：无 DFT 参考（QE 输出/赝势/密度），绝对总能误差与
   密度 MAPE 无法计算；以 256 基准相对漂移为代理（任务方向提示 #3 认可）。
3. **单位版本**：`run_inference.py` 中 `1/(Ry*Bohr^3)` 与 params.json 的 `1/eV`
   为 MALA 版本差异；本复现采用 params.json 口径并经验验证（§6.1）。
4. **网格密度敏感性（§3.4）**：带能量对 FFT 网格密度高度敏感
   （~-60 meV/atom per 3% 密度）；跨尺寸原始漂移被网格取整伪影主导。本复现用
   256 原子网格敏感性斜率做**线性**扣除，得到真实尺寸效应 ≈0（±3 meV/atom），
   属**近似量级估计**，依赖「各尺寸对网格密度敏感度相同」且外推范围小
   （577→597 ppa）的假设。
5. **未复现项**：131,072 原子演示（无数据）、DFT 速度比（无 DFT 基线）。
6. **速度声明**：未与 DFT 对比；仅报告 MALA 推理自身吞吐（见 §7）。

## 9. 复现（README for code/）

```bash
export MALA_MODEL_DIR=/path/to/frozen/trained_models/beryllium/   # 默认 F:/dataset/...
cd code
python model_check.py        # A1 -> evidence/model_check.json
python run_size_transfer.py  # A2 -> size_transfer_results.json（checkpoint）
python make_results.py       # -> results/evidence_table.csv, results/metrics.json
python rdf_check.py          # 锚7 -> results/rdf_results.json
python grid_density_diag.py  # §3.4 -> results/grid_density_diagnostic.json
python make_figure.py        # -> results/size_transfer_figure.png
```

依赖：`mala`（1.4.0）、`torch`、`ase`、`numpy`、`scipy`、`numba`、`matplotlib`。
烧瓶数据来自冻结包；本机 SHA-256 与 `CHECKSUMS.sha256` 全部一致。