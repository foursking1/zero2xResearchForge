# 科研任务：检验「微调 MACE 模型复现分子晶体多晶型能量景观」关键论断（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2604.13897_molcryst_mlips`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：MolCryst-MLIPs: A Machine-Learned Interatomic Potentials Database for Molecular Crystals（arXiv:2604.13897, 2026）
- 领域：materials / 分子晶体 / ML 原子间势（MACE）微调

## 问题（可证伪）

论文发布 MolCryst-MLIPs：9 个分子晶体体系（Benzamide、Benzoic acid、Coumarin、Durene、Isonicotinamide、Nicotinic acid、Niacinamide、Pyrazinamide、Resorcinol）的 MACE-MH-1（omol head）微调模型与训练/验证数据集。核心论断：
1. **微调精度**：微调后跨体系平均能量 MAE=0.141 kJ·mol⁻¹·atom⁻¹、力 MAE=0.648 kJ·mol⁻¹·Å⁻¹。
2. **多晶型分辨**：在 DFT 标注的多晶型集上，只有微调模型能分辨多晶型能量景观（三个 SOTA 基础模型做不到）；体系间单体间（intermolecular）能量差 ΔE 从 Durene 0.09 kJ/mol 到 Resorcinol 4.64 kJ/mol（均值见正文）。
3. **生产可用**：NVE MD 能量守恒（漂移 ~10⁻⁷ 量级）、取向序参数（P2）与 RDF 保持结构完整性。
4. **数据库**：HF 仓库 `adamlaho/MolCryst` 发布 10 体系（含 acridine 扩展）的 train/valid h5 数据集与 10 个微调模型权重。

请基于冻结数据回答：

1. **数据统计**：解析冻结的 20 个 h5（10 体系 × {train,valid}；每个 `config_batch_*` 组含 `config_*` 子组：`positions,atomic_numbers,cell,pbc,properties/energy,properties/forces,property_weights`）。统计每体系 train/valid 构型数、原子数分布、能量/力范围。
2. **数据-论文对照**：核对 h5 内 `config_type` 字段（如多晶型/晶胞变体标注），统计与论文描述（9 体系 + acridine 扩展）的对应关系。
3. **能量/力基准（可选但加分）**：用冻结数据对至少 1 个体系训练/微调轻量势（或直接评估论文模型若可用），报告能量 MAE（kJ/mol/atom）与力 MAE（kJ/mol/Å），验证论文量级（0.141 / 0.648）。
4. **验证论文论断**：结合自身结果给出四档结论。

- 结论标签：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结）→ 物理位置 `$PAPER_BENCH_DATA_DIR`（来源/许可/逐文件 SHA-256 见 `data/SOURCE.md` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 文件：20 个 `{acridine,benzac,bzamid,coumar,durene,ehowih,nicoac,nicoam,pyrizin,resora}_{train,valid}.h5`（h5py 格式；`config_batch_*` → `config_*` → `positions/atomic_numbers/cell/pbc/properties/energy|forces/property_weights`；能量单位 eV、力 eV/Å；`config_type` 为体系标注）。
- 来源：Hugging Face 仓库 `adamlaho/MolCryst`（论文官方发布）。
- 规模：~1.18GB；h5 读取秒级；训练/微调视配置 1–10 小时（可只做数据层验证）。

## 方向提示（协议建议）

1. **读取**：`h5py.File('acridine_train.h5','r')`；顶层为 `config_batch_N` 组（每批 8 个 config）。
2. **单位**：h5 内为 eV/eV/Å；论文 MAE 为 kJ/mol/atom 与 kJ/mol/Å；换算 1 eV = 96.485 kJ/mol。
3. **构型统计**：统计总构型数/批数、原子数、能量范围；`config_type` 若为体系名则用于核对。
4. **评估（可选）**：若安装 MACE 且能加载论文权重（HF models/），直接评估 valid 集；否则训练轻量等变/描述符势作代理并声明。
5. **对照**：论文摘要（0.141 / 0.648）、正文（ΔE 0.09–4.64 kJ/mol）数值仅用于对照讨论，禁止抄作实测。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从冻结数据读取并完成统计/评估。
3. **`results/evidence_table.csv`**：至少含列 `system,split,metric,value`（构型数、能量/力统计、MAE）。
4. **`results/metrics.json`**：样本统计、各体系摘要、论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（单位换算/评估口径差异 vs 论文）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止合成/模拟数据。
- 禁止手工抄写论文数字作为「实测结果」；所有指标必须运行代码得到。
- 论文数值只能用于对照讨论。
