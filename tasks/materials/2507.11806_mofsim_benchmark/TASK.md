# Task: 2507.11806_mofsim_benchmark（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

## 元信息
- task_id: `2507.11806_mofsim_benchmark`
- 层级: L1（critical claim，可证伪）
- 论文: Kraß, H., Huang, J., Moosavi, S.M. *MOFSimBench: Evaluating Universal Machine Learning Interatomic Potentials In Metal–Organic Framework Molecular Modeling.* arXiv:2507.11806 (2025).
- 领域: materials（MOF/多孔材料通用 ML 势场基准）
- 数据: 论文官方 GitHub 仓库 AI4ChemS/mofsim-bench（MIT）发布的 DFT 参考数据

## 问题（可证伪）
论文核心 claim：MOFSimBench 的 **DFT 参考体弹模量（B0）数据集**真实且可复算——它覆盖 **100 个 MOF/COF/沸石结构**（正文 "a larger set of 100 MOFs, COFs, and zeolites"），每个结构给出 ≥5 个应变点的（体积, 能量）EOS 数据；其中四个原型 MOF 的 DFT B0 为 **MOF-5=16.06、IRMOF-10=9.4、UiO-66=37.5、HKUST-1=23.58 GPa**（SI Table S.1 的 DFT 行，与 Figure 2 紫色 DFT 线一致）。

请仅用本任务冻结数据（官方仓库 DFT 参考 + 论文 SI 提取表 + 4 个原型 CIF）独立复算并回答：

1. **C1（主锚，对应 Table S.1 DFT 行）**：从冻结 EOS 表取 MOF-5/IRMOF-10/UiO-66/HKUST-1 的 `volumes_A3`–`energies_au` 点，用**三阶 Birch–Murnaghan EOS** 拟合，报告各结构的 B0（GPa）与 V0/E0/B1。复算结果是否与 Table S.1 DFT 行（16.06 / 9.4 / 37.5 / 23.58 GPa）一致（±0.5 GPa）？是否与冻结 EOS 表的 `B0_GPa` 列一致（±0.05 GPa）？
2. **C2（数据集规模与拟合一致性）**：对冻结 EOS 表**全部 100 个结构**做同一 EOS 拟合，报告：行数是否恰好 100；拟合 B0 vs `B0_GPa` 列的偏差分布（中位/最大绝对偏差、≤0.5 GPa 的结构数/占比）；对偏差较大的结构给出名称与可能原因（论文 Methods 承认部分 EOS 拟合不稳定会被排除）。结论是否支持"100 结构 DFT 体弹模量参考集"claim？
3. **C3（佐证）**：a) 4 个原型 CIF（`data/opt_*_primitive.cif`）是否与 EOS 表 `structure` 名一一对应（`MOF-5/IRMOF-10/UiO-66/HKUST-1`）；b) 从冻结热容参考表报告覆盖框架数与 `cv_300K_JperKperg` 的分布（中位数/范围），并与论文 Figure 7 所称"DFT 参考覆盖 231 个 MOF/COF/沸石"对照——若冻结表行数与 231 不一致，如实报告并给出可能解释（本任务不要求裁决该差异）。

## 方向提示
- **数据**：`data/bulk_modulus_eos_dft_reference.csv`（100 行，列 `cif_name, strains, node_pks, volumes_A3, energies_au, B0_GPa, structure`）；`data/SI_Table_S1_bulk_modulus_GPa.csv`（Table S.1 的 PDF 提取版）；`data/heat_capacity_cv_300k_dft_reference.csv`（232 行）；4 个 `opt_*_primitive.cif`。
- **EOS 口径（论文 Methods）**："The bulk modulus was computed from a fitted Birch-Murnaghan equation of state." 三阶 BM：`E(V) = E0 + (9·V0·B0/16)·[(η−1)³·B1 + (η−1)²·(6−4η)]`，其中 `η = (V0/V)^(2/3)`。
- **单位换算**：`energies_au` 为 hartree；**1 hartree/Å³ = 4359.7447222071 GPa**。建议以 `energies_au` 最低点对应体积为 V0 初值；超大胞结构（总能量 ~1e5 Ha）对拟合数值尺度敏感，可用多初值/能量中心化提升稳健性。
- **Table S.1 说明**：提取表含 20 个 uMLIP 行 + `DFT` 行 + `UFF` 行（正文称 SI 共 21 个被评测模型，含 host-guest 专用 MACE-DAC-0，不在本表）。DFT 行即 C1 目标。
- **独立实现**：自行编写解析脚本（Python 即可，scipy 拟合或手写最小二乘均可）；不得调用论文作者未随数据发布的程序。
- **诚实报告**：C2 中若个别结构拟合不稳定（如 B0 数量级异常、V0 超出采样范围），如实列出，不要静默丢弃。

## 数据说明
- 目录：`data/`（冻结，9 文件，约 100 KB；来源见 `data/DATA_SOURCES.md` 与 `data/README.md`）
- **来源**：论文官方 GitHub 仓库 `AI4ChemS/mofsim-bench`（论文 Data availability 声明明确指向该仓库的 DFT/UFF 结果；DFT EOS 与热容参考表均出自 `mof_benchmark/analysis/`）；`SI_Table_S1_bulk_modulus_GPa.csv` 由论文 arXiv 版 Supporting Information Table S.1 提取。
- **许可**：仓库 **MIT License**；论文正文按 arXiv 惯例。报告中须注明来源（arXiv 号 + 仓库 URL）。
- **Checksum**：`data/checksums.sha256`（9 文件 SHA-256 固定）；使用前必须校验。
- **Schema**：见 `data/README.md`。

## 输出要求
1. **结论**：对 C1/C2/C3 给出明确回答（复现 / 部分复现 / 未复现），并与论文数值逐项对比（Table S.1 DFT 行、100 结构 claim）。
2. **证据表**（`results/`）：4 个原型 MOF 的 B0/V0/E0/B1 表（含论文值、CSV 值、拟合值、偏差）；全 100 结构偏差统计表；偏差 >0.5 GPa 的结构清单。
3. **代码**：可运行脚本，能从冻结 `data/` 直接重算证据表全部数值（含 checksum 校验）。
4. **报告**：EOS 形式与拟合细节、单位换算、初始化策略、与论文口径的差异、局限性。

## 数据铁律提醒
- 只用本任务冻结的真实数据（官方 GitHub 发布 + 论文 SI 提取）；**禁止下载其他来源数据、禁止合成/伪造数据、禁止修改冻结文件**。
- 论文正文另有 uMLIP 预测类数值（如 Figure 6 的 MAE：MACE-MP-MOF0=3.14、SevenNet-mf-ompa=3.35、eSEN-OAM=2.64、orb-d3-v2=72.29 GPa）与 Table S.1 的 UFF 行（14.5/7.6/28.7/42.4 GPa）——这些需要 SI 中的 uMLIP/UFF 模拟输出，**本任务不要求复算**；如引用须注明不可从冻结数据复算。
- 报告中注明数据来源、许可与 checksum。