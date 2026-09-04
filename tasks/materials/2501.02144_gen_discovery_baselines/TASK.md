# Task: 2501.02144_gen_discovery_baselines（L2 端到端科研再发现）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

## 元信息
- task_id: `2501.02144_gen_discovery_baselines`
- 层级: L2（RCBench 三段式：input / output / scientific goal；目标论文隐藏，不提供全文）
- 领域: materials（无机晶体生成式发现评测：模板基线 vs 生成模型）

## 任务描述

### Input（输入数据）
- 六个生成方法的**冻结结构数据**（`data/structures/`，每个方法 500 个新材料，均为相对 Materials Project 的 novel 结构）：
  - 模板基线：`Random.csv`（随机电荷平衡原型枚举）、`Ion-Exchange.csv`（数据驱动离子交换）
  - 生成模型：`CrystaLLM.csv`（LLM）、`CDVAE.csv`（VAE）、`FTCP.csv`（flow 匹配）、`MatterGen.csv`（扩散）
  - 每行 schema：`Chemical Formula, Space Group Number, Ed (eV/atom)`；`Ed` = 相对 MP 稳定相凸包的分解能（meV/atom 口径换算，`≤0` 即在凸包上=热力学稳定）
- 结构数据样本：`data/structures/<Method>/*.cif`（每方法 10 个 CIF 样例，pymatgen 生成格式）
- 支持数据：`data/mp_formation_energies.json`（MP 形成能，分解能计算参考）、`data/element_energies.json`、`data/element_oxidation_states.json`、`data/prototypes.json`（结构原型库）
- 全部数据来自论文官方仓库 `github.com/Bartel-Group/matgen_baselines`（commit 770129797a9919955d84f3c3e59cc389e3b04315，2026-08-13 抓取）；许可证 MIT（`data/LICENSE`）

### Output（要求产出）
1. **证据表**（`results/evidence_table`）：每个方法 × 指标的统计表——`中位 ΔEd（meV/atom）`、`稳定性率（Ed≤0 占比 %）`、`Ed 分布分位数（如 80% 阈值）`；含各方法与论文 Table 1 目标值的对照。
2. **结论**：回答 scientific goal 的三问，给出明确的"基线 vs 生成模型"优劣边界判断与排序。
3. **代码**：可运行脚本，从冻结 `data/` 直接重算出证据表关键数值。
4. **报告**：方法、指标口径（Ed 定义、稳定性判据）、误差分析、局限。

### Scientific goal（科学目标）
在隐藏目标论文（2501.02144）的情况下，仅凭冻结数据回答：
1. 模板化基线（随机枚举、离子交换）与生成模型（CrystaLLM/CDVAE/FTCP/MatterGen）在"生成热力学稳定新材料"上谁更优？量化各方法中位分解能与稳定性率排序。
2. 稳定性-新颖性权衡是否成立：稳定性率高的方法是否以结构新颖性（新原型占比）为代价？
3. 生成模型是否存在类别内差异（扩散 vs VAE vs LLM），以及哪种方法最接近"实用材料发现"？

## 数据说明
- 目录：`data/`（冻结，71 文件，约 2.95 MB；SHA-256 见 `data/CHECKSUMS_SHA256.tsv`）
- **来源**：论文 Data Availability Statement 指向的官方仓库 `Bartel-Group/matgen_baselines`（含全部方法生成结构的 CIF 与 Ed 表）；本任务冻结 6 个 CSV（500 novel/方法）+ 每方法 10 个 CIF 样例 + 4 个支持 JSON。
- **许可**：仓库 LICENSE = MIT（`data/LICENSE`）；底层数据含 Materials Project 派生数据，使用需遵循 MP 数据条款。
- **口径**：`Ed` 单位 eV/atom（表中直接读出）；论文 Table 1 以 meV/atom 呈现（×1000）。稳定性率 = Ed ≤ 0 的占比。CSV 中全部结构均为 novel（不在 MP 中），故表中统计即论文 Table 1 的"novel materials"统计。

## 输出要求
1. 结论给出明确方法排序（稳定性率 / 中位 ΔEd）与"模板基线 vs 生成模型"判断。
2. 证据表覆盖全部 6 方法 ×（中位 ΔEd、稳定性率、分布分位数）。
3. 代码从冻结 `data/` 重算（允许 pandas/numpy 等标准库），不得联网获取论文数值。
4. 报告注明指标口径与局限（如 CIF 仅为样例、新颖性率无法从冻结数据重算——需 MP/AFLOW 全集对比）。

## 数据铁律提醒
- 只能用本任务冻结的真实数据（CSV/CIF/JSON），**禁止伪造或合成结构/能量数据**。
- 禁止把行号、文件名顺序等非物理信息当作特征。
- 数据 checksum 已固定（SHA-256）；报告需注明来源与许可（MIT + MP 数据条款）。