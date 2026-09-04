# Solution: 2401.15089_pst_matbench

## 结论摘要（判定：部分复现 / partially_supported）

论文核心论断「PDD 等距不变量 + 组成信息 → MatBench 高精度属性预测」在本工作中用**简化 PDD 编码代理模型**（PDD k=15 距离直方图 + 元素分数组成 + LightGBM，5 折 CV）做了独立复算：

- **精度量级**：简化代理在 3 个属性上的 5 折 MAE 为 mp_gap **0.504 ± 0.004 eV**、mp_e_form **0.167 ± 0.002 eV/atom**、log_gvrh **0.108 ± 0.002 log10(GPa)**，均差于论文 PST（0.210 / 0.032 / 0.074），但处于同一数量级（1.4–5 倍内），且全部远优于「预测均值」平凡基线（mp_gap 平凡基线 1.328）。
- **消融方向（PDD 编码必要性）**：**复现**。Band Gap 消融 Comp-only 0.528 / PDD-only 0.814 / PST-ish（组合）0.516——PDD-only 最差、组合最优，与论文 Table 3（PDD-only 0.596 > Comp-only 0.273 > PST 0.212）方向一致。
- **结论标签**：`partially_supported`。方向性（PDD 有用、结构信息必要）由消融复现；绝对精度因代理模型（扁平直方图 + GBDT vs 论文注意力 Transformer + mat2vec）弱于论文，未能量级复现。

## 方法

1. **数据**：冻结 `F:/dataset/materials/2401.15089_pst_matbench/`（121 文件，~671MB；120 个 `matbench_{dataset}_fold{f}_{split}.parquet` + `CHECKSUMS.sha256`）。已抽查 6 个 parquet SHA-256 与 `CHECKSUMS.sha256` 一致。数据为 MatBench v0.1 标准 5 折划分（Dunn et al., npj Comput. Mater. 6, 138 (2020)），镜像自 Hugging Face `nimashoghi/matbench_*`；底层为 Materials Project DFT 数据。
2. **parquet 格式**：9 列 `orig_idx, positions, atomic_numbers, natoms, tags, fixed, cell, pbc, y`。`positions` 为笛卡尔坐标（Å），`cell[0]` 为 3×3 晶胞矩阵，`y` 为目标值。已用「分数坐标逆变换在 [0,1) 内」验证笛卡尔解释正确。
3. **特征**（每结构）：
   - **PDD 直方图**：用 `average-minimum-distance`（amd 1.6.1）`amd.periodicset_from_pymatgen_structure` + `amd.PDD(pset, k=15)` 计算 k 近邻距离分布；将全部 motif 的 15 个近邻距离按 motif 权重加权，统计为 55 bin（1.5–7.0 Å）直方图（55 维）。
   - **ElFrac 组成**：118 维元素分数（atomic_numbers 频数归一化）。
4. **模型**：LightGBM 回归（800 棵树、lr=0.05、num_leaves=63、early stopping 100 轮，early stopping 用验证折选择，固定 seed=42）。5 折与冻结划分一致；大训练集每折子采样最多 max_train=30000（固定 seed）。特征在多进程（8 workers，contiguous 分块保证与 y 对齐）下计算一次并缓存复用。
5. **评估**：MAE（与论文 Table 1 同口径），报告 5 折均值±std；测试集预测写入 `results/pred_{dataset}.csv`。

## 结果

### 数据统计（fold0 划分，train/val/test）

| dataset | train | val | test | 总 |
|---|---|---|---|---|
| mp_gap | 76,401 | 8,489 | 21,223 | 106,113 |
| mp_e_form | 95,580 | 10,621 | 26,551 | 132,752 |
| log_gvrh | 7,910 | 879 | 2,198 | 10,987 |

（注：mp_gap fold0 train+val = 84,890，对应 MatBench 标准 5 折 train 大小 106,113×0.8。）

### 主回归：PDD+ElFrac-LGBM，5 折 CV MAE

| dataset | 论文 PST | 本工作复算 | 偏差 |
|---|---|---|---|
| mp_gap (eV) | 0.210 ± 0.002 | **0.5037 ± 0.0037** | 2.4× |
| mp_e_form (eV/atom) | 0.032 ± 0.0003 | **0.1671 ± 0.0015** | 5.2× |
| log_gvrh (log10(GPa)) | 0.074 ± 0.001 | **0.1084 ± 0.0016** | 1.5× |

逐折数值见 `results/evidence_table.csv`。对照平凡基线（预测均值）：mp_gap 1.328、mp_e_form 0.197、log_gvrh 0.121（后两者由训练集均值预测测试集计算），本工作各属性均明显优于平凡基线。

### Band Gap 消融（5 折均值 MAE，eV）—— PDD 编码必要性

| 模型 | 论文 Table 3 | 本工作复算 |
|---|---|---|
| Comp-only（仅组成） | 0.273 | **0.5275** |
| PDD-only（仅 PDD 直方图） | 0.596 | **0.8142** |
| PST-ish（组成+PDD） | 0.212 | **0.5156** |

方向一致：PDD-only 最差，组合最优；与论文 Table 3 的「PDD 单独使用精度显著下降、组合 PDD+组成最优」方向相符。但组合相对仅组成的提升在本代理中很小（0.528→0.516，~2%），远小于论文（0.273→0.212，~22%）。

## 对论文论断的判定

1. **PST 精度**（Formation 0.032 / Band Gap 0.210 / Shear 0.074）：简化代理给出同一量级但明显偏高的 MAE（0.167 / 0.504 / 0.108），**未定量复现**；差值主要来自特征/模型简化（见局限）。
2. **优于同类 Transformer**：未直接复现（未运行 CrabNet/coGN 对照）；从代理精度看，简化 PDD+GBDT 弱于论文 PST，不足以支持「PST 全面优于 CrabNet」。
3. **PDD 编码有效性**：**方向复现**——PDD-only 最差（0.814 vs Comp-only 0.528），组合最优（0.516），与论文 Table 3 一致。
4. **超参行为**（k/tolerance/权重）：未测试。

## 局限

- **特征简化**：论文 PST 用完整 PDD 集（逐 motif 的元素 + 距离列表）+ mat2vec 稠密嵌入 + 注意力池化；本代理用扁平距离直方图（丢弃元素身份）+ 118 维 one-hot 元素分数 + LightGBM。这解释了绝对 MAE 差距与「组合提升小」。
- **数据子采样**：大训练集（mp_gap/mp_e_form）每折仅用 30000 样本（固定 seed 子采样）控制计算量；log_gvrh 用全量。
- **轻量训练**：LightGBM 未做深度调参（固定超参、仅 early stopping 由验证折决定），未做模型集成。
- 本工作不修改任何冻结数据；全部指标由运行 `code/pst_matbench.py` 得到。

## 文件清单

- `code/pst_matbench.py`：完整可复现脚本（固定 seed，读取冻结 parquet，特征计算→训练→评估→输出）。
- `results/evidence_table.csv`：逐属性逐折 MAE + 消融（含列 `dataset,fold,model,metric,value`）。
- `results/metrics.json`：样本统计、各属性/模型指标、论文锚对照、消融、结论标签。
- `results/pred_{mp_gap,mp_e_form,log_gvrh}.csv`：测试集预测（test_idx, y, pred）。
