# 科研任务：ProteinGym「零样本突变效应预测」关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2205.13760_tranception_proteingym`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Notin et al., "Tranception: Protein Fitness Prediction with Autoregressive Transformers and Inference-Time Retrieval", ICML 2022（arXiv:2205.13760）
- 领域：biomed / 蛋白质工程 / 突变效应（variant effect）预测

## 问题（可证伪）

论文提出 ProteinGym 基准（87 个替换突变 DMS 实验，约 150 万错义突变）并论证：**基于蛋白质语言模型的零样本突变效应预测（Spearman ρ）能有效预测实验测定的适应度；带检索（MSA 上下文）的方法（Tranception w/ retrieval）在整体上优于纯单序列语言模型（如 ESM-1v）与基于 MSA 的模型（EVE、MSA Transformer）**；在浅比对（shallow MSA）与病毒/人源蛋白上差距更明显。

请基于冻结数据回答：

1. **数据与基准**：解析冻结的 7 个 ProteinGym 替换突变 DMS assay（ADRB2/BLAT_ECOLX_Deng/BRCA1/GAL4/GFP/PTEN 等；格式 `mutant,DMS_score,DMS_score_bin`，mutant 形如 "M1I"），说明每个 assay 的突变类型与分数方向（更高 = 更高适应度）。参考文件 `ProteinGym_reference_file_substitutions.csv` 提供 Uniprot ID/物种/MSA 深度等元数据。
2. **预测方法**：实现至少 2 类零样本评分器，对每个 assay 的每个突变打分：
   - **蛋白质语言模型**（推荐：HuggingFace ESM-2 或 ESM-1v，用掩码 log-likelihood 计算突变体 vs 野生型的分数差；亦可用 Tranception 官方模型若资源允许）；
   - **基于参考序列/MSA 的基线**（如 EVmutation/位置特异性频率模型，或简单 BLOSUM62 替换分数、或仅用野生型频率的 site-independent 模型）。
3. **验证论断**：各 assay 上模型分数与 DMS_score 的 Spearman ρ；两类方法排序是否与论文整体结论一致（LM ≥ 简单基线；MSA 深时 LM 更优）？给出 7 个 assay 的 ρ 表与四档结论。

- 结论标签：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结）→ 物理位置 `$PAPER_BENCH_DATA_DIR`（来源/许可/逐文件 SHA-256 见 `data/SOURCE.md` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 文件：7 个 assay CSV（`mutant,DMS_score,DMS_score_bin`）+ `ProteinGym_reference_file_substitutions.csv`（Uniprot_ID、MSA 深度 Neff、DMS 元数据等）。
- 来源：ProteinGym 官方 GitHub（OATML-Markslab/ProteinGym）；许可：ProteinGym 数据 CC BY 4.0（官方声明），原始 DMS 来自各文献（Jones 2020、Deng 2012、Findlay 2018、Kitzman 2015、Sarkisyan 2016、Matreyek 2021）。
- 规模：~2.4MB；零样本评分需下载预训练 LM 权重（允许，非评测数据）；若资源受限可只用 2-3 个 assay（固定，声明）。

## 方向提示（协议建议）

1. **突变评分**：对每个突变（如 M1I），计算 `log p(mut) - log p(wt)` 在掩码位置的似然差（ESM-2 输出 logits；参考位置 = 野生型残基）。也可用 Tranception 的 scoring 脚本（需下载模型权重）。
2. **基线**：site-independent 模型——用参考序列各位置野生型频率（可由 MSA 估计；无 MSA 时用 BLOSUM62 替换得分）打分。
3. **评估**：每个 assay 内计算 Spearman ρ（scipy.stats.spearmanr）；报告全部 7 个 assay 的平均/中位 ρ。
4. **对照**：论文 Fig 6 / Table 3（整体 Tranception w/ retrieval > ESM-1v > EVE > 单序列基线；具体数值以论文为准）——只能对照讨论，禁止抄为实测。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从冻结数据读取并完成评分与评估。
3. **`results/evidence_table.csv`**：至少含列 `assay,uniprot_id,method,spearman_rho,n_variants`（每 assay × 每方法一行）。
4. **`results/metrics.json`**：各 assay 突变数、方法平均 ρ、排序、论文锚对照、结论标签。
5. **`report.md`**：方法（评分器/基线/掩码策略）、结果、局限（assay 子集 vs 87、模型选择、MSA 深度）。

## 数据铁律提醒

- 只使用本包冻结的 assay 数据作为评估目标；禁止合成突变或模拟 DMS 分数。
- 预训练模型权重不算「数据」，允许下载使用；但评估只能用冻结 assay 分数。
- 禁止手工抄写论文数字作为「实测结果」。
