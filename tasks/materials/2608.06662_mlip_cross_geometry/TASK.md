# Task: 2608.06662_mlip_cross_geometry（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

## 元信息
- task_id: `2608.06662_mlip_cross_geometry`
- 层级: L1（critical claim，可证伪；卡标 L2 → 按 L1 造题）
- 论文: *Cross-Geometry Transferability Assessment of Universal Machine Learning Interatomic Potentials: From Bulk Materials to Atomic Nanowires.* arXiv:2608.06662v1，Zanineli, Focassio & Schleder（LNNano/CNPEM & UFABC）。
- 领域: materials（通用 ML 原子间势 × 跨几何迁移零样本评估）

## 问题（可证伪）
论文声称：在自建 ZrO2 DFT 数据集（体相 bulk / 表面 slab / 颗粒 particle / 颈 neck / 原子线 wire 五类几何环境）上，26 个预训练通用 MLIP 的**零样本**预测（不做任何训练，仅做参考能量对齐）呈现**明显的几何依赖退化**：最佳模型 **ORB-V3** 的全局能量/力 RMSE 为 **6 meV/atom 与 197.3 meV/Å**，且**最大力误差出现在 neck 与 wire 配置**；26 个模型的平均误差约 **20 meV/atom 与 400 meV/Å**；MP-NC 组（训练数据超出 Materials Project 许可范围的模型）整体误差低于 MP-C 组（MP 合规模型），MP-C 组最佳 ORB-V2-MPtrj 为 **107.67 meV/atom 与 309.1 meV/Å**。

请使用本任务冻结的官方 ZrO2 数据集（extended XYZ，含 DFT 能量/力/应力参考），对至少一个（理想多个）论文 26 模型清单中的预训练通用 MLIP 做零样本单点推理，独立重算并验证该声明，回答：

1. **几何依赖方向**：随配位降低（bulk → slab → particle/wire/neck），能量与力误差是否系统性上升？**neck 与 wire 的力误差是否最大**、bulk/slab 是否最小？
2. **关键数值**：对可用最佳模型（首选 ORB-V3），参考能量对齐后的全局能量 RMSE 与力 RMSE 是否 ≈ **6 meV/atom / 197.3 meV/Å**（论文报告值）？
3. **模型分组与均值**：若运行多个模型——全体模型平均误差是否 ≈ 20 meV/atom / 400 meV/Å；MP-NC 组整体是否低于 MP-C 组；MP-C 组最佳是否为 ORB-V2-MPtrj（107.67 / 309.1）？
4. （加分，B 组方向）微调（fine-tuning）是否优于 from-scratch 训练（同 epoch、墙钟时间相当）？几何特化微调是否出现负迁移（如 wire-only 微调提高其他几何误差）？

## 方向提示
- **数据**：`data/ZrO2/` 五类共 **35 个多帧 extended XYZ**（14,434 帧：bulk 94 / slab 3,073 / particle 838 / neck 4,000 / wire 6,429）+ `README.md`。每帧第二行为 key-value 头：`Lattice=...`、`Properties=species:S:1:pos:R:3:forces:R:3`、`energy=`（eV，整帧总能量）、可选 `stress=`（kBar）与 `pbc=`。数据为 DFT（VASP）参考；`neck` 与 `wire` 为轨迹（逐帧构型）。
- **零样本协议（与论文 Sec II.B / III.B 一致）**：
  - 对冻结全部帧做单点（single-point）推理，不做结构弛豫/重训练；
  - **参考能量对齐**：对每个模型拟合元素级能量偏移（{Δµ_Zr, Δµ_O} = argmin Σ_i (E_DFT,i − E_model,i − Σ_α N_iα Δµ_α)²，最小二乘），只偏移能量、**不偏移力**；
  - **论文未随数据发布训练/验证/测试划分标签**（正文为几何分层划分、力过滤后约 72/18/10），因此需要**自行定义并明确报告对齐参考集**（例如全部 14,434 帧，或带种子的显式划分），并与论文数值的差异做归因。
- **指标口径**：每原子能量 RMSE（meV/atom，对齐后）；力 RMSE（meV/Å，对全部原子×3 分量）。
- **模型获取**：首选 ORB-V3（`orb-models` PyPI 包 / HuggingFace `orb-v3`）；也可用论文 26 模型清单中任一带公开权重的模型（MACE-MP-0、MACE-MPA-0、SevenNet-MF-ompa、MatterSim、GRACE、DPA3-v2、CHGNet 等）。**权重许可需在下载时自行核对**（ORB 类模型权重含 MatBench/榜单评测限制；本任务为学术复现，仅用于在作者公开发布的数据上重算误差）。
- **计算预算**：全量 14,434 帧单点推理在消费级 GPU 上可行（neck/wire 为大轨迹）；资源受限时可按几何类随机子采样（固定随机种子并报告采样比例与每类帧数），但方向性判据应基于一致的采样协议。
- **输出证据**：务必提交**逐结构误差表**（`results/per_structure_errors.csv`：geometry/file/frame/n_atoms/E_DFT/E_model/force_rmse_per_atom），供裁判从冻结数据独立重算核查。

## 数据说明
- 目录：`data/`（冻结，36 个文件：35 个 xyz + README.md + checksums.sha256 + DATA_SOURCES.md，解压后约 81.5 MB）。
- **来源**：论文官方 Zenodo 记录 **10.5281/zenodo.21829037**（文件 `ZrO2.zip`，18,732,610 字节，zip SHA-256 `dc935b91c35d9a13c5030e339901a5718ceb9b6e5c953da4b3ac0524ad28ed4d`）。下载地址：`https://zenodo.org/records/21829037`（文件直链 `https://zenodo.org/api/records/21829037/files/ZrO2.zip/content`）。
- **许可**：**CC-BY-4.0**（Zenodo 官方记录元数据）。使用需引用论文与 DOI。
- **Checksum**：逐文件 SHA-256 见 `data/checksums.sha256`；原始 zip 的 SHA-256 见 `data/DATA_SOURCES.md`。
- **Schema 摘要**（详见 `data/DATA_SOURCES.md`）：35 个多帧 extended XYZ；`ZrO2/bulk/`（5 文件、94 帧）、`ZrO2/slab/`（12、3,073）、`ZrO2/particle/`（3、838）、`ZrO2/neck/`（2、4,000）、`ZrO2/wire/`（13、6,429）。

## 输出要求
1. **结论**：对主问题 1–3（+加分项 4）给出明确回答（复现 / 部分复现 / 未复现），与论文数值逐项对比；若某个锚因模型权重不可得而无法验证，须明确标注并说明对结论的影响。
2. **证据表**（`results/evidence_table`）：逐几何类能量/力 RMSE；可用最佳模型全局对齐后能量/力 RMSE 与论文 6/197.3 对照；若运行多模型：全体模型均值（≈20/400）、MP-NC vs MP-C 分组均值、MP-C 组最佳模型。
3. **逐结构误差表**（`results/per_structure_errors.csv`）：geometry/file/frame/n_atoms/E_DFT/E_model/force_rmse_per_atom。
4. **代码**：可运行脚本，能从冻结数据 `data/` + 提交的逐结构误差表直接重算证据表关键数值（模型推理脚本与聚合脚本分开给出）。
5. **报告**：模型与 checkpoint 清单、对齐协议（参考集定义、拟合方法）、误差口径、与论文差异归因（对齐参考集未发布 / 采样 / 模型版本）、局限性。

## 数据铁律提醒
- 只用本任务冻结的真实 DFT 数据；**禁止自行生成/合成模拟数据、伪造或修改标签/数值**。
- 模型预测必须来自真实权重推理（零样本），不得硬编码论文数值冒充复现结果。
- 报告数值必须能由冻结数据 + 提交的逐结构误差表重算复现；数据 checksum 已固定（SHA-256），报告中注明数据来源与许可。