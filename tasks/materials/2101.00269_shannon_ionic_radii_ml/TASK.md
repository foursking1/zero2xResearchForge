# 科研任务：检验「ML 扩展 Shannon 离子半径数据库（475→987 离子）GPR 精度」关键论断（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2101.00269_shannon_ionic_radii_ml`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Baloch et al., "Extending Shannon's Ionic Radii Database Using Machine Learning", Phys. Rev. Materials 5, 043804 (2021)（arXiv:2101.00269）
- 领域：materials / 材料信息学 / 离子半径数据库扩展

## 问题（可证伪）

论文用高斯过程回归（GPR）把 Shannon 离子半径表从 475 个离子扩展到 987 个离子（预测 512 个新离子），特征为周期数、价电子构型、氧化态（OS）、配位数（CN）、电离势。核心论断：
1. **精度**：GPR 在 Shannon 475 个离子上做 7 折交叉验证，RMSE=0.0332 Å，R²=99.3%。
2. **特征有效**：周期数、价电子构型、OS、CN、电离势可解释离子半径；模型对未见过的 OS/CN 组合给出合理预测。
3. **数据库扩展**：扩展表含 987 个离子（含 512 个新预测），对无 Shannon 数据的稀有组合（来自 Materials Project 晶体结构提取）提供半径值，可用于容差因子/结构分类等下游应用。
4. **负离子校准**：后续工作（Alsalman et al.）对阴离子半径做了与 Shannon 表一致的校准（"Updated Anions" 列）。

请基于冻结数据回答：

1. **数据统计**：解析冻结的 `ionic_radii_extended.csv`（由官方站点 cmd-ml.github.io 内嵌数据表解析；1005 行，含 Shannon 半径 476 个 + ML 半径 988 个，单位 pm）。统计元素/氧化态/配位数覆盖，报告 Shannon 有值与 ML 预测值的行数。
2. **GPR 复现（核心）**：用冻结数据中「Shannon 有值」的行作为监督标签（特征：周期数、价电子构型或原子序数、OS、CN），实现 GPR（或 Ridge/MLP 对照），报告 RMSE（Å）与 R²，验证「RMSE≈0.0332 Å、R²≈99%」的量级与方向。
3. **扩展验证（可选）**：用训练好的模型对「仅 ML 预测」的行做留一/抽样验证（若模型对这些行有预测），或定性讨论预测半径的物理合理性（随 OS 升高半径减小、随 CN 升高半径增大）。
4. **验证论文论断**：结合自身结果给出四档结论。

- 结论标签：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结）→ 物理位置 `$PAPER_BENCH_DATA_DIR`（来源/许可/逐文件 SHA-256 见 `data/SOURCE.md` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 文件：
  - `ionic_radii_extended.csv`：解析自官方站点内嵌数据表，列 `element,oxidation_state,coordination_number,shannon_radius_pm,ml_radius_pm,ml_sd_pm,updated_anion`（1005 行；单位 pm）。
  - `cmd-ml.github.io_index.html`：官方站点原始 HTML 存档（2026-08-13 抓取，数据来源）。
  - `README.md`：本包说明。
- 来源：论文官方数据库站点 `https://cmd-ml.github.io/`（论文 Data Availability 指定）。
- 规模：~200KB；GPR 毫秒-分钟级，CPU 可完成。

## 方向提示（协议建议）

1. **单位**：CSV 内为 pm，论文指标为 Å；换算 1 Å=100 pm。
2. **特征**：周期数可用元素原子序数/周期表映射；价电子构型可简化为元素族/价电子数；OS 与 CN 直接用列。
3. **模型**：GPR（sklearn `GaussianProcessRegressor`，RBF 核 + 白噪声）与 Ridge/MLP 对照；固定随机种子；7 折 CV 或声明划分。
4. **指标**：RMSE（Å）、R²；对照论文 0.0332 Å / 99.3%。
5. **对照**：论文数值仅用于对照讨论，禁止抄作实测。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从冻结数据读取并完成训练与评估。
3. **`results/evidence_table.csv`**：至少含列 `feature_set,model,split,metric,value`。
4. **`results/metrics.json`**：样本统计、各模型指标、论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（特征简化/单位换算/划分差异 vs 论文）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止合成/模拟数据。
- 禁止手工抄写论文数字作为「实测结果」；所有指标必须运行代码得到。
- 论文数值只能用于对照讨论；不同方法必须在同一划分、同一评估协议下比较。
