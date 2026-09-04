# Task: 2511.22885_mech_props_mlip（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

## 元信息
- task_id: `2511.22885_mech_props_mlip`
- 层级: L1（critical claim，可证伪）
- 论文: *Evaluating Mechanical Property Prediction across Material Classes using Molecular Dynamics Simulations with Universal Machine-Learned Interatomic Potentials.* arXiv:2511.22885v1 (2025-11-28)，通讯作者 J. D. Evans（Univ. Adelaide）。
- 领域: materials（MLIP × MD 力学/热属性评估）

## 问题（可证伪）
论文声称：六个通用机器学习原子间势（MLIP：MACE-1/MACE-MP-0a、MACE-2、MACE-MOF、fairchem_OMAT、fairchem_ODAC、Orb-v3）在 13 种材料（9 MOF + 4 无机）的 MD 模拟中，对体模量（KT）、热膨胀系数（αV）与热分解温度（Tdecomp）的预测**系统性低估体模量、高估热膨胀**（势能面软化），且最优三模型为 **MACE-1（平均误差 41%）、fairchem_OMAT（44%）、Orb-v3（47%）**。

请使用本任务冻结数据（论文官方 Zenodo 数据集的派生表与逐模型汇总文件）独立重算并验证该声明，回答：

1. **方向性**：六个模型是否**全部**系统性低估体模量（每模型 KT 偏差中位数 < 0）并**全部**高估热膨胀（每模型 αV 偏差中位数 > 0）？（对应论文“PES 软化”结论）
2. **模型排序**：按三指标（Bulk/CTE/Stability）平均 MAE(%)，前三名是否为 MACE-1、fairchem_OMAT、Orb-v3，且平均误差分别 ≈41/44/47%？
3. **指标级精度**：NVT 体模量 MAE 是否 ≈43.8%±6.9%；CTE MAE 是否 ≈76.2%±25.2%；三指标偏差中位数是否 ≈ −6.92 GPa / +11.38 MK⁻¹ / +18.50 K？
4. （加分）fairchem_ODAC 是否体现“任务特异精度”：总体 MAE≈66%、分解温度 MAE≈23%？CaMn7O12 例子是否成立：NPT 均值≈9.3 GPa vs NVT 均值≈197.8 GPa vs 实验 190 GPa？

## 方向提示
- **核心文件**：`data/4-data/all_metrics_deltas_from_reference.xlsx` 的 `Deltas` 表 = 215 行，每行 `Material / Method / Metric(Bulk|NTE|Stability) / Reference / Predicted / Delta / Absolute_Error / Percent_Error`（官方管线产物）。
- **聚合口径**（与论文一致）：
  - 每行 MAE% = 100×|Delta|/|Reference|；按 `Method×Metric` 分组求均值 = 每模型×每指标 MAE%。
  - 指标级平均 = 对 6 个模型的方法级 MAE% 再求均值±标准差（论文 Bulk 43.8±6.9%、CTE 76.2±25.2% 即此口径）。
  - 模型总体平均误差 = 该模型三指标 MAE% 的均值（论文 41/44/47% 即此口径）。
  - 偏差中位数：每指标全体 Delta 中位数，以及“每模型先取中位数、再对模型平均”两种口径均报告（论文 −6.92/+11.38/+18.50 接近后者；正文同时给出范围：KT −11.21~243.02、CTE −64.10~152.09、Tdecomp 200~1000）。
- **模型名映射**：orbital=Orb-v3；mace-mp-0=MACE-1（目录 `bulk_NVT/mace-1/`）；mace2.0=MACE-2（`mace-2/`）；macemof=MACE-MOF（`mace-mof/`）；fairchem_omat；fairchem_odac。
- **独立交叉核对**：用 `data/4-data/bulk_NVT/<model>/bulk_modulus_results_stress.xlsx` 的 `Bulk Modulus (GPa)` 与 Deltas 表 `Predicted`（Bulk 行）逐一对齐，确认派生表与原始汇总一致；`nte_results_ref.xlsx`（CTE）与 `stability_results.xlsx`（分解温度，忽略其中未用于论文 6 模型的 SevenNet-MF-ompa 列）同理。
- **参考值**：Deltas 表已含官方口径 `Reference` 列（体模量/CTE 参考即论文 Table 3；分解温度参考在官方管线中封顶 1000 K，CaMn7O12=550、Zr(WO4)2=1050、SiO2=1000、UiO-67=670）。聚合时直接使用该列，勿混用其他参考集。
- **口径备注**：论文在 MAE% 比较中剔除 CaMn7O12 与 Zr(WO4)2（MACE-MOF 不含 Ca/W）；冻结 Deltas 表包含这两材料（macemof 缺行）。剔除与否不改变模型排序结论，但报告需注明所用口径。
- **评估工具**：可直接用 `data/3-analysis/score_methods.py`（MAE% 聚合）与 `data/3-analysis/plot_violin.py`（偏差分布）作为参考实现；也可自行实现等价聚合。

## 数据说明
- 目录：`data/`（冻结，68 个数据/脚本文件 + LICENSE + SOURCE + CHECKSUMS，约 0.8 MB）
- **来源**：论文官方 Zenodo 记录 10.5281/zenodo.17730688（`share.zip`，13.3 GB），本包为其除 `combined_methods.npz`（13.26 GB 原始压力/体积时间序列）外的全部内容，保持官方目录结构。
- **许可**：CC-BY-4.0（Zenodo 官方元数据；`data/LICENSE_CCBY4.txt`）。使用需引用论文与 DOI。
- **Checksum**：全部文件 SHA-256 见 `data/CHECKSUMS_SHA256.tsv`（相对路径 / 字节数 / SHA-256）；核心文件 `data/4-data/all_metrics_deltas_from_reference.xlsx` 哈希见该表。
- **Schema 摘要**（详见 `data/SOURCE.md`）：
  - `4-data/all_metrics_deltas_from_reference.xlsx`：Deltas（215 行 × 8 列）+ Missing_Data（1 行）
  - `4-data/nte_results_ref.xlsx`：13 材料 × 6 模型 CTE（MK⁻¹）
  - `4-data/stability_results.xlsx`：13 材料 × 7 列分解温度（K）
  - `4-data/bulk_NVT/<model>/bulk_modulus_results_stress.xlsx`：13 材料（mace-mof 为 11）NVT 体模量（GPa）
  - `4-data/bulk_NPT/bulk_moduli_multimethod_results.npz`：NPT 体模量（GPa，per 材料 × 温度档，含 300 K）
  - `4-data/job_runtimes.tsv`：各模型效率（s atom⁻¹ step⁻¹）
  - `1-run_files/`、`2-calculate/`、`3-analysis/`、`0-Barostat_parameter/`：MD 运行 / 计算 / 分析脚本

## 输出要求
1. **结论**：对 3 个主问题（+加分项）给出明确回答（复现 / 部分复现 / 未复现），并与论文数值（方向性、41/44/47%、43.8±6.9 / 76.2±25.2、−6.92/+11.38/+18.50）逐项对比。
2. **证据表**（`results/evidence_table`）：每模型×每指标 MAE%、每模型总体平均误差与排名、三指标偏差中位数（两种口径）、方向性判定表（每模型 Bulk/NTE 中位数符号）。
3. **代码**：可运行脚本，能从冻结数据 `data/` 直接重算证据表中的关键数值（含 Predicted↔原始 xlsx 交叉核对）。
4. **报告**：聚合口径、材料筛选说明、与论文数值的偏差及可能原因（数据版本/口径差异）、局限性。

## 数据铁律提醒
- 只用本任务冻结的真实数据；**禁止自行生成/合成模拟数据、伪造或修改标签/数值**。
- 本任务是“重算验证”，不是“重跑 MD”：不需要也不应重新运行 NPT/NVT 模拟；一切结论基于冻结派生表与汇总文件。
- 报告数值必须能由冻结数据重算复现；数据 checksum 已固定（SHA-256），报告中注明数据来源与许可。