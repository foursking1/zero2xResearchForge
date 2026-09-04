# 科研任务：检验「RadonPy 全自动 MD 计算高分子性质与 PoLyInfo 实验值系统一致」关键论断（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2203.14090_radonpy_polymer_informatics`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Hayashi et al., "RadonPy: Automated Physical Property Calculation using All-atom Classical Molecular Dynamics Simulations for Polymer Informatics", npj Comput. Mater. 8, 222 (2022)（arXiv:2203.14090）
- 领域：materials / 高分子信息学 / 自动化 MD 计算性质数据库

## 问题（可证伪）

论文开发 RadonPy——全自动全原子经典 MD 计算管线，对 1,138 个均聚物（选自 PoLyInfo 15,335 个仅含 H/C/N/O/F/P/S/Cl/Br/I 十元素的均聚物）计算 15 种物理性质（密度、热导率、比热容、热膨胀系数、体积模量、折射率等）。核心论断：
1. **自动化产出**：1,138 个目标中至少一次计算成功 1,070 个，≥3 次成功 1,001 个，5 次全成功 759 个；失败分为 4 类（DFT 不收敛、MD 未平衡、取向序参数>0.1、NEMD 温度梯度非线性）。
2. **系统性验证**：计算值与 PoLyInfo 实验值系统比较（密度、热导率、折射率、Cp、线膨胀/体积膨胀系数），显示良好一致；热导率关注度最高。
3. **数据库价值**：PI1070 数据集（1,070 聚合物 × 15 性质，含均值/标准差/计数）作为计算性质数据库发布，支撑高分子信息学；并发现 8 个热导率未报道的高热导率无定形聚合物。
4. **机制分析**：热导率分解（键/角/二面角/库仑等）揭示高热导率来自氢键与偶极-偶极相互作用或刚性线性主链共价键。

请基于冻结数据回答：

1. **数据统计**：解析冻结的 `PI1070.csv`（1,077 行、157 列，20 个 polymer_class），报告：唯一聚合物数（monomer_ID）、polymer_class 分布、15 类性质列的存在与均值/标准差（如 `density`、`thermal_conductivity`、`refractive_index`、`Cp`、`bulk_modulus` 等）。
2. **性质分布**：至少选 3 个性质（建议 `density`、`thermal_conductivity`、`refractive_index`），报告分布（均值/中位数/范围）并说明这些是 MD 计算值（含 _min/_max/_std/_count 列）。
3. **与论文对照**：从冻结数据筛选 PoLyInfo 可匹配的聚合物（按 polymer_class 或单体 SMILES），定性/定量比较计算性质分布与论文 Figure 中实验值范围的趋势（如热导率随结构变化），验证「系统性一致」的方向性。
4. **验证论文论断**：结合自身结果给出四档结论。

- 结论标签：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结）→ 物理位置 `$PAPER_BENCH_DATA_DIR`（来源/许可/逐文件 SHA-256 见 `data/SOURCE.md` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 文件：`PI1070.csv`（1,077 数据行 × 157 列；列含 `monomer_ID,smiles,mol_weight_monomer,...,density,density_min/max/std/count,Rg,self-diffusion,Cp,Cv,compressibility,bulk_modulus,thermal_conductivity,refractive_index,...`，单位 SI/常用：密度 g/cm³、热导率 W/m/K、折射率无量纲、Cp J/kg/K 等）+ `LICENSE`（RadonPy 仓库 MIT）。
- 来源：RadonPy 官方 GitHub 仓库 `radonpy/radonpy`（MIT License）`data/PI1070.csv`；论文 Supporting Information 同步发布。
- 规模：~1.5MB；纯表格分析，CPU 秒级。

## 方向提示（协议建议）

1. **读表**：`pandas.read_csv('PI1070.csv')`；注意 157 列中含 `_min/_max/_std/_count` 后缀的统计列（5 次独立 MD 重复）。
2. **性质选择**：推荐 `density`、`thermal_conductivity`、`refractive_index`、`Cp`（比热容）；报告分布并对照论文 Table/Figure。
3. **polymer_class**：20 类（如 polystyrene、polyvinyl、polyacrylate 等，来自 PoLyInfo 分类），可做类别分布与跨类热导率比较。
4. **对照**：论文 Figure 4/5（计算 vs 实验验证）与正文（1,138→1,070/1,001/759）数值仅用于对照讨论，禁止抄作实测。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从冻结数据读取并完成统计/分析。
3. **`results/evidence_table.csv`**：至少含列 `property,metric,value`（各性质均值/中位数/范围）。
4. **`results/metrics.json`**：样本统计、性质分布摘要、论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（与 PoLyInfo 匹配粒度/对照方式差异 vs 论文）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止合成/模拟数据。
- 禁止手工抄写论文数字作为「实测结果」；所有指标必须运行代码得到。
- 论文数值只能用于对照讨论。
