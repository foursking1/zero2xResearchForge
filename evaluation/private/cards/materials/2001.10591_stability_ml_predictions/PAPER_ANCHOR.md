# 论文锚：2001.10591_stability_ml_predictions

> 用途：LLM judge 判分基准（私有）。数值来自 arXiv:2001.10591（npj Computational Materials 6:97, 2020），禁止篡改。

## 锚清单

| # | 指标 | 论文数值 | 出处 | 定义口径 | 容差 |
|---|---|---|---|---|---|
| 1 | 数据集 | 85,014 唯一成分（MP DFT） | Abstract | 成分数 | 精确（冻结数据核验） |
| 2 | 划分 | train 59,509 / val 12,752 / test 12,753 | 仓库 mse_datasets 预划分（论文 60/20/20 近似） | 行数 | 精确 |
| 3 | ΔHf MAE 提升 | 各表示相对 ElFrac 基线降低 27–74% | Figure 2 段 | 回归 MAE（eV/atom） | 方向 |
| 4 | ΔHf 精度 | MAE 与 DFT-vs-实验差 ~0.1–0.2 eV/atom 相当 | 正文 | 回归 MAE | 参照 |
| 5 | ΔHd MAE（六模型） | ElFrac 0.101 / Meredig 0.095 / Magpie 0.092 / AutoMat 0.084 / ElemNet 0.075 / Roost 0.069 eV/atom | 冻结 ml_results.json `stats.Ed.reg.abs.mean`（对应 Figure 3/正文 "~0.10–0.14 除 Roost"） | 全 85,014 预测 vs MP Ed | ±0.01 |
| 6 | 分类指标（Table S2 口径） | 正文：acc<80%、F1<0.75、FPR>0.15；冻结 classifier：ElFrac acc 0.723/F1 0.631/FPR 0.191、Meredig 0.746/0.666/0.180、Magpie 0.759/0.683/0.170、AutoMat 0.792/0.732/0.153、ElemNet 0.744/0.683/0.219 | 正文 + 冻结 classifier JSON `stats.Ed.cl` | ΔHd≤0 二分类 | ±0.03 |
| 7 | 朴素基线 | 60% 化合物不在 hull；全判不稳定 acc=60%；五模型（除 Roost）58–65% | Figure 4 段 | 分类 acc | 参照 |
| 8 | 假阳性率 | 25–38%（ΔHf 训练模型） | Figure 4 段 | FPR | 参照 |
| 9 | 结构模型 CGCNN | ΔHf MAE=34 meV/atom；误差取消弱（ΔHd MAE +26%、F1 −3%）；稀疏空间唯一有效 | Figure 7d 段 | 回归 MAE/方向 | 参照 |
| 10 | Li-Mn-TM-O 案例 | 13,659 候选 / 9 个 MP 稳定 / 预测稳定 507–685（3.7–5.0%）/ 各模型正确 1–2 个 | Table 1 | 候选计数 | 精确 |
| 11 | 误差取消 | ML 模型 ΔHd 误差≈ΔHf 误差（几乎无取消）；Roost 例外（用 ΔHf,rand 时 ΔHd MAE +80%） | 正文/Figure 8 | 方向性 | 方向 |

## 备注
- 主论断：形成能预测准确 ≠ 稳定性预测准确；本卡冻结数据 = 论文同源（mse_datasets 预划分 CSV + TestStabilityML 模型结果）。
- 判分提示：以「Ef MAE 低但稳定性分类差」的方向一致性 + 冻结参考锚区间复现为主判据；绝对数值受实现/特征影响，不强求。
