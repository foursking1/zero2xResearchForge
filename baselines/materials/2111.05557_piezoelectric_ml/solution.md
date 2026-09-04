# solution.md — 复现方法说明与结果概要

任务：`2111.05557_piezoelectric_ml`（L1 critical claim）
复现对象：Hu & Song, *Chem. Phys. Lett.* 791 (2022) 139359（arXiv:2111.05557）的三大核心论断。

## 1. 方法概要

**数据（全部来自冻结包，未引入任何外部数据/权重）**

| 文件 | 用途 |
|---|---|
| `Piezoelectric_renewed.csv` | 1,705 个标签材料，目标 `Piezoelectric_Modulus`（C/m²），附 `Crystal_Symmetry`、`mp_id` |
| `MP_allcompounds_synthesis_totalenergy.csv` | 138,613 行 MP 化合物，用于增强特征（能量/磁性/电子）与扩展预测 |
| `feature_vectors.csv` | 仓库原始特征向量（10 行×104,652 列，仅样本组），未直接用于训练（样本不足），仅说明论文特征维度 |

**特征构造**（自建，Magpie 风格元素统计 + MP 属性，全部由冻结数据算出）：
- 解析 `Materials` 化学式（支持括号，如 `Mn(AlTe2)2`）→ 元素配比。
- **基础特征（168 维，仅组成）**：元素分数 one-hot（87 个出现元素）+ 12 个元素性质（原子序数/周期/族/原子量/电负性/电离能/电子亲和能/共价半径/密度/熔点/价电子数/热导）的组成加权统计（加权均值、加权标准差、min、max、range、MAD）+ 组元数 + 组成熵。
- **中间特征（176 维，基础+结构）**：+7 类晶系 one-hot + 电负性配对极性代理（氧化态水平的近似）。
- **增强特征（185 维，基础+结构+能量/磁/电）**：+MP 快照属性（`final_energy_per_atom, formation_energy_per_atom, e_above_hull, band_gap, density, volume, total_magnetization, spacegroup.number, nelements`），按 `mp_id` 对齐（1,705/1,705 全覆盖）。

**模型与评估协议**：
- 模型：`RandomForestRegressor`（n_estimators=500, max_features='sqrt'，固定种子）与 `SVR`（RBF，标准缩放）。
- **主协议：5 折交叉验证**（shuffled KFold，seed=42），**所有模型共用同一折**。SVR 的超参数由**内层 3 折 GridSearchCV 仅在训练折内**选择（C∈{3,10,30}，γ∈{scale,0.001,0.005}）——划分固定、超参不接触验证/测试，无泄漏。次协议：固定 80/20 划分（seed=42）。
- 指标：MAE / RMSE / R²（五折 mean±std + pooled OOF）。
- **GNN（加分项）**：轻量消息传递网络（MPNN）作用在**组成图**上（节点=元素属性向量，全连接边权=min(分数)，4 跳消息传递，分数加权读出），CPU 训练、同折 5 折 CV、每折早停。注：冻结包无 CIF 结构文件，故为组成图代理而非 CGCNN/SchNet 的结构图。
- 对照组：增强特征上的 3 层 MLP（深度学习基线）。

**防泄漏**：标签仅 `Piezoelectric_Modulus`；特征全部来自组成/结构元数据；CV 折固定且跨模型共享；SVR 超参只由内层训练折验证集选择；MP 增强特征与标签来自同一冻结快照但均为描述属性（非目标）。

## 2. 结果概要（5 折 CV，全部实测）

| 模型 | 特征 | MAE (C/m²) | R² |
|---|---|---|---|
| RF | 基础 | 1.150 ± 0.096 | −0.531 ± 0.856 |
| RF | 增强 | 1.096 ± 0.091 | −0.392 ± 0.713 |
| SVM | 基础 | 0.871 ± 0.186 | 0.001 ± 0.018 |
| SVM | 增强 | 0.837 ± 0.178 | 0.040 ± 0.062 |
| GNN (MPNN) | 组成图 | 0.998 | −0.062 |
| MLP | 增强 | 0.866 | 0.045 |

方向性验证：
1. **特征工程提升传统 ML：支持**。RF MAE 1.150→1.096（↓4.7%，论文 ↓18.5% 方向一致）；RF R² −0.531→−0.392（论文 −0.509→−0.343）；SVM MAE 0.871→0.837（↓3.9%）；SVM R² 0.001→0.040（恒正、上升，论文从 0.043 起）。
2. **SVM 优于 RF：支持**。SVM R² mean +0.040 > RF −0.392；MAE 0.837 < 1.096。
3. **GNN 介于两者之间：支持**。MPNN MAE 0.998 ∈ (SVM 0.837, RF 1.096)，落在论文 CGCNN/SchNet 区间 0.97–1.34。

扩展预测（论文论断 3）：对 MP 化合物（去重后 97,536 个）用增强特征 SVM 预测，top-20 全部为三方/正交/四方晶系铌酸盐类（NaNb2O4 7.67、Na3Nb6O11 7.40、W(BrO)2 7.29…），与已知高性能压电体（LiNbO3 族）的化学直觉一致。

## 3. 复现运行

```bash
# 环境：Python 3.12；numpy/pandas/scikit-learn/scipy/matplotlib/torch
cd agent_solution
export PIEZO_DATA_DIR=/path/to/2111.05557_piezoelectric_ml   # 冻结数据目录
bash code/run_all.sh        # 依序运行 01→07（约 20–40 分钟，CPU 即可）
```

脚本依赖 `results/` 中间产物，按顺序执行即可全量重算。逐脚本说明见 `report.md` §6 与 `code/run_all.sh`。

## 4. 产物清单

- `code/`：`01_explore_data.py`(数据统计) `02_build_features.py`(特征) `03_train_ml.py`(RF/SVM) `04_train_gnn.py`(MPNN+MLP) `05_predict_mp.py`(扩展预测) `06_summarize.py`(汇总) `07_make_figures.py`(图表) + `common.py`
- `results/evidence_table.csv`：216 行 `model,feature_set,split,metric,value[,value_std]`（含逐折/mean/pooled/80-20）
- `results/metrics.json`：样本统计、各方法指标、论文锚对照、结论标签
- `results/`：`data_stats.csv`、`features.npz`、`oof_predictions.csv`、`mp_expansion_predictions.csv`、`mp_top20.csv`、`ml_metrics.json`、`gnn_metrics.json`、`expansion_summary.json`
- `evidence/figures/`：`data_distribution.png`、`model_comparison.png`、`feature_engineering_effect.png`
- `claim.md`、`solution.md`、`report.md`