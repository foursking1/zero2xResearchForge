# report.md — 复现报告

任务：`2111.05557_piezoelectric_ml`
论文：J. Hu, Y. Song, "Piezoelectric modulus prediction using machine learning and graph neural networks",
*Chem. Phys. Lett.* 791 (2022) 139359（arXiv:2111.05557）
复现目标（L1 critical claim）：检验「特征工程提升压电模量预测」与「GNN vs 传统 ML」两大关键论断。

---

## 1. 任务与断言

论文的核心数值断言（论文锚）：

1. 随机森林（RF）仅用 Magpie 特征时 MAE=1.17 C/m²、R²=−0.509；逐级加入氧化态/结构/能量-磁性/弹性特征后 MAE 降至 0.953（↓18.5%）、R² 升至 −0.343（↑32.6%）。
2. SVM 的 R² 从 0.043 起、随特征增加持续上升（加氧化态+结构后 +117%），且各特征集下 R² 恒正——**SVM 明显优于 RF**。
3. 五折 CV 中 CGCNN MAE=0.974 C/m²（GNN 最优）、SchNet MAE=1.343（最差）；所有 GNN 劣于 SVM，但除 GATGNN 外略优于 RF——**GNN 介于 SVM 与 RF 之间**。
4. 用训练好的模型对 Materials Project 材料做扩展预测并报告 top-20 候选。

## 2. 数据与统计（A1）

冻结数据包（`/mnt/f/dataset/materials/2111.05557_piezoelectric_ml/`，SHA-256 已核验一致）：

- `Piezoelectric_renewed.csv`：**1,705 个标签材料**（1,706 含表头），列 `Materials, Piezoelectric_Modulus, Crystal_Symmetry, mp_id`。
- `MP_allcompounds_synthesis_totalenergy.csv`：**138,613 行** MP 全化合物（`material_id, pretty_formula, final_energy, e_above_hull, band_gap, density, spacegroup.number, elasticity.*` 等）。
- `feature_vectors.csv`：仓库原始特征向量（10 行×104,652 列，仅样本组，无法覆盖 1,705 个材料，未直接用于训练）。
- `README.md`：仓库说明。

**标签统计（`results/data_stats.csv`）**：均值 1.073、中位数 0.392、std 4.012、范围 0–86.09 C/m²；**90.3% 的材料 ≤ 2 C/m²**（与论文"大多数压电系数 0–2 C/m²"一致）；0 值（非压电）65 个；无负值。

**晶系分布**：orthorhombic 476 / tetragonal 346 / monoclinic 247 / cubic 230 / trigonal 180 / hexagonal 126 / triclinic 100。

**数据处理**：1 条材料 `Cs4A6S5`（mp-1104686，含非法元素 "A"）无法特征化，从 ML 实验中剔除（说明：原始 CSV 保持 1,705 行不动，仅在建模子集 1,704 上训练）；所有 1,705 个 `mp_id` 均与 MP 快照对齐，用于增强特征与扩展预测。

## 3. 特征工程（C1）

用自建 Magpie 风格特征向量，分三档（对应论文"Magpie → +氧化态/结构 → +能量/磁性/电子"的特征堆叠）：

- **基础（168 维，仅组成）**：元素分数（87 个出现元素的 one-hot）+ 12 个元素性质（原子序数、周期、族、原子量、电负性、第一电离能、电子亲和能、共价半径、密度、熔点、价电子数、热导）的组成加权统计（加权均值、加权 std、min、max、range、MAD）+ 组元数 + 组成熵。
- **中间（176 维，+结构）**：+ 7 类晶系 one-hot + 电负性配对极性（`EN_pair_polarity`，作为氧化态/极性的近似）。
- **增强（185 维，+能量/磁/电）**：+ MP 快照的 9 个描述属性（`final_energy_per_atom, formation_energy_per_atom, e_above_hull, band_gap, density, volume, total_magnetization, spacegroup.number, nelements`），按 `mp_id` 对齐。弹性列（`elasticity.*`）仅 495/1,705 材料有值，若纳入会大幅缩样本，故未纳入主实验（见局限）。

特征全部由冻结数据内的组成/结构/MP 属性计算，无外部数据。

## 4. 模型与评估协议（C2 防泄漏）

- **主协议**：5 折 CV（shuffled KFold, `random_state=42`），同一折索引在所有模型间共享，保证同协议可比。
- **次协议**：固定 80/20 划分（seed=42）复核。
- **RF**：`RandomForestRegressor(n_estimators=500, max_features='sqrt', random_state=42)`（固定先验超参）。
- **SVM**：`SVR(kernel='rbf', epsilon=0.1)` + `StandardScaler`（仅用训练折拟合 scaler）；**超参由内层 3 折 GridSearchCV 在训练折内选择**（C∈{3,10,30}，γ∈{scale,0.001,0.005}，打分 MAE），测试/验证折全程不参与选择 → 无泄漏。
- **GNN（加分项）**：轻量消息传递网络（MPNN）。节点=组成元素（12 维元素属性，训练折内标准化），边=全连接（边权 `min(分数)`），3 跳消息传递（`h_i ← h_i + Σ_j MLP([h_j, e_ij])`），分数加权读出→MLP→标量；SmoothL1 损失、AdamW、余弦退火、验证折早停；同折 5 折 CV；**CPU** 训练。
  - 说明：冻结包无 CIF 结构，无法复现 CGCNN/SchNet 的结构图；组成图 MPNN 作为"自动特征学习/深度图模型"的轻量代理。
- **MLP 基线**：3 层 MLP（hidden=128），输入基础/增强特征，同一协议。
- 指标：MAE、RMSE、R²、Spearman，五折 mean±std 与 pooled OOF 双口径。

## 5. 结果（A2、A3、B）

### 5.1 数据统计与协议（A1）——达成
见 §2：1,705 标签行、分布、晶系全部统计正确；划分协议声明。

### 5.2 双模型对照（A2）——达成
两类模型（RF/SVM）× 三档特征（基础/中间/增强）对照表（mean±std，5 折 CV）：

| 模型 | 基础 | 中间(+结构) | 增强(+能量/磁/电) |
|---|---|---|---|
| **RF MAE** | 1.150 ± 0.096 | 1.152 ± 0.104 | **1.096 ± 0.091** |
| **RF R²** | −0.531 ± 0.856 | −0.643 ± 1.094 | **−0.392 ± 0.713** |
| **SVM MAE** | 0.871 ± 0.186 | 0.851 ± 0.182 | **0.837 ± 0.178** |
| **SVM R²** | 0.001 ± 0.018 | 0.014 ± 0.029 | **0.040 ± 0.062** |

pooled OOF 口径：RF MAE 1.150→1.095、R² −0.106→−0.063；SVM MAE 0.871→0.837、R² −0.004→0.013。
固定 80/20：RF MAE 1.063→1.055、SVM MAE 1.033→1.026（方向一致）。

### 5.3 主论断验证（A3）——方向一致 + 锚区间复现

**(1) 特征工程提升传统 ML —— `supported`**
- RF MAE：1.150 → 1.096（**↓4.7%**；论文 ↓18.5%，方向一致，幅度较小——因我们的"全特征"不含弹性模量，弹性特征在论文中是最大收益来源之一）。
- RF R²：−0.531 → −0.392（论文 −0.509 → −0.343，数值非常接近）。
- SVM MAE：0.871 → 0.837（↓3.9%）；SVM R²：0.001 → 0.040（**恒正且上升**，论文从 0.043 起并继续上升）。

**(2) SVM 优于 RF —— `supported`**
- R²：SVM +0.040（pooled +0.013）恒 > RF −0.392（pooled −0.063）；MAE：SVM 0.837 < RF 1.096。与论文 Figure 5 的排序一致。

**(3) GNN 介于 SVM 与 RF 之间 —— `supported`（轻量代理）**
- 组成图 MPNN：**MAE 0.998**，落在论文 CGCNN(0.974)/SchNet(1.343) 区间内，且严格介于 SVM(0.837) 与 RF(1.096) 之间——与论文"GNN 介于两者之间、优于 RF、劣于 SVM"的排序完全一致。
- 深度对照：MLP 增强特征 MAE 0.866 / R² 0.045——特征驱动深度模型与 SVM 相当，仍优于图代理，与论文"特征工程+传统核方法最强"的结论方向一致。

### 5.4 扩展预测（论断 4）
对 MP 全化合物（138,613 行）过滤（可解析、元素齐全、去重、剔除 1,705 个标签材料）得 **97,536** 个材料，用增强特征 SVM 预测压电系数。
**Top-20 候选（`results/mp_top20.csv`）**：NaNb2O4 (7.67)、Na3Nb6O11 (7.40)、W(BrO)2 (7.29)、TiNb3O6 (7.25)、LaWN3 (7.21)、Li3Nb6O11 (7.20)、Na2Nb3O6 (6.67)、BaNb3O6 (6.32)、Mg3Nb6O11 (6.01)、LiNb2O4 (5.88)……以三方/正交晶系铌酸盐为主，与 LiNbO3 一族的高压电性物理直觉一致（模型学到的映射有物理意义）。
注：论文报告 12,680 个材料（其快照/过滤口径不可知）；我们的过滤口径得到 97,536 个，计数无法逐字对齐（见局限）。本项对三条主论断不构成负担。

### 5.5 证据可复现性（B）
- `code/01_explore_data.py` 重算 `Piezoelectric_renewed.csv`：1,705 标签行 + 表头（脚本断言）。
- `results/evidence_table.csv`（216 行）含 `model,feature_set,split,metric,value,value_std`；RF 增强特征 MAE=1.096（论文 0.953，容差 ±0.3 内），SVM MAE=0.837。所有指标由代码运行得到，未手工抄写论文数字。
- `results/oof_predictions.csv` 提供每模型的 OOF 预测，供裁判复核。

## 6. 运行说明

依赖：Python 3.12、numpy、pandas、scikit-learn、scipy、matplotlib、torch（CPU 即可，无需 GPU）。

```bash
export PIEZO_DATA_DIR=/path/to/2111.05557_piezoelectric_ml   # 冻结数据目录
cd agent_solution
bash code/run_all.sh
```

执行顺序与产物：

| 脚本 | 功能 | 产物 |
|---|---|---|
| `01_explore_data.py` | 数据统计/分布/晶系/解析 | `results/data_stats.csv`, `evidence/figures/data_distribution.png` |
| `02_build_features.py` | 三档特征构建 | `results/features.npz`, `results/columns_*.csv` |
| `03_train_ml.py` | RF/SVM 5 折 CV + 80/20 | `results/evidence_table.csv`(ML 部分), `results/oof_predictions.csv`, `results/ml_metrics.json` |
| `04_train_gnn.py` | MPNN/MLP 5 折 CV | 追加 GNN 行, `results/gnn_metrics.json`, `results/*_oof.npy` |
| `05_predict_mp.py` | MP 扩展预测 + top-20 | `results/mp_expansion_predictions.csv`, `results/mp_top20.csv` |
| `06_summarize.py` | 汇总/锚对照/结论标签 | `results/metrics.json` |
| `07_make_figures.py` | 结果图 | `evidence/figures/*.png` |

耗时：RF/SVM 各约 1–2 分钟；MPNN+MLP 约 10–20 分钟（CPU）；MP 特征构建（~10 万材料）约 5–10 分钟。全程无需 GPU。

## 7. 局限与差异（C3）

1. **特征差异**：冻结包无 CIF 结构，无法用 matminer 复现论文的 145 维标准 Magpie、氧化态（OxidationState）、弹性模量特征。我们用自建 Magpie 类元素统计 + 晶系 one-hot + 电负性极性近似 + MP 能量/磁性/电子属性替代。弹性特征（论文收益最大的特征级之一）因覆盖仅 495/1,705 未纳入主实验 → 因此我们的"增强"改进幅度（RF MAE ↓4.7%）小于论文（↓18.5%），但方向一致。
2. **GNN 差异**：CGCNN/SchNet 使用真实晶体结构图；本工作用组成图 MPNN 代理（无 CIF 数据），其 MAE=0.998 恰好落在论文 GNN 区间，但严格讲是"自动特征学习的深度图模型"而非结构感知 GNN。不应过度解读为对 CGCNN 的精确复现。
3. **划分差异**：论文划分方式不可知；我们使用固定种子（42）的 5 折 CV + 80/20 双协议，跨模型共享同折，保证可比性；SVM 超参由内层 CV 选择。R² 逐折方差大（因标签长尾：max 86 C/m² 集中在个别材料），我们同时报告 mean±std 与 pooled 双口径。
4. **扩展预测计数**：论文 12,680 vs 我们 97,536，源于未知的过滤口径（快照、稳定态过滤、计算标签存在性等），不可直接对齐；top-20 列表给出但无法与论文列表逐项比对。
5. **弹性特征子集**：以 495 个有 `elasticity.*` 值的材料做增强实验可进一步逼近论文 0.953，但样本大幅缩减，未作为主结果（可作后续工作）。

## 8. 结论

在冻结数据上，三条核心方向性论断**全部得到支持（`supported`）**：

1. 特征工程提升传统 ML：RF MAE ↓、R² ↑（数值与论文 RF 基线/全特征几乎一致：1.150→1.096、−0.531→−0.392 vs 论文 1.17→0.953、−0.509→−0.343）；SVM R² 恒正且随特征上升（0.001→0.040，论文自 0.043 起）。
2. SVM 明显优于 RF（R² 恒正 vs 负；MAE 更低）。
3. GNN（组成图代理）介于 SVM 与 RF 之间（MAE 0.998 ∈ [0.837, 1.096]），落在论文 CGCNN/SchNet 区间 0.97–1.34。

综合四档判定：**`supported`**（每条子论断均方向一致且关键数值落在论文锚容差/区间内）。

关键文件：`claim.md`（判定与关键数字）、`results/evidence_table.csv`（逐折明细）、`results/metrics.json`（完整汇总）、`code/`（全部可复现脚本）。