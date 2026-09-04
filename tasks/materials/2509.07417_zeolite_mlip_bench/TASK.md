# Task: 2509.07417_zeolite_mlip_bench（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

## 元信息
- task_id: `2509.07417_zeolite_mlip_bench`
- 层级: L1（critical claim，可证伪）
- 论文: Ito, S., Muraoka, K., Nakayama, A. *Benchmarking Universal Interatomic Potentials on Zeolite Structures.* arXiv:2509.07417 (2025).（目标论文对本任务隐藏，仅给 claim 与数据）
- 领域: materials（沸石结构与通用势场基准）

## 问题（可证伪）
论文核心 claim：现代预训练**通用 MLIP**（CHGNet / ORB-v3 / MatterSim / eSEN-30M-OAM / PFP-v7 / EqV2）能在**沸石结构**（纯硅 229 个 IZA 拓扑 + 347 个 Cu/CHA + 1,190 个 K-OSDA/ERI）上很好复现 **DFT（PBE+D3）级相对能量**；其中 **eSEN-30M-OAM 在所有体系中表现最一致（RMSE 最小）**；而通用解析势（UFF / Dreiding / GFN-FF）与定制势（SLC / ClayFF / BSFF）误差显著更大，GFN-FF 是解析势中最好的但仍无法满足精度。

请仅用本任务冻结数据（官方 Zenodo 发布：全部结构的各势场总能量）独立复算并回答：

1. **C1（纯硅，对应论文 Table 3）**：按每 Si 归一化、以各自 α-quartz 为参考计算各势场相对能量，计算 vs DFT 相对能量的 RMSE（kJ/molSi）。复现的模型排序是否为 **eSEN(0.44) < ORB-v3(1.01) < PFP-v7(1.33) < MatterSim(1.49) < CHGNet(3.60) ≪ GFN-FF(24.44) < Dreiding(40.86) < UFF(44.55)**，且解析势 RMSE 至少比最优 MLIP 大一个数量级？
2. **C2（含客体沸石，对应论文 Table 4）**：按每原子归一化、以 DFT 最稳定结构为参考计算相对能量，计算各 MLIP vs DFT 的 RMSE（kJ/molatom）。Cu/CHA 中 eSEN 是否最小（≈0.14）、K-OSDA/ERI 中 eSEN 是否最小（≈0.02）？每个模型的 Cu/CHA RMSE 是否都大于其 ERI RMSE（论文称含过渡金属更难）？
3. **C3（定性）**：eSEN-30M-OAM 是否在三个体系（纯硅/Cu-CHA/K-OSDA-ERI）中全部取得最小或并列最小 RMSE（"最一致" claim）？

## 方向提示
- **数据**：`data/ZeoBenchmark.zip`（官方源，CC BY-NC-ND 4.0）解压后含 `Puresilica.json`（229 拓扑，含 `quartz`）、`Cu_CHA.json`（347）、`KSDA_ERI.json`（1,190）。每结构每势场键值 = 总能量（eV）；`dft` 另含 pymatgen 结构（用于数原子）。
- **模型键映射**：`chgnet`→CHGNet；`orb_v3`→ORB-v3；`mattersim`→MatterSim；`eSEN-30M-OAM`→eSEN(OMat)；`pfp`/`pfp_shifted`→PFP-v7（相对能量下二者等价，论文用修正版）；`EquiformerV2-lE4-lF100-S2EFS-OC22`→EqV2(OC22)；`gfn`/`uff`/`dreiding`→GFN-FF/UFF/Dreiding；`slc`/`clayff`/`bsff`→SLC/ClayFF/BSFF；`dft`→PBE+D3 参考。
- **相对能量定义（论文口径）**：
  - 纯硅：`rel(s) = [E(s)/nSi(s) − E(quartz)/nSi(quartz)] × 96.485`（kJ/molSi）；每个势场用自己的 α-quartz 能量做参考。RMSE 对全部拓扑（除 quartz 外；含 quartz 不影响结果）计算 vs DFT 的 rel。
  - 客体：`rel(s) = [E(s)/N(s) − E(ref)/N(ref)] × 96.485`（kJ/molatom）；`ref` = 该数据集内 DFT 每原子能量最低的结构。N(s) = 结构原子总数（可由 pymatgen sites 求和）。
  - 单位：1 eV = 96.48533212 kJ/mol。能量字段已含 D3 修正（MLIP 亦为"MLIP+D3"口径）。
- **数据完整度**：Puresilica 全部 17 个键齐全；Cu_CHA/KSDA_ERI 含 12 个键（无解析势），无缺失能量。
- **独立实现**：自行编写解析脚本（Python 即可），不得调用论文作者未随数据发布的程序。

## 数据说明
- 目录：`data/`（冻结，4 文件，约 45.8 MB 压缩包）
- **来源**：论文官方 Zenodo 发布，DOI 10.5281/zenodo.17075635（记录页 https://zenodo.org/records/17075635 ，version 1.0，2025-09-08）；即论文 Data availability 声明所指数据。
- **许可**：CC BY-NC-ND 4.0（非商业、禁止演绎）；报告中须注明来源 DOI 与许可。
- **Checksum**：`data/checksums.sha256`（zip SHA-256 = `f8214b63e39c6d3e3f84bfe6bcf7cf5c44140074de5d12de4085921131a7f3d1`）；使用前必须校验。
- **Schema**：见 `data/README.md`（键映射、单位、相对能量定义）。

## 输出要求
1. **结论**：对 C1/C2/C3 给出明确回答（复现 / 部分复现 / 未复现），并与论文数值逐项对比（Table 3/4 的 RMSE 与排序）。
2. **证据表**（`results/`）：模型 × 体系（Puresilica / Cu_CHA / KSDA_ERI）RMSE 表；纯硅模型完整排序；参考结构 id；缺失/异常处理说明。
3. **代码**：可运行脚本，能从冻结 `data/ZeoBenchmark.zip` 直接重算证据表全部数值（含解压与 checksum 校验）。
4. **报告**：相对能量定义、参考结构选择、单位换算、与论文口径的差异、局限性。

## 数据铁律提醒
- 只用本任务冻结的真实数据（官方 Zenodo 发布）；**禁止下载其他来源数据、禁止合成/伪造数据、禁止修改冻结文件**。
- 论文 Table 2（vs 实验热力学数据）需要论文 SI 中的实验值，**本任务不要求复算 Table 2**；如引用须注明不可从冻结数据复算。
- 报告中注明数据来源、许可与 checksum。