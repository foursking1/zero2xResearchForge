# 科研任务：检验「机器学习形成能预测准确 ≠ 稳定性预测准确」关键论断（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2001.10591_stability_ml_predictions`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Bartel et al., "A critical examination of compound stability predictions from machine-learned formation energies", npj Computational Materials 6:97 (2020)（arXiv:2001.10591）
- 领域：materials / 材料信息学 / 形成能与稳定性预测

## 问题（可证伪）

论文核心论断：**机器学习形成能（ΔHf）预测虽可达到与 DFT 相当的准确度，但所有组合式（compositional）模型在稳定性预测上表现很差——「形成能预测准确 ≠ 稳定性预测准确」**。基于 Materials Project（MP）85,014 个唯一成分：
1. 六个组合式模型（ElFrac 基线、Meredig、Magpie、AutoMat、ElemNet、Roost）的 ΔHf MAE 相对 ElFrac 基线降低 27–74%、与 DFT-vs-实验误差（~0.1–0.2 eV/atom）相当；但 ΔHd（分解能/到凸包距离）MAE ≈ 0.10–0.14 eV/atom（除 Roost 外仅边际提升），稳定性分类 accuracy<80%、F1<0.75、FPR>0.15（Table S2 口径）；
2. 在稀疏化学空间（Li-Mn-TM-O：13,659 候选、9 个 MP 稳定化合物），组合模型全部仅正确预测 1–2 个稳定化合物（预测稳定 507–685 个、3.7–5.0%），仅结构模型 CGCNN（ΔHf MAE=34 meV/atom）可用。

请基于冻结数据回答：

1. **数据与基准**：解析冻结的 6 个 CritExam CSV（Ef/Ed × train/val/test，共 85,014 成分），统计划分行数（train 59,509 / val 12,752 / test 12,753）与 Ef/Ed 目标分布（eV/atom）。
2. **形成能模型**：实现并训练 ≥1 个组合式模型（建议 ElFrac 基线：元素分数特征 + XGBoost/GradientBoosting/Ridge；可另加 Magpie 式元素统计特征或轻量 MLP 作对照），在 Ef test 上报告 MAE/RMSE/R²。
3. **稳定性预测对照**：用预测 ΔHf 重建各化学空间凸包得到 ΔHd,pred（可用 pymatgen `PhaseDiagram` 或自写 hull 代码并说明方法），或等价地训练 ΔHd 回归器/分类器，以 ΔHd≤0 为稳定判据报告 accuracy/F1/FPR（可选报告 ΔHd MAE）。关键输出：Ef 预测误差小（MAE ≤ ~0.2 eV/atom 量级）而稳定性分类指标差（acc<80% 或 F1<0.75 或 FPR>0.15 至少其一成立）的对照表。
4. **验证论文论断**：用冻结的 6 个 `Ed_allMP_<model>_ml_results.json`（各含 85,014 条 formulas→ΔHd 预测）重算各模型 ΔHd MAE（对照 0.069–0.101 eV/atom），并用 5 个 `Ed_classifier_<model>_ml_results.json` 重算分类指标（对照 acc 0.72–0.79、F1 0.63–0.73、FPR 0.15–0.22）。结合自身训练结果给出四档结论。

- 结论标签：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结）→ 物理位置 `$PAPER_BENCH_DATA_DIR`（来源/许可/逐文件 SHA-256 见 `data/SOURCE.md` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 文件：6 个 `CritExam__{Ef,Ed}_{train,val,test}.csv`（`formula,target`，target 单位 eV/atom）；6 个 `Ed_allMP_<model>_ml_results.json`（论文官方仓库模型结果：`stats` + `data.formulas`/`data.Ed`）；5 个 `Ed_classifier_<model>_ml_results.json`（分类器结果：`stats.Ed.cl` 含 precision/recall/f1/accuracy/fpr）。
- 来源：`Kaaiian/mse_datasets`（GitHub 公开仓库，CritExam 预划分 CSV）；`CJBartel/TestStabilityML`（论文官方仓库，MIT）。底层数据为 Materials Project DFT 计算。
- 规模：全部 ~31MB；ElFrac 式基线 CPU 数分钟即可；hull 重建建议用 pymatgen（若无，可走 ΔHd 回归/分类替代路线）。

## 方向提示（协议建议）

1. **划分**：直接使用冻结 CSV 的 train/val/test（与论文/仓库同源）。
2. **特征**：ElFrac=元素分数向量（补齐 0 列）；Magpie 式=元素统计属性（可用 matminer，或按元素周期表手算均值/方差/极差）。
3. **模型**：回归 XGBoost/GradientBoosting/Ridge；分类 LogisticRegression/RandomForest；固定随机种子。
4. **指标**：回归 MAE/RMSE/R²（eV/atom）；分类 accuracy/F1/FPR（稳定=ΔHd≤0）；hull 重建需说明化学空间（按元素集分组）与稳定判据。
5. **对照**：论文 Figure 2（ΔHf MAE 降 27–74%）、Figure 3/4 与 Table S2（acc<80%、F1<0.75、FPR>0.15）——论文数值仅用于对照讨论，禁止抄作实测。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从冻结数据读取并完成训练与评估。
3. **`results/evidence_table.csv`**：至少含列 `dataset,method,split,metric,value`。
4. **`results/metrics.json`**：样本统计、各方法指标、ΔHf vs 稳定性对照、论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（hull 实现/特征/划分差异 vs 论文）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止合成/模拟数据。
- 禁止手工抄写论文数字作为「实测结果」；所有指标必须运行代码得到。
- 论文数值只能用于对照讨论；两种方法必须同一划分、同一评估协议。
