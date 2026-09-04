# Solution: 2501.02144_gen_discovery_baselines

## 结论摘要（判定：复现）

从冻结的 6 个方法 CSV（各 500 个 novel 结构，Ed 单位 eV/atom）独立复算得到的中位分解能 ΔEd（meV/atom）与稳定性率（Ed ≤ 0 占比）与论文 Table 1 完全一致（FTCP 205 vs 205.5 为舍入差），方法排序完全一致。论文科学目标三问的答案如下。

## 方法

1. **数据**：冻结 `F:/dataset/materials/2501.02144_gen_discovery_baselines/structures/<Method>.csv`，每文件 500 行 + 表头，列 `Chemical Formula, Space Group Number, Ed (eV/atom)`。Ed 单位 eV/atom，论文 Table 1 用 meV/atom（×1000）。
2. **校验**：6 个 CSV 的 SHA-256 与 `data/CHECKSUMS_SHA256.tsv` 全部一致（脚本自动核验）。
3. **指标**：
   - 中位 ΔEd（meV/atom）= 样本 Ed 中位数 ×1000。
   - 稳定性率（%）= Ed ≤ 0 的样本数 / 500 × 100。
   - 分布分位数：20/50/80/90 百分位（meV/atom）。
4. **工具**：pandas/numpy/statistics，CPU 单进程。

## 结果

| 方法 | 中位 ΔEd 论文 | 中位 ΔEd 本工作 | 稳定性率 论文 | 稳定性率 本工作 | q80 本工作 (meV/atom) |
|---|---|---|---|---|---|
| Random | 409 | **409.5** | 1.4% | **1.4%** | 804.2 |
| Ion-Exchange | 85 | **85.5** | 9.2% | **9.2%** | 190.0 |
| CrystaLLM | 442 | **442.0** | 2.4% | **2.4%** | 806.2 |
| CDVAE | 207 | **207.0** | 1.8% | **1.8%** | 340.2 |
| FTCP | 205 | **205.5** | 2.0% | **2.0%** | 345.2 |
| MatterGen | 188 | **188.5** | 3.0% | **3.0%** | 311.4 |

- **中位 ΔEd 排序**：Ion-Exchange(85.5) < MatterGen(188.5) < FTCP(205.5) < CDVAE(207.0) < Random(409.5) < CrystaLLM(442.0)。与论文一致（FTCP 205 vs 205.5 为舍入差）。
- **稳定性率排序**：Ion-Exchange(9.2%) > MatterGen(3.0%) > CrystaLLM(2.4%) > FTCP(2.0%) > CDVAE(1.8%) > Random(1.4%)。
- **分布形状**：Ion-Exchange 分布最紧（q80 = 190 meV/atom，约 100 meV/atom 量级）；CrystaLLM（806）与 Random（804）最分散（>600 meV/atom 量级）；生成模型 CDVAE/FTCP/MatterGen 居中（311–345）。与论文方向一致。

## 科学目标回答

1. **模板化基线 vs 生成模型**：离子交换模板基线（Ion-Exchange）显著最优（中位 85.5 meV/atom、稳定性率 9.2%）；随机枚举基线（Random）最差（409.5 meV/atom、1.4%）；生成模型居间（中位 188–442 meV/atom、稳定性率 1.8–3.0%）。结论：**"模板基线并非全面优于生成模型，仅离子交换显著更优"** —— 与论文一致。
2. **稳定性-新颖性权衡**：从冻结数据可直接量化稳定性，但新颖性率（不在 MP 中的比例）与新原型率（AFLOW 无法索引）需 MP/AFLOW 全集对比，**无法从冻结数据重算**（TASK 已声明）。论文报告的新颖性率（Random 98.6% / IonX 72.4% / FTCP 38.2% / CDVAE 96.0% / MatterGen 91.8% / CrystaLLM 98.2%）显示稳定性最高的 Ion-Exchange 新颖性最低、稳定性最低的 Random 新颖性最高，方向支持"稳定性-新颖性反向权衡"，但该方向为论文上下文值，不构成本工作复算。
3. **生成模型类别内差异**：扩散（MatterGen）在生成模型中稳定性率最高（3.0%）且中位 ΔEd 最低（188.5）；VAE（CDVAE）与 flow（FTCP）接近（1.8–2.0%、205–207）；LLM（CrystaLLM）中位 ΔEd 最差（442）且分布最分散。生成模型中最接近"实用材料发现"的是 MatterGen（居间稳定、较窄分布）。

## 与论文口径的差异与局限

- Ed 定义、稳定性判据（Ed ≤ 0）、单位换算（eV/atom → meV/atom ×1000）均按论文/冻结数据口径。
- CIF 样例（每方法 10 个）仅作结构格式示例，不参与统计。
- 新颖性率 / 新原型率 / 属性定向命中率 / CHGNet 筛选后稳定性等论文数字需 MP/AFLOW 全集或重跑筛选，无法从冻结数据复算；本报告仅作方向性讨论引用并明确标注为论文报告值。
- 设备：CPU 单进程。

## 数据来源与许可

- 论文：Szymanski & Bartel, "Establishing baselines for generative discovery of inorganic crystals", arXiv:2501.02144 (2025)。
- 官方仓库：github.com/Bartel-Group/matgen_baselines（commit 770129797a9919955d84f3c3e59cc389e3b04315）。
- 许可：仓库 MIT（`data/LICENSE`）；底层含 Materials Project 派生数据，受 MP 数据条款约束。
- 校验：6 个 CSV SHA-256 与 `data/CHECKSUMS_SHA256.tsv` 一致。
- 代码：`agent_solution/code/analyze_baselines.py`。
