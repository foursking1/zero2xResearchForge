# Task: 2607.06645_batterymat（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

## 元信息
- task_id: `2607.06645_batterymat`
- 层级: L1（critical claim，可证伪）
- 论文: Lee, J., Campbell, C.R., Zhang, K., Choudhary, K. *BatteryMat: a hierarchical machine-learning and DFT framework for average-voltage screening of lithium-ion cathode materials.* arXiv:2607.06645 (2026).
- 领域: materials（锂离子正极平均电压筛选）

## 问题（可证伪）
论文声称：BatteryMat 三层筛选框架（ALIGNN 单次电压预测 → ALIGNN-FF 脱锂曲线 → 自动选泛函的 PBE+U / optB88-vdW+U DFT 验证）的 **DFT 验证层能把四个商用正极体系（LFP、LMP、LMO、LCO）的平均电压复现到实验值 ±0.3 V 以内**（论文数值：LFP 3.60 vs 实验 3.45；LMP 3.91 vs 4.10；LMO 4.08 vs 4.05；LCO 4.18 vs 4.05），且 **锂金属参考在同一平面波基组下重算，以消除表列参考值引入的 ~1 V 系统偏移**；代理层从 7,474 条 ALIGNN-FF 平均电压（Li 池过滤后）中筛出 **71 个候选**。

请用冻结数据独立验证以下声明，回答三个问题：

1. **从冻结的 DFT 逐步能量（energies.json）重算五个化学体系的平均电压**（凸包平衡电压；LMP 因无全脱锂端点用步进电压均值），是否与论文数值一致（LFP 3.60 / LMP 3.91 / LMO 4.08 / LCO 4.18 / NMC 4.40）？四个主体系与实验值之差是否 ≤0.3 V？
2. **代理层筛选**：从 `Li_min.csv`（7,474 条 ALIGNN-FF 电压标签）重现实用的电压筛选（论文：1 V < 平均电压 ≤ 5.5 V 且最大电压 ≤ 5.5 V），并核对 `cathode_candidates_ranked.csv` 的 71 个候选是否与该筛选一致（注意：能量凸包 ehull ≤ 0.05 eV 过滤需要 JARVIS-DFT 元数据，排名表中已含 ehull 列）；论文声称 top 候选由聚阴离子磷酸盐/氟化物主导——是否成立？
3. **锂金属参考修正**：论文给出 PBE 参考 -1.9031 eV/atom、optB88-vdW 参考 -0.9646 eV/atom（`dft_inputs/JVASP-913-Li/` 输入文件）；量化"表列参考 vs 同基组重算"对电压的系统偏移量级（论文称 ~1 V）。

## 方向提示
- **电压公式**（每移除 1 个 Li）：`V_step = E(n-1) - E(n) + e_li`（e_li 为每原子 Li 金属参考能，见各 `energies.json` 的 `e_li_metal` 字段）；步进电压均值 = 各步电压平均。
- **凸包平衡电压**：以 x = n_Li / n_li_total 为横轴、逐步总能 E(x) 为纵轴做下凸包，凸包相邻顶点间为平台，平台电压 `V = (E_a - E_b + Δn·e_li)/Δn`，平均电压按 Δx 加权（论文口径：ΔE(x) = E(x) − xE(1) − (1−x)E(0) 的下凸包，V = −dΔE/dx）。
- **泛函选择**：层状框架（R-3m、P63/mmc、C2/m、C2/c）→ optB88-vdW+U（本数据中仅 LCO/JVASP-2017，e_li=-0.9646）；3D 键合框架 → PBE+U（其余，e_li=-1.9031）。核对该映射与各 `energies.json` 的 `functional`/`layered` 字段。
- **体系对照**：LFP=JVASP-42723、LMP=JVASP-116897、LMO=JVASP-141792、NMC 变体=JVASP-144791（Li:TM=1:2 非化学计量，论文作边界案例）、LCO=JVASP-2017。
- **实验参考**（论文引用文献值）：LFP 3.45、LMP 4.10、LMO 4.05、LCO 4.05 V；NMC 变体 3.70 V（非同类对比，勿并入主结论）。
- 注意 LMP 的 `energies.json` 第 16 步（全脱锂 Mn⁴⁺）未收敛（energy=null），因此无 x=0 端点 → 不能用凸包，论文用 15 步步进均值 3.91。

## 数据说明
- 目录：`data/`（冻结，321 文件，约 10 MB）
- **来源**：论文官方仓库 https://github.com/atomgptlab/batterymat（分支 master，2026-08-13 抓取；论文 Data availability 声明）。全部文件直接复制自仓库，未做任何修改。
- **许可**：MIT License（NIST，2024；文件 `data/LICENSE_MIT.txt`）。底层 JARVIS-DFT 结构与 ALIGNN 权重分别受 NIST/JARVIS 条款约束（本包仅含作者仓库发布的中间数据与 DFT 输入，不含 JARVIS-DFT 原始结构）。
- **Checksum**：全部 321 文件 SHA-256 见 `data/CHECKSUMS_SHA256.tsv`；核心文件：
  - `Li_min.csv` 942a2b6253a133e614f331f6363f8bdaefef4588913ab5a1006b5e606b50f983
  - `cathode_candidates_ranked.csv` 2a35dd55d92c792b3f6b70274bc453cd5f73880c929611966cbb481f3e04c4df
  - `screening_cathode_analysis.md` f53bd7c5475a56824b03fef03c207e281734afe7c4a50ad93a3c75ce0f2eca21
  - `dft_inputs/JVASP-42723-LFP/supercell_2x2x1/energies.json` 5f5695096bb284d41144dbfe1b3473461b48798a8b63783ca4e4d7ad37b039ea
  - `dft_inputs/JVASP-116897-LMP/supercell_2x2x1/energies.json` 84ad7bcd62b27581a0170b2bd73a502cde5dfb03cd3ba3ca0cc2bb0d4270c4a2
  - `dft_inputs/JVASP-141792-LMO/supercell_2x2x2/energies.json` 5f9927e2b81c2100bb09941e89f9439b078fc35ffcdaeb80a0cd90a7155a03cc
  - `dft_inputs/JVASP-2017-LCO/supercell_2x2x2/energies.json` b1fb6cf11e55ec74eba46913b17289be2fda5d36210d4a35ac1fb2e449f9fec0
  - `dft_inputs/JVASP-144791-NMC/supercell_2x2x1/energies.json` f890458c950bfebc651a4b2c71b0b2f2f5e4076c6411c24bb61d6d10737ce840
- **Schema**（详见 `data/CHECKSUMS_SHA256.tsv` 与仓库 README）：
  - `Li_min.csv`：7,474 行 × 9 列（name, avg_voltage, voltage_profile, max_voltage, max_vol_cap, vol_capacity_profile, max_grav_cap, grav_capacity_profile），ALIGNN-FF 顺序脱锂平均电压标签（V）
  - `cathode_candidates_ranked.csv`：71 行候选（含 jid, ehull, optb88vdw_bandgap, formula, atoms, score）
  - `dft_inputs/<JVASP>-<ABBR>/supercell_*/energies.json`：逐脱锂步总能量（eV）+ e_li_metal + 泛函/层状标记；`step_XX_LiNN/` 含 POSCAR/INCAR/KPOINTS/POTCAR_spec
  - `dft_inputs/JVASP-913-Li/`：Li 金属参考输入（PBE 与 optB88vdW 两套）
  - `screening_cathode_analysis.md`：作者对五个体系的凸包电压/容量/实验对照分析（含文献引用）

## 输出要求
1. **结论**：对 3 个问题给出明确回答（复现 / 部分复现 / 未复现），逐体系对照论文数值与实验值。
2. **证据表**（`results/evidence_table`）：五体系重算电压 vs 论文 vs 实验（含偏差）；凸包平台数/电压；71 候选筛选核对；Li 参考修正量级。
3. **代码**：可运行脚本，从冻结 `data/` 直接重算出证据表中的关键数值（电压重算 + 筛选核对）。
4. **报告**：方法（凸包实现、筛选口径）、与论文口径差异、局限性（如 ehull 元数据缺失、NMC 边界案例）。

## 数据铁律提醒
- 只用本任务冻结的数据（全部来自论文官方仓库）；**禁止自行运行 DFT/势场生成"新数据"或伪造标签**。
- 禁止把文件顺序、行号等非物理信息当特征。
- 数据 checksum 已固定（SHA-256）；报告中注明数据来源与许可（MIT，作者仓库）。
