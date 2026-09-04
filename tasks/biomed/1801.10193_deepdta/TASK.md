# 科研任务（L2 端到端科研再发现）：基于序列的药物-靶点结合亲和力预测

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`1801.10193_deepdta`
- 层级：L2（RCBench 对齐：input/output/scientific goal 三段式；目标论文隐藏）
- 领域：biomed / 药物发现 / 药物-靶点结合亲和力（DTA）预测

## 任务描述（三段式）

### Input（给定）
- `data/`（冻结，物理位置 `$PAPER_BENCH_DATA_DIR`）：
  - **Davis 数据集**：`davis_ligands_can.txt`（68 个药物 SMILES）、`davis_proteins.txt`（442 个激酶蛋白序列）、`davis_drug-target_interaction_affinities_Kd__Davis_et_al.2011v1.txt`（68×442 亲和力矩阵，Kd 值，µM 取负对数），`davis_folds_train/test_fold_setting1.txt`（官方 5 折划分）。
  - **KIBA 数据集**：`kiba_ligands_can.txt`（2,111 药物 SMILES）、`kiba_proteins.txt`（229 蛋白序列）、`kiba_kiba_binding_affinity_v2.txt`（亲和力矩阵，预处理后分数），`kiba_folds_train/test_fold_setting1.txt`（官方 5 折划分）。
- 数据为真实测量/文献整合的激酶抑制活性数据；`fold_setting1` 为官方提供的 5 折交叉验证划分（train 含 4 折，test 含 1 折）。

### Output（必须产出）
1. **`method/`**：实现并训练**至少 2 类可运行的 DTA 预测器**：
   - 一个**序列编码深度模型**（如双 CNN 编码药物 SMILES 与蛋白序列并拼接回归；或 Transformer/图模型替代，框架不限）；
   - 至少 1 个**基线**（如基于相似度的 KronRLS 思路，或特征拼接 + 岭回归/GBDT，或药物-蛋白指纹 + RF）。
2. **`protocols/`**：实现 5 折交叉验证评估协议（使用包内官方 `fold_setting1` 划分，或自建固定 5 折并声明）；实现 Concordance Index（CI）与 MSE 计算。
3. **`results/`**：每数据集 × 每方法 × 每折的 CI/MSE 表（`evidence_table.csv`）、聚合指标（`metrics.json`）。
4. **`report.md`**：完整科研报告（见 Scientific Goal 的问题）。

### Scientific Goal（要回答的科学问题）
针对「仅从药物与靶点的**一维序列**能否学习到结合亲和力的有效表示」这一主题，回答：
1. **Q1 模型能力**：你的深度序列模型在 Davis 与 KIBA 测试折上的平均 CI 与 MSE 是多少？是否显著优于你实现的基线？
2. **Q2 数据集规模效应**：KIBA（约 118 万对）远大于 Davis（约 3 万对）——深度模型在更大数据集上的相对优势是否更明显（对比两数据集上深度模型 vs 基线的差距）？
3. **Q3 你的发现**：基于上述证据，你支持还是反对「仅用序列的深度学习即可达到甚至超过基于相似度/特征的基线（CI≈0.86-0.88）」这一论断？给出四档结论标签：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明
- 冻结真实数据（来源/许可/checksum 见 `data/SOURCE.md` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- Davis 亲和力矩阵为 Kd（µM）取负对数（数值越大亲和力越强）；KIBA 矩阵已按论文预处理（负号 + 平移，方向与亲和力一致）。
- 禁止从网络下载其他版本数据；禁止合成数据。
- 深度模型与基线必须在**同一 5 折划分、同一 CI/MSE 口径**下比较。

## 数据铁律提醒
- 只用本包冻结数据；禁止合成分子/蛋白或模拟亲和力。
- 时间/序列顺序不得打乱；划分固定；禁止测试折信息进入训练或早停。
- 禁止把任何论文数字当作「本实验实测」；所有指标必须由你的代码从本包数据算出。
- 论文锚（Davis 深度模型 CI≈0.878/MSE≈0.261、KIBA CI≈0.863/MSE≈0.194）只用于对照讨论。
