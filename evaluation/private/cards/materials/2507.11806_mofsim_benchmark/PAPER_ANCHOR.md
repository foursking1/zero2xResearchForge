# PAPER_ANCHOR: 2507.11806_mofsim_benchmark（私有）

论文：Kraß, Huang & Moosavi, "MOFSimBench: Evaluating Universal Machine Learning Interatomic Potentials In Metal–Organic Framework Molecular Modeling", arXiv:2507.11806 (2025)。锚全部摘自论文正文/表格/图，并用冻结数据重算验证（编译期核对，2026-08-13）。

## 锚 1（主锚，A 维度，可复算）
- 指标名：四个原型 MOF 的 DFT 体弹模量 B0（GPa）
- 论文数值（SI Table S.1，`DFT` 行）：**MOF-5 = 16.06、IRMOF-10 = 9.4、UiO-66 = 37.5、HKUST-1 = 23.58 GPa**
- 出处：
  - SI Table S.1 "Bulk modulus computed with different uMLIPs for MOF-5, IRMOF-10, HKUST-1, and UiO-66" 的 `DFT` 行（表位于 SI；正文 Figure 2 区域引用 "see SI Table S.1 for the full table of all 21 uMLIPs"）。
  - Figure 2（正文 "Modeling Prototypical MOFs" 节）紫色 DFT 参考线，与 Table S.1 DFT 行一致。
  - 冻结官方数据 `bulk_modulus_eos_dft_reference.csv` 的 `B0_GPa` 列：16.0623 / 9.3993 / 37.4997 / 23.5815。
- 定义口径：DFT 结构优化后对 5（UiO-66 为 11）个应变点拟合 Birch–Murnaghan EOS 得到的 B0；单位 GPa。
- 编译期重算（冻结数据，三阶 BM，B1 自由）：16.0622 / 9.3991 / 37.5013 / 23.5811 —— 与 CSV 列差 ≤0.002 GPa、与论文两位小数一致。
- 容差（判定满分档）：拟合 B0 与论文值 **±0.5 GPa**；与 CSV `B0_GPa` 列 **±0.05 GPa**。

## 锚 2（主锚，A 维度，可复算）
- 指标名：DFT 体弹模量参考集规模（结构数）
- 论文数值：**100**（正文 "Static modeling and structure optimization" 节： "We extend our analysis to a larger set of 100 MOFs, COFs, and zeolites"）
- 出处：正文第 10–11 页（"larger set of 100"）；冻结 CSV 行数 = 100。
- 编译期核对：冻结 `bulk_modulus_eos_dft_reference.csv` 恰 100 行、结构名唯一。
- 容差：行数恰好 100。

## 锚 3（佐证，A 维度，部分可复算）
- 指标名：DFT 热容参考集规模与 Cv(300 K)/g 参考表
- 论文数值：Figure 7 及正文 "comprise a set of 231 MOFs, COFs, and zeolites"（DFT 参考源自 Ref. 57 数据集）。
- 冻结数据：`heat_capacity_cv_300k_dft_reference.csv` 恰 **232 行**（232 个唯一框架）。行数与论文"231"差 1——本卡将"如实报告并讨论差异"作为 A3/C 的诚实性加分点，不裁决对错。
- 出处：正文 Figure 7 讨论段（"Heat capacity ... compared to DFT references from Ref. 57, which comprise a set of 231 MOFs, COFs, and zeolites"）。
- 容差：无硬数值容差；要求报告覆盖数并对照论文 231。

## 锚 4（背景，不可从冻结数据复算，不入 A 分）
- 指标名：体弹模量预测 MAE（Figure 6，需 SI 中 uMLIP 预测）与 UFF 行（Table S.1）
- 论文数值（正文）：MACE-MP-MOF0 MAE=3.14、SevenNet-mf-ompa MAE=3.35、eSEN-OAM MAE=2.64、orb-d3-v2 MAE=72.29、eqV2-OMsA MAE=11.05 GPa；eSEN-OAM MAPE=22.1%、orb-v3-omat MAPE=23.4%。Table S.1 UFF 行：14.5/7.6/28.7/42.4 GPa。
- 定义口径：uMLIP 在 100 结构上预测 B0 vs DFT 参考的误差（Figure 6）；UFF 行为论文 UFF EOS 计算结果。
- 说明：需 SI 中 uMLIP/UFF 模拟输出，未随仓库发布可冻结文件；本卡明确不要求复算（TASK.md 已注明）。

## 辅助事实（裁判核查用）
- 正文核心结论：top-performing uMLIP 全面超越经典力场与微调 MLIP；**数据质量（训练集多样性、含非平衡构象）比模型架构更重要**。
- 四个原型 MOF 的 UFF 与 MACE-MP-MOF0 在 Figure 2 的表现；orb-d3-v2/eqV2-OMsA 为非保守模型（力为直接输出），EOS 不稳定。
- Methods：B0 由 Birch–Murnaghan EOS 拟合；EOS 体积最小点偏离优化体积 >1% 视为不稳定拟合并排除。
- 数据源：GitHub AI4ChemS/mofsim-bench（MIT）；论文 arXiv:2507.11806；SI 内嵌于 arXiv PDF（72 页版）。