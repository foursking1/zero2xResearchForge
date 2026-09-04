# 科研任务：检验「PDD 编码 Transformer（PST）在 MatBench 材料性质预测上的精度」关键论断（L2）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2401.15089_pst_matbench`
- 层级：L2（卡标 L2/L3→L2 题：方法复现 + 基准对照）
- 论文：Balasingham et al., "Accelerating Material Property Prediction using Generically Complete Isometry Invariants", Sci. Rep. 14, 10132 (2024)（arXiv:2401.15089）
- 领域：materials / 晶体性质预测 / 等距不变量（PDD）/ MatBench

## 问题（可证伪）

论文提出 Periodic Set Transformer（PST）：把点云距离分布（PDD，k 近邻等距不变量）作为结构表示，结合 mat2vec 原子嵌入，在 MatBench（Materials Project 属性）基准上做 5 折交叉验证回归。核心论断：
1. **PST 精度**：在 MatBench 8 个 MP 属性上 5 折 CV MAE——Formation Energy 0.032 eV/atom、Band Gap 0.210 eV、Shear Modulus 0.074 log10(GPa)、Bulk Modulus 0.056 log10(GPa)、Refractive Index 0.290、Phonon Peak 29.40 1/cm、Exfoliation Energy 31.15 meV/atom、Perovskites FE 0.030 eV/cell。
2. **优于同类 Transformer**：PST 全面优于 CrabNet（另一 Transformer；如 Formation 0.086、Band Gap 0.266）；与 GNN（coGN：Formation 0.021、Band Gap 0.156 最优）互有胜负，但训练/预测更快（预测快约 5 倍）。
3. **PDD 编码有效性**：结构信息（PDD）与组成信息（mat2vec）都必要；只用一个组分（Composition 或 PDD）精度明显下降（如 Band Gap：Composition 0.273 / PDD 0.596 / PST 0.212）。
4. **超参行为**：k（近邻数）与 collapse tolerance 影响精度（k=15、tolerance 10⁻⁴ 附近最优）；PDD 权重纳入 attention/pooling 提升精度（0.212 vs No weights 0.278 for Band Gap）。

请基于冻结数据回答：

1. **数据统计**：解析冻结的 120 个 parquet（8 属性 × 5 折 × {train,val,test}；列 `orig_idx,positions,atomic_numbers,natoms,tags,fixed,cell,pbc,y`），统计每属性每折样本数（如 dielectric 4,764 总、phonons 1,265 总、jdft2d 636 总、perovskites 1,128 总、mp_e_form 132,752 总等）。
2. **回归模型（核心）**：实现 PST 或等价 PDD 编码模型（可用 `average-minimum-distance`（amd）库计算 PDD + 轻量 Transformer/注意力模型），在 ≥3 个属性（建议 band gap、formation energy、shear modulus）上做 5 折 CV，报告 MAE（与论文 Table 1 对照）。
3. **消融（可选但加分）**：对照「仅组成（mat2vec 嵌入求和/均值）」与「仅 PDD」的 MAE，验证 PDD 编码的必要性（Band Gap：0.212 vs 0.273/0.596）。
4. **验证论文论断**：结合自身结果给出四档结论。

- 结论标签：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结）→ 物理位置 `$PAPER_BENCH_DATA_DIR`（来源/许可/逐文件 SHA-256 见 `data/SOURCE.md` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 文件：120 个 `matbench_{dataset}_fold{f}_{split}.parquet`（8 属性 × 5 折 × train/val/test）+ `README.md`。
  - 属性：`mp_e_form`（形成能 eV/atom）、`mp_gap`（带隙 eV）、`log_gvrh`（对数剪切模量 log10(GPa)）、`log_kvrh`（对数体积模量 log10(GPa)）、`dielectric`（折射率 n）、`phonons`（声子峰 1/cm）、`jdft2d`（剥离能 meV/atom）、`perovskites`（钙钛矿 FE eV/cell）。
  - parquet 列：`orig_idx,positions,atomic_numbers,natoms,tags,fixed,cell,pbc,y`（ASE 风格；`y` 为目标值）。
- 来源：Hugging Face 镜像 `nimashoghi/matbench_{dataset}_fold{f}`（MatBench 标准 5 折划分；底层 Materials Project DFT 数据）。
- 规模：~671MB；PDD 计算 + 轻量模型 CPU/GPU 数小时（可只做部分属性/折）。

## 方向提示（协议建议）

1. **PDD**：`pip install average-minimum-distance`（amd），`amd.PDD(crystal, k)`；或用简化距离直方图/邻近距离特征替代并声明。
2. **模型**：轻量 Transformer/注意力（论文 250 epoch）或简化（Ridge/GBDT on PDD 特征）作代理；固定种子，5 折 CV 与冻结划分一致。
3. **指标**：MAE（与论文 Table 1 同口径）；报告 5 折均值±std。
4. **对照**：论文 Table 1（PST/CrabNet/coGN/CrystalTwins 数值）、Table 3（消融）仅用于对照讨论，禁止抄作实测。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从冻结数据读取并完成训练与评估。
3. **`results/evidence_table.csv`**：至少含列 `dataset,fold,model,metric,value`（MAE）。
4. **`results/metrics.json`**：样本统计、各属性/模型指标、论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（模型/特征简化 vs 论文）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止合成/模拟数据。
- 禁止手工抄写论文数字作为「实测结果」；所有指标必须运行代码得到。
- 论文数值只能用于对照讨论；不同方法必须在同一划分、同一评估协议下比较。
