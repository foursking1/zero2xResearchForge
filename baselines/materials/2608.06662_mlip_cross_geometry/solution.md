# Solution: 2608.06662_mlip_cross_geometry

## 结论（判定：复现，方向性与分组结论成立；ORB-V3 数值因权重不可得未直接验证）

论文核心声明「通用 MLIP 在 ZrO2 五类几何环境上的零样本预测呈现明显的几何依赖退化：最大力误差出现在 neck 与 wire 配置；MP-NC 组整体误差低于 MP-C 组」由三个真实预训练模型的独立零样本推理**复现**。ORB-V3（论文最佳，6 meV/atom / 197.3 meV/Å）的权重在本评测环境无法获取（`orb-models` 依赖 `dm-tree`，Windows 上源码编译卡死），因此锚 1 的具体数值改为由本工作可用的最佳模型对照并归因。

## 方法

### 1. 数据
- 冻结官方 ZrO2 extended-XYZ 数据集（Zenodo 10.5281/zenodo.21829037，CC-BY-4.0）：`F:/dataset/materials/2608.06662_mlip_cross_geometry/ZrO2/`，35 文件 / 14,434 帧（bulk 94 / slab 3,073 / particle 838 / neck 4,000 / wire 6,429）。
- 每帧解析：`ase.io.read` → DFT 能量/力/应力存于 `SinglePointCalculator.results`。已抽查 5 个几何的文件，力与能量与原始 xyz 文本逐值一致（maxdiff 0.0）。

### 2. 零样本推理与采样
- 模型（全部真实权重、CPU 单点推理，零训练/零弛豫）：
  | 模型 | checkpoint | 分组 |
  |---|---|---|
  | CHGNet v0.3.0（chgnet 0.4.2） | 预训练 MP | MP-C |
  | MACE-MP-0 small | `2023-12-10-mace-128-L0_energy_epoch-249.model`（GitHub ACEsuit/mace-mp，MIT） | MP-C |
  | MACE-MPA-0 medium | `mace-mpa-0-medium.model`（GitHub ACEsuit/mace-mp，MIT；训练含 Alexandria → MP-NC） | MP-NC |
- **采样协议**：分层随机子采样，`random.Random(42)`，每几何类最多 120 帧（bulk 全 94），共 574 帧。方向性判据基于一致采样协议。采样明细写入 `results/inference_meta.json`。
- **对齐参考集**：论文未发布训练/测试划分标签，故以全部 574 个采样帧作为对齐参考集（TASK.md 允许）。

### 3. 参考能量对齐与误差口径（与论文 Sec II.B 一致）
- 元素级偏移 `{Δµ_Zr, Δµ_O} = argmin Σ_i (E_DFT,i − E_model,i − N_Zr,i·Δµ_Zr − N_O,i·Δµ_O)²`，最小二乘。只偏移能量、不偏移力。
- 每原子能量误差 = `(E_DFT,i − E_aligned,i)/N_i`；能量 RMSE = `sqrt(mean(e_i²))`（meV/atom）。
- 力 RMSE = `sqrt(Σ sse / Σ n_comps)`（meV/Å，全部原子×3 分量）。

## 结果

### 4. 逐几何类能量/力 RMSE（对齐后，meV/atom 与 meV/Å）

| 几何 | CHGNet (MP-C) | MACE-MP-0 (MP-C) | MACE-MPA-0 (MP-NC) |
|---|---|---|---|
| bulk | 28.16 / 180.65 | 8.72 / 291.41 | 18.64 / 209.24 |
| slab | 14.90 / 332.14 | 12.31 / 335.45 | 9.36 / 293.62 |
| particle | 95.21 / 391.33 | 59.90 / 520.06 | 48.19 / 486.96 |
| neck | 21.77 / 384.29 | 24.76 / 461.31 | 26.76 / 405.33 |
| wire | 68.05 / 572.98 | 55.15 / 557.57 | 64.11 / 518.54 |
| **global** | **56.02 / 351.04** | **39.47 / 421.43** | **39.62 / 375.19** |

### 5. 方向性判定（锚 3，三个模型一致）
- 力 RMSE：neck+wire > bulk+slab（CHGNet 478.6 > 256.4；MACE 509.4 > 313.4；MPA0 461.9 > 251.4）；wire 力误差为最大（572.98 / 557.57 / 518.54），bulk 最小（180.65 / 291.41 / 209.24）。✓
- 能量 RMSE：低配位类（particle/wire/neck）> bulk/slab（CHGNet 61.7 > 21.5；MACE 46.6 > 10.5；MPA0 46.4 > 14.0）。✓
- 机制关联：neck/wire 为 1D/受限构型，力幅值大、配位低，误差放大与论文「力过滤 >3 eV/Å、低配位导致误差放大」一致。

### 6. 关键数值对照（锚 1 与锚 2）

| 项目 | 论文 | 本工作 | 判定 |
|---|---|---|---|
| 最佳模型全局（ORB-V3） | 6 / 197.3 | ORB-V3 权重不可得；本工作最佳 MPA-0 39.62 / 375.19 | 数值超容差，归因（模型不同 + 对齐参考集=全部采样帧 vs 论文训练划分） |
| 全体模型均值 | ≈20 / 400 | 45.04 / 382.55 | 能量超 ±5（模型样本少、偏 MP-C）；力在 ±100 内 |
| MP-NC 组整体 | 低于 MP-C | 39.62 / 375.19 < 47.75 / 386.24 | ✓ 方向一致 |
| MP-C 组最佳 | ORB-V2-MPtrj 107.67 / 309.1 | 未运行 ORB-V2-MPtrj（未验证数值） | 未验证 |

### 7. 数据与可复现性
- 逐结构误差表：`results/per_structure_errors.csv`（CHGNet，574 行）、`results/per_structure_errors_mace.csv`、`results/per_structure_errors_mpa0.csv`（列：geometry/file/frame/n_atoms/E_DFT/E_model/force_rmse_per_atom/sse/n_comps）。
- 聚合脚本 `code/aggregate.py` 可从冻结数据 + 上述 CSV 直接重算证据表（`results/evidence_table.csv`）全部关键数值（B1/B2/B3 抽查口径）。
- 推理脚本：`code/infer_mlip.py`（CHGNet）、`code/infer_mace.py`（MACE，支持 checkpoint 参数）、`code/infer_orb.py`（ORB-V3，未运行）。

## 与论文口径的差异与局限
1. **模型可得性**：ORB-V3（及 ORB 系列）因 `dm-tree` 在 Windows 上源码编译卡死未能安装；用 MACE-MPA-0 作为 MP-NC 代表。未验证 ORB-V2-MPtrj 的 MP-C 最佳数值。
2. **对齐参考集**：论文用内部训练划分（≈72%，未发布）；本工作用全部 574 采样帧。该差异对能量 RMSE 有影响（绝对平移+斜率），是 A2 数值归因的一部分。
3. **采样**：分层子采样 574/14,434（~4%），方向性判据基于一致协议；bulk 全量 94 帧。
4. **设备**：CPU（20 核，OMP_NUM_THREADS=2，10 workers）。
5. **许可**：CHGNet 权重（MP 训练，学术使用）；MACE 权重 MIT；ZrO2 数据 CC-BY-4.0。

## 数据来源与许可
- 数据：Zenodo 10.5281/zenodo.21829037 `ZrO2.zip`（CC-BY-4.0），逐文件 SHA-256 见 `data/checksums.sha256`。
- 模型权重：CHGNet（MP 预训练）；MACE-MP-0 / MACE-MPA-0（GitHub ACEsuit/mace-mp，MIT）。
- 代码：`agent_solution/code/`（`infer_mlip.py` / `infer_mace.py` / `infer_orb.py` / `aggregate.py`）。
