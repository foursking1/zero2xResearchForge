# Report: 2401.15089_pst_matbench

## 1. 任务与协议

复现 Balasingham et al., *Accelerating Material Property Prediction using Generically Complete Isometry Invariants*, Sci. Rep. 14, 10132 (2024)（arXiv:2401.15089）的核心论断：PDD 等距不变量 + 组成信息在 MatBench 材料属性上的 5 折 CV 回归精度。

本工作采用任务允许的**简化代理模型**：PDD 距离直方图（`average-minimum-distance` 库计算）+ 元素分数组成特征 + LightGBM，固定 seed=42，使用冻结的 MatBench 标准 5 折划分（train/val/test）。

## 2. 数据

- **冻结包**：`F:/dataset/materials/2401.15089_pst_matbench/`（121 文件，~671MB）。
- **校验**：抽查 6 个 parquet 的 SHA-256 与包内 `CHECKSUMS.sha256` 一致（该文件哈希为大写，比对时大小写不敏感）。
- **来源/许可**：MatBench v0.1 标准 5 折划分（Dunn et al., npj Comput. Mater. 6, 138 (2020)）；镜像自 Hugging Face `nimashoghi/matbench_*`；底层为 Materials Project DFT 数据（公开，学术评测用途）。
- **格式**：9 列 `orig_idx, positions, atomic_numbers, natoms, tags, fixed, cell, pbc, y`。`positions` 为笛卡尔坐标（验证：分数坐标逆变换落在 [0,1) 内），`cell[0]` 为 3×3 晶胞矩阵，`y` 为目标。
- **fold0 样本数**：mp_gap train 76,401 / val 8,489 / test 21,223；mp_e_form 95,580 / 10,621 / 26,551；log_gvrh 7,910 / 879 / 2,198。（mp_gap train+val=84,890 即 MatBench 5 折 train 大小。）

## 3. 方法

### 特征
- **PDD 直方图（55 维）**：对每个结构用 `amd.periodicset_from_pymatgen_structure(struct)` + `amd.PDD(pset, k=15)` 得到逐 motif 的 k 近邻距离分布（ndarray：col0 权重，col1..15 距离）；将全部距离按 motif 权重加权，统计 55 bin（1.5–7.0 Å）直方图。此表示保留结构几何，但丢弃逐距离的元素身份。
- **ElFrac 组成（118 维）**：atomic_numbers 的元素分数直方图。

### 模型与训练
- LightGBM 回归：n_estimators=800、lr=0.05、num_leaves=63、n_jobs=2、seed=42；用验证折 early stopping（100 轮）选择迭代数（防泄漏：超参不来自测试集）。
- 每属性 5 折；大训练集每折固定 seed 子采样 max_train=30000（log_gvrh 用全量 7,910）。
- 特征用 ProcessPoolExecutor（8 workers）计算；关键点：分块为 **contiguous 切片**（非 round-robin），保证 `ProcessPoolExecutor.map` 返回顺序与 `y`/`orig_idx` 对齐（已验证：full 集上 comp 与 atomic_numbers、y、orig_idx 完全对齐）。

### 评估
- 指标：MAE（与论文 Table 1 同口径），报告 5 折均值±std。
- 消融：Band Gap 上 Comp-only / PDD-only / 组合三变体（复用同一缓存特征），5 折均值。

## 4. 结果

### 主回归（5 折 CV MAE）

| dataset | 论文 PST | 本工作 | 平凡基线（预测均值） |
|---|---|---|---|
| mp_gap (eV) | 0.210 | **0.5037 ± 0.0037** | 1.328 |
| mp_e_form (eV/atom) | 0.032 | **0.1671 ± 0.0015** | 0.197 |
| log_gvrh (log10(GPa)) | 0.074 | **0.1084 ± 0.0016** | 0.121 |

- 各属性均明显优于平凡基线（尤其 mp_gap：0.504 vs 1.328）。
- mp_gap 与 mp_e_form 的绝对 MAE 比论文 PST 大 2.4× 与 5.2×；log_gvrh 为 1.5×（同量级）。

### Band Gap 消融（5 折均值 MAE，eV）

| 模型 | 论文 Table 3 | 本工作 |
|---|---|---|
| Comp-only | 0.273 | **0.5275** |
| PDD-only | 0.596 | **0.8142** |
| PST-ish（组合） | 0.212 | **0.5156** |

- 排序方向与论文一致：PDD-only 最差、组合最优。
- 组合相对仅组成的提升在本代理中约 2%（0.528→0.516），小于论文的约 22%（0.273→0.212）。

## 5. 结论标签

`partially_supported`

- **PDD 必要性**：方向复现（消融排序一致，PDD-only 显著最差）。
- **绝对精度**：简化代理同一量级但未达论文数值；原因为特征/模型简化而非数据问题。

## 6. 局限

1. **特征简化**：扁平距离直方图丢弃 PDD 逐 motif 的元素身份与集合结构；one-hot 组成弱于 mat2vec 稠密嵌入；GBDT 无注意力/池化。→ 绝对精度与「组合提升幅度」低估。
2. **子采样**：大训练集每折只用 30000 样本（固定 seed）。
3. **轻量调参**：固定 LightGBM 超参，仅 early stopping 由验证折决定；未集成。
4. **对照未复现**：未运行 CrabNet/coGN 对照（任务允许只做 3 属性 + 简化模型）。

## 7. 复现

运行：`python code/pst_matbench.py <data_root> results 30000 8`（data_root 默认 `F:/dataset/materials/2401.15089_pst_matbench`）。产出 `results/evidence_table.csv`、`results/metrics.json`、`results/pred_{dataset}.csv`。
