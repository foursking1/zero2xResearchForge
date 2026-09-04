# 科研任务：检验「FC 基维度分类大规模发现低维材料」关键论断（L2）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2509.20164_lowdim_materials_screening`
- 层级：L2（卡标 L2/L3→L2 题：方法复现 + 大规模筛选验证）
- 论文：Bagheri et al., "Massive Discovery of Low-Dimensional Materials from Universal Computational Strategy", arXiv:2509.20164（2026）
- 领域：materials / 低维材料发现 / 力常数基维度分类（FCDimen）

## 问题（可证伪）

论文用通用 ML 原子间势（UMLIP）计算力常数（FC），用 FC 基维度分类方法（FCDimen）对大规模材料做低维性筛选。核心论断：
1. **基准**：对 Materials Project（MP）35,689 个材料用 UMLIP 计算力常数与声子，验证其首性原理级精度（对照 >10K 材料的声子数据库）。
2. **大规模发现**：对 153,234 个块体材料筛选，发现 **9,139 个低维材料**（1,838 个 0D 团簇 / 1,760 个 1D 链 / 3,057 个 2D 层 / 2,484 个混合维度），均为传统几何描述符无法识别的。
3. **可剥离 2D**：对发现的 2D 材料计算结合能，识别 **887 个可易剥离/可能剥离的 2D 片层**，全部为已知 2D 数据库（C2DB/2DMatPedia/MC2D 等）之外的新材料。
4. **数据库发布**：`screened_materials.json`（全部优化材料+性质）与 `2D_materials.json`（发现的 2D 材料+剥离能+性质）。

请基于冻结数据回答：

1. **数据统计**：解析冻结的 `screened_materials.json`（~197MB，全部筛选材料；字段含 `formula,mpid,ehull,mp_gap,stable,spacegroup,dimen_larsen,fcdimen_score,dim_fcdimen_c1/c2/c3,free_energy` 等）与 `2D_materials.json`（~13MB，发现的 2D 材料；字段含 `E_exf,ehull,mp_gap,c2db,matpedia,mc2d,rae` 等）。统计：筛选材料总数、FCDimen 维度分布（c1/c2/c3）、2D 材料数。
2. **维度分类复现（核心）**：对 `2D_materials.json` 中的条目，基于 `fcdimen_score`/`dim_fcdimen_c1` 验证维度判据；或对 `screened_materials.json` 抽样用 FCDimen 分数重建 0D/1D/2D/混合维度计数（对照论文 9,139 = 1,838/1,760/3,057/2,484）。
3. **剥离能分析**：对 2D 材料报告 `E_exf`（meV/Å）分布，估计「易剥离/可能剥离」阈值下的数量（对照论文 887），并结合 `c2db/matpedia/mc2d/rae` 标记说明新材料占比。
4. **验证论文论断**：结合自身结果给出四档结论。

- 结论标签：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结）→ 物理位置 `$PAPER_BENCH_DATA_DIR`（来源/许可/逐文件 SHA-256 见 `data/SOURCE.md` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 文件（Zenodo 记录 17035156 的 `databases.zip` 解包）：
  - `screened_materials.json`：153,234 个筛选材料的优化结构+性质（~197MB）。
  - `2D_materials.json`：发现的 2D 材料+剥离能+性质（~13MB）。
  - `README.txt`：字段说明（见上）。
- 来源：Zenodo DOI 10.5281/zenodo.17035156（论文 Data Availability 指定）。
- 规模：~210MB；JSON 解析需 pandas/纯 Python（大文件建议 `ijson` 或抽样），CPU 可完成。

## 方向提示（协议建议）

1. **读取**：`2D_materials.json` 为 dict（键为序号）；`screened_materials.json` 同构；可用 `json.load`（注意内存）或按需抽样。
2. **维度计数**：论文口径 FCDimen 的 c1（原始分数判据）/c2/c3 三变体；从 `dim_fcdimen_c1`（字符串维度标签）直接统计最直接。
3. **剥离能**：`E_exf` 单位 meV/Å；论文按结合能阈值区分「易剥离/可能剥离」。
4. **已知性**：`c2db/matpedia/mc2d/rae/topo/DBBs` 布尔标记表示是否存在于已知 2D 数据库。
5. **对照**：论文 Abstract/Section III（35,689 基准、9,139 低维、887 可剥离）数值仅用于对照讨论，禁止抄作实测。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从冻结数据读取并完成统计/分析。
3. **`results/evidence_table.csv`**：至少含列 `dataset,group,metric,value`（维度分布、E_exf 统计、已知性计数）。
4. **`results/metrics.json`**：样本统计、FCDimen 分布、剥离能分析、论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（大文件解析/口径差异 vs 论文）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止合成/模拟数据。
- 禁止手工抄写论文数字作为「实测结果」；所有统计必须运行代码得到。
- 论文数值只能用于对照讨论。
