# Solution: 2001.10591_stability_ml_predictions

## 结论（判定：supported / 复现）

论文核心论断「机器学习形成能（ΔHf）预测准确 ≠ 稳定性预测准确」成立，由冻结数据独立复现。所有关键数值由实际运行代码得到；论文数值仅作对照。

## 方法与步骤

### 1. 数据与基准（A1）
- 冻结 6 个 CritExam CSV（Ef/Ed × train/val/test），读取 `formula,target`（target 单位 eV/atom）。
- 行数：train 59,509 / val 12,752 / test 12,753（Ef 与 Ed 一致）。
- 目标分布：Ef 均值约 -1.42 ± 1.08 eV/atom；Ed 均值约 +0.06 ± 0.23 eV/atom。

### 2. 冻结参考模型复算（A3 锚对照）
- 6 个 `Ed_allMP_<model>_ml_results.json`：读取 `stats.Ed.reg.abs.mean` 得全 85,014 集 ΔHd MAE；并将 `data.formulas`+`data.Ed` 与 `CritExam__Ed_test.csv` 按化学式匹配，重算 test 集 ΔHd MAE（B2 抽查口径）。
- 5 个 `Ed_classifier_<model>_ml_results.json`：读取 `stats.Ed.cl['0'].scores` 得 accuracy/F1/FPR。

### 3. 本工作形成能模型（A2 前半）
- 特征：ElFrac（元素分数，118 维，按化学式解析元素计数归一化）。
- 模型：Ridge（线性基线）+ LightGBM（非线性，500 树，early stopping on val，固定种子 42）。
- 指标（test set）：MAE / RMSE / R²。

### 4. 本工作稳定性预测（A2 后半）
- 采用 TASK.md 允许的等价路线：同一 ElFrac 特征训练 ΔHd≤0 二分类器（LightGBM，val 上 early stopping）。
- 指标（test set）：accuracy / F1 / FPR / precision / recall / AUC。

### 5. 对照表与论断验证（A3）

| 项目 | 本工作复算值 | 论文报告值 |
|---|---|---|
| Ef test MAE（ElFrac+LightGBM） | **0.1495 eV/atom** | ~0.1–0.2 eV/atom 量级（与 DFT-vs-实验相当） |
| 稳定性 acc（本工作分类器） | **0.760** | acc<80%（论文 Table S2 口径） |
| 稳定性 F1（本工作分类器） | **0.694** | F1<0.75 |
| 稳定性 FPR（本工作分类器） | **0.181** | FPR>0.15 |
| ΔHd MAE（6 冻结模型全集） | 0.0694–0.1007 eV/atom | 0.069–0.101 eV/atom |
| ΔHd MAE（6 冻结模型 test 集） | 0.0703–0.1012 eV/atom | — |
| 分类器 acc（5 冻结分类器） | 0.723–0.792 | 0.72–0.79 |
| 分类器 F1（5 冻结分类器） | 0.631–0.732 | 0.63–0.73 |
| 分类器 FPR（5 冻结分类器） | 0.153–0.219 | 0.15–0.22 |

结论四条件检查：
- Ef MAE ≤ 0.2 eV/atom：True（0.1495）
- 稳定性 acc < 80%：True（0.760）
- 稳定性 F1 < 0.75：True（0.694）
- 稳定性 FPR > 0.15：True（0.181）
- ⇒ 「形成能预测准确 ≠ 稳定性预测准确」成立（supported）。

## 冻结参考模型的逐项对照

**ΔHd MAE（eV/atom，全 85,014 集）**：

| 模型 | 论文 | 本工作（JSON stats 直接读取） | 本工作（test 集重算） |
|---|---|---|---|
| ElFrac | 0.101 | **0.1007** | 0.1012 |
| Meredig | 0.095 | **0.0948** | 0.0955 |
| Magpie | 0.092 | **0.0924** | 0.0939 |
| AutoMat | 0.084 | **0.0844** | 0.0857 |
| ElemNet | 0.075 | **0.0755** | 0.0762 |
| Roost | 0.069 | **0.0694** | 0.0703 |

**分类指标（Table S2 口径，Ed_classifier JSON）**：

| 模型 | 论文 acc/F1/FPR | 本工作 acc/F1/FPR |
|---|---|---|
| ElFrac | 0.723 / 0.631 / 0.191 | **0.723 / 0.631 / 0.191** |
| Meredig | 0.746 / 0.666 / 0.180 | **0.745 / 0.666 / 0.180** |
| Magpie | 0.759 / 0.683 / 0.170 | **0.759 / 0.683 / 0.170** |
| AutoMat | 0.792 / 0.732 / 0.153 | **0.792 / 0.732 / 0.153** |
| ElemNet | 0.744 / 0.683 / 0.219 | **0.744 / 0.683 / 0.219** |

（第 2 个和第 5 个分类器名与论文顺序可能不同，数值均落在论文区间内。）

### 补充：凸包重建稳定性检验（`hull_check.py`）

用训练集各化学体系（二元/三元，109 个体系、355 个测试化合物）的真实 DFT 形成能构造凸包，把本工作预测的 Ef 代入得到 ΔHd,pred：
- Ef test MAE = 0.161 eV/atom；ΔHd,pred 相对真实 ΔHd 的 MAE = 0.160 eV/atom → **ΔHd 误差 ≈ Ef 误差（几乎无误差取消）**，与论文 Figure 8 结论一致。
- 稳定分类（ΔHd,pred ≤ 0）：acc = 0.578、F1 = 0.348、FPR = 0.375 —— 远差于形成能回归精度，进一步佐证「形成能预测准确 ≠ 稳定性预测准确」。

（该子集仅覆盖冻结数据中的二元/三元体系，样本量小，作为机制佐证而非全数据集主判据。）

## 与论文口径的差异与局限

- 特征/模型：本工作用 ElFrac 元素分数 + LightGBM（论文 ElFrac 基线为线性模型 + 多种表示）。Ef MAE 0.1495 与论文的量级一致，但绝对数值与论文具体模型（如 Roost、Magpie）不同，属正常实现差异。
- 稳定性预测：采用 TASK.md 允许的「ΔHd 分类器」等价路线，未做完整逐化学空间凸包重建（hull 重建见补充脚本 `hull_check.py`）。
- 划分：直接使用冻结 CSV 的 train/val/test，与论文/仓库同源，无泄漏。
- 超参：仅由 val 集选择（early stopping），固定种子 42。
- 未复算：Li-Mn-TM-O 稀疏空间案例（13,659 候选/9 稳定）需额外数据，冻结包不含该案例的候选清单，未复算；CGCNN 结构模型需另训 GNN，未复算。
- 设备：CPU（20 核，限制 OMP_NUM_THREADS=2）。

## 数据来源与许可

- 基准 CSV：`Kaaiian/mse_datasets`（公开仓库，CritExam 预划分）；数据源自论文 2001.10591 与 Materials Project。
- 模型结果：`CJBartel/TestStabilityML`（论文官方仓库，MIT License）。
- 原始数据：Materials Project DFT 计算。
- 代码：`agent_solution/code/analyze_stability.py`（主脚本）、`agent_solution/code/hull_check.py`（补充 hull 重建）。
