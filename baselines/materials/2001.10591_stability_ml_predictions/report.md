# Report: 2001.10591_stability_ml_predictions

## 背景与目标
验证 Bartel et al. (npj Comput. Mater. 6:97, 2020; arXiv:2001.10591) 的核心论断：机器学习形成能预测可达到与 DFT 相当的精度，但组合式模型的稳定性（分解能 ΔHd≤0）预测在分类层面很差——「形成能预测准确 ≠ 稳定性预测准确」。

## 方法

### 数据
冻结包 `F:/dataset/materials/2001.10591_stability_ml_predictions/`：
- `CritExam__{Ef,Ed}_{train,val,test}.csv`：85,014 成分，train/val/test = 59,509/12,752/12,753。
- `Ed_allMP_{6 models}_ml_results.json`：各模型在全 85,014 成分上的 ΔHd 预测与统计。
- `Ed_classifier_{5 models}_ml_results.json`：各分类器在 85,014 成分上的 acc/F1/FPR 等。

### 特征与模型
- 特征：ElFrac = 元素分数向量（118 维），由化学式正则解析计数归一化得到。
- 形成能回归：Ridge（α=1.0）与 LightGBM（500 树、lr=0.05、num_leaves=63、early_stopping 50、seed=42、n_jobs=2）。
- 稳定性分类：同特征 LightGBM 二分类（ΔHd≤0 = 稳定）。
- 评估：固定冻结划分；test set 报告 MAE/RMSE/R²（回归）与 accuracy/F1/FPR/precision/recall/AUC（分类）。

### 冻结参考复算
- ΔHd MAE：直接读取 JSON `stats.Ed.reg.abs.mean`；另按化学式匹配 test CSV 重算 test 集 MAE。
- 分类指标：读取 JSON `stats.Ed.cl['0'].scores`。

## 结果
见 `solution.md` 与 `results/evidence_table.csv`、`results/metrics.json`。要点：
- Ef 回归 test MAE = 0.1495 eV/atom（R²=0.953）——低误差。
- 稳定性分类 test acc=0.760 / F1=0.694 / FPR=0.181——三个指标均不达标（acc<80%、F1<0.75、FPR>0.15）。
- 冻结 6 模型 ΔHd MAE = 0.069–0.101 eV/atom，与论文 0.069–0.101 一致。
- 冻结 5 分类器 acc 0.72–0.79 / F1 0.63–0.73 / FPR 0.15–0.22，与论文一致。

## 结论标签
**supported（复现）**。

## 局限
1. 本工作模型为 ElFrac+LightGBM 简化实现，绝对精度与论文各表示的具体模型存在实现差异，但量级与方向一致。
2. 稳定性预测用分类器路线（TASK.md 允许），未做完整逐空间凸包重建；补充脚本 `hull_check.py` 尝试用训练集凸包 + 预测 Ef 重建 ΔHd，作为进一步佐证。
3. Li-Mn-TM-O 案例与 CGCNN 结构模型不在冻结数据范围，未复算。
4. 设备：CPU（20 核），OMP_NUM_THREADS=2。

## 可复现性
- 固定随机种子 42；划分由冻结 CSV 决定。
- 运行：`OMP_NUM_THREADS=2 python agent_solution/code/analyze_stability.py`。
