# 科研任务：检验「无缺陷结构的系统性训练集可得到可迁移的 Mg 缺陷 ML 势」关键论断（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2207.04009_mg_mtp_defect_training`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Mortazavi et al., "Systematic Atomic Structure Datasets for Machine Learning Potentials: Application to Defects in Magnesium", arXiv:2207.04009（2023）
- 领域：materials / 机器学习势（MTP）/ 缺陷建模

## 问题（可证伪）

论文提出一套物理驱动的训练集构建策略：通过随机晶体结构（Random-SPG）+ 体积/单轴应变 + 声子 + 无缺陷构型等系统性采样，构造纯 Mg 的 MTP 训练数据，**训练集中完全不含缺陷结构、也不使用主动学习**，却能对空位、间隙、位错、晶界等缺陷给出可迁移的高精度描述。核心论断：
1. **数据集结构**：Everything（全部构型）与 Everything±Shear（加/不加剪切构型）两套训练集；DFT（PBE）参考数据收敛到能量误差 0.6 meV/atom（均值）、6.4 meV/atom（最大）。
2. **MTP 精度**：MTP 训练 RMSE 随势阶/截断半径提升，最优配置能量误差 ~10 meV/atom 量级，比经典势（EAM/MEAM/Tersoff 类）低 1–2 个数量级。
3. **缺陷可迁移性**：不用任何缺陷结构训练，MTP 即可准确描述空位/间隙形成能、晶界能、位错核等缺陷性质，优于现有 Mg 势；bcc Mg 的声子谱/弹性也被正确复现（此前经典势做不到）。
4. **剪切构型的作用**：加入 Shear 集（体积/单轴应变变体）可显著影响势在弹性/缺陷性质上的表现（论文分析各子集对性能的影响）。

请基于冻结数据回答：

1. **数据统计**：解析冻结的 Edmond 数据集（`structures_packed.csv` / `fit_packed.csv` 索引 + 对应 `*.tar.gz` 内 AiiDA 计算文件），统计两套数据的构型总数、job/subjob 类别分布（如 Hydrostatic、Uniaxial、Phonons、Shear 等）。
2. **参考数据质量**：从 packed 数据中抽查 DFT 计算的收敛参数（k 点、平面波截断、能量/力收敛阈值），报告论文声称的 0.6 meV/atom 均值与 6.4 meV/atom 最大收敛误差（若能复算）。
3. **势拟合（可选但加分）**：用冻结的 AiiDA 结构/能量数据拟合一个轻量 MTP 或代理势（可用 MLIP 包或简化描述符回归），报告能量 RMSE（meV/atom），验证「1–2 个数量级优于经典势」的方向性（可用 EAM/MEAM 作对照）。
4. **验证论文论断**：结合自身结果（至少完成数据统计与子集分析）给出四档结论。

- 结论标签：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结）→ 物理位置 `$PAPER_BENCH_DATA_DIR`（来源/许可/逐文件 SHA-256 见 `data/SOURCE.md` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 文件（Edmond DOI 10.17617/3.A3MB7Z 原始发布物）：
  - `structures_packed.csv`（10 行索引）+ `structures_packed.tar.gz`（11 members，~832MB 解压）：初始构型计算的 AiiDA 归档（Random-SPG 随机晶体结构、体积/单轴应变等）。
  - `fit_packed.csv`（47 行索引）+ `fit_packed.tar.gz`（280 members，~1.0GB 解压）：MTP 拟合所用 DFT 参考数据（含 job/subjob 类别）。
  - `structure_files.tar.gz` / `fit_files.tar.gz`：对应未打包文件。
  - `MANIFEST.TXT`：Edmond 发布的文件清单与字节数。
- 来源：Edmond 开放研究数据仓库（Max Planck Digital Library），DOI 10.17617/3.A3MB7Z；论文 Data Availability 提供。
- 规模：~742MB（压缩）；结构数据为 AiiDA 归档，解析需 `aiida` 或手工解 tar.gz 读取输入/输出文件（VASP POSCAR/OUTCAR 或转换后数据）。

## 方向提示（协议建议）

1. **解析**：tar.gz 内为 AiiDA 节点归档（含 `*.txt` 元数据与计算输入输出）；可用 `aiida.tools.importexport` 或直接搜索目录内 VASP 输出文件；若环境无 AiiDA，可统计目录/文件并说明解析范围。
2. **构型类别**：从 packed CSV 的 `job/subjob` 列或 tar 内路径统计（如 `Hydrostatic`、`Uniaxial`、`Phonon`、`Shear`、`Random` 等）。
3. **指标**：能量 RMSE（meV/atom）；对照 EAM/MEAM 或论文 Figure 4 数值。
4. **对照**：论文 Figure 4（能量 RMSE 随势阶/截断）、Figure 9（声子力常数误差）、缺陷验证章节数值仅用于对照讨论，禁止抄作实测。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从冻结数据读取并完成统计/拟合。
3. **`results/evidence_table.csv`**：至少含列 `dataset,subset,metric,value`（构型数、类别计数、能量 RMSE 等）。
4. **`results/metrics.json`**：样本统计、各子集分析、论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（AiiDA 解析/拟合实现差异 vs 论文）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止合成/模拟数据。
- 禁止手工抄写论文数字作为「实测结果」；所有指标必须运行代码得到。
- 论文数值只能用于对照讨论。
