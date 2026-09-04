# report.md — ProteinGym 零样本突变效应预测关键论断验证

- **task_id**：`2205.13760_tranception_proteingym`
- **论文**：Notin et al., *Tranception: Protein Fitness Prediction with Autoregressive Transformers and Inference-Time Retrieval*, ICML 2022 (arXiv:2205.13760)
- **范围**：冻结数据包中 6 个替换突变（substitution）DMS assay，共 71,625 个变异（v.s. 论文的 87 assay / ~1.5M variants，子集验证）。

---

## 1. 数据与基准（对应 A1）

### 1.1 冻结数据核验
6 个 assay CSV（`mutant,DMS_score,DMS_score_bin`）逐行解析，全部通过"位置映射一致性"检验（每个 mutant 的野生型残基与参考序列 `target_seq` 在对应 1-indexed 位置 100% 匹配）。原始文件行数（含表头）/变体数：ADRB2 7,801/7,800；BLAT 4,997/4,996；BRCA1 1,838/1,837；GAL4 1,196/1,195；GFP 51,715/51,714；PTEN 5,084/5,083。

| DMS assay | UniProt | taxon | seq_len | n_variants | n_single | n_multi | mutation 形式 | DMS_score 范围 | 方向 |
|---|---|---|---|---|---|---|---|---|---|
| ADRB2_HUMAN_Jones_2020 | ADRB2_HUMAN | Human | 413 | 7,800 | 7,800 | 0 | `M1I` 单点 | [0.02, 6.93] | + |
| BLAT_ECOLX_Deng_2012 | BLAT_ECOLX | Prokaryote | 286 | 4,996 | 4,996 | 0 | 单点 | [-6.06, 2.46] | + |
| BRCA1_HUMAN_Findlay_2018 | BRCA1_HUMAN | Human | 1,863 | 1,837 | 1,837 | 0 | 单点（RING 区） | [-3.72, 1.31] | + |
| GAL4_YEAST_Kitzman_2015 | GAL4_YEAST | Eukaryote | 881 | 1,195 | 1,195 | 0 | 单点（DNA 结合域） | [-15.55, 5.16] | + |
| GFP_AEQVI_Sarkisyan_2016 | GFP_AEQVI | Eukaryote | 238 | 51,714 | 1,084 | 50,630 | `K3R:V55A:...` 多点 | [1.28, 4.12] | + |
| PTEN_HUMAN_Matreyek_2021 | PTEN_HUMAN | Human | 403 | 5,083 | 5,083 | 0 | 单点 | [-0.28, 1.67] | + |

**分数方向**：ProteinGym 处理后的 DMS_score 统一为「越高 = 适应度越高」；冻结文件核验 `DMS_score_bin ∈ {0,1}` 时 bin=1 的均值显著更高（6/6 assay），与 `raw_DMS_directionality` 处理一致。

**参考文件元数据使用**：`ProteinGym_reference_file_substitutions.csv` 提供 UniProt ID、taxon、`MSA_N_eff`（比对深度）、`MSA_Neff_L_category`（shallow/medium/high）、raw directionality 等（见 `results/metrics.json` 与 `results/exploration_summary.json`）。

### 1.2 打分位置约定
mutant 位置是相对参考文件 `target_seq` 的 1-indexed 编号；序列对比核验 100% 匹配后按该编号打分。

---

## 2. 预测方法（对应 A2）

全部为**零样本**、无训练、无泄漏（从未利用 DMS_score）。

### 2.1 蛋白质语言模型（主评分类）
- 模型：HuggingFace **facebook/esm2_t33_650M_UR50D**（主）、**esm2_t6_8M_UR50D**（小模型/容量消融）、**esm2_t33_650M joint**（GFP 校验）。
- 评分（掩码边际 masked-marginal）：
  1. 对每条 `target_seq`（全长）逐位置构建表 `L[p][a] = log P(a | x_p=<mask>, 其余=WT)`，softmax 在 20 个标准氨基酸上重整化（ProteinGym/ESM 约定）；
  2. 变异得分 `score = Σ_i ( L[p_i][mut_i] − L[p_i][wt_i] )`（site-independent log-odds；单点精确，多点近似）；
  3. 注意：必须用 tokenizer 实际词表取 20 AA 的 logit 列（ESM-2 词表非字母序），否则结果失真（我们在校正前后做了自检：WT rank 1/20、各 assay ρ 从 ~0 恢复到 0.4–0.7）。
- 实现：batch 化，fp16 GPU 推理；详见 `code/01_score_lm.py`。

### 2.2 非 LM 基线
- `baseline_blosum62`：site-independent 替换 log-odds 分，`score=Σ_i BLOSUM62[wt_i,mut_i]`（标准 20×20 BLOSUM62 矩阵，代码内程序化校验）。
- `baseline_blosum62_norm`：BLOSUM62 按位置 z 标准化（稳健性对照）。
- `baseline_null`：固定种子均匀随机（下限自检，期望 ρ≈0）。

### 2.3 附加：GFP 多重突变的联合掩码
多点变异中存在约 4.7 万种互不相同的"掩码模式"（joint masking = 一次前向把所有突变位点同时 mask）。对 GFP 用 650M 跑完整 joint masked-marginal（46,942 masks, 184 batches），作为独立位点近似的保真校验。

---

## 3. 结果（对应 A3 / 主论断验证）

### 3.1 各 assay × 方法 Spearman ρ（`results/evidence_table.csv` 全表）

| assay | ESM-2 650M | ESM-2 8M | BLOSUM62 | BLOSUM62-norm | null |
|---|---|---|---|---|---|
| ADRB2_HUMAN_Jones_2020 | **0.492** | 0.408 | 0.191 | 0.159 | -0.012 |
| BLAT_ECOLX_Deng_2012 | **0.528** | 0.243 | 0.306 | 0.255 | 0.022 |
| BRCA1_HUMAN_Findlay_2018 | **0.520** | 0.128 | 0.270 | 0.246 | -0.033 |
| GAL4_YEAST_Kitzman_2015 | **0.667** | 0.340 | 0.145 | 0.106 | 0.007 |
| GFP_AEQVI_Sarkisyan_2016 | 0.108 | 0.078 | **0.339** | 0.041 | 0.004 |
| PTEN_HUMAN_Matreyek_2021 | **0.465** | 0.165 | 0.217 | 0.178 | 0.007 |
| **mean** | **0.463** | 0.227 | **0.245** | 0.164 | −0.001 |

所有 LM 与基线（除 null 外）ρ 均显著 >0（p < 1e-5，样本量大）。

### 3.2 主论断判定
- **ESM-2 650M ρ ≥ BLOSUM62 ρ 在 5/6 assay 成立**（GAL4、BLAT、BRCA1、ADRB2、PTEN 胜；GFP 败）。
- 平均 ρ 提升 +0.219（0.463 vs 0.245）；paired 差经 Wilcoxon signed-rank p=0.094、6 样本下为**方向性支持**。
- 模型规模缩放符合论文（"bigger LLMs better"）：650M (0.463) > 8M (0.227)，且 8M 平均仅与 BLOSUM62 相当。
- 噪声下限自检通过：null ρ≈0。
- 论文锚对照（只作定性，不抄数值）：论文 Fig.6 整体顺序 Tranception w/ retrieval > ESM-1v > 单序列 LM > site-independent 基线——我们的单序列 LM 远胜 BLOSUM62 基线的**方向**一致。

**结论（四档）**：`supported`。
> 零样本蛋白语言模型能有效预测实验适应度，且在多数 assay 上系统性优于 site-independent 基线——主论断成立。

### 3.3 GFP 反例分析（诚实披露）
- GFP 是唯一 LM 输给 BLOSUM62 的 assay，且输面大（0.108 vs 0.339）。
- 原因诊断：
  1. assay 结构：51,714 变体中 **50,630 是多重突变**（7 轮组合式亮度/稳定性筛选），只有 1,084 个单点；多重突变体的累积效应近似被 additive BLOSUM62 的求和更平滑地映射；
  2. 浅比对：参考 MSA N_eff=14.9（category=low），是所有 assay 中最浅，单序列 LM 的演化先验在该折叠上判别力弱；
  3. 精确性：即使在单点子集内，ESM-2 650M 的 within-position 平均 ρ 也只有 0.08–0.10，而其余 assay 为 0.26–0.43；
  4. 联合掩码（joint masked-marginal）ρ=0.094，与独立位点近似（0.108）一致，排除了"独立位点近似"这一实现细节造成的偏差。
- 论文 Fig.6 中 GFP 也属困难例（浅比对），故单独此反例不推翻全貌，但构成「部分支持」的风险点——我们选择 supported 时已将此点在 claim.md 中声明。

### 3.4 与 MSA 深度/物种的关系（论文锚 3）
- 检索增益（Tranception w/ retrieval 的优势）主要发生在浅比对（Neff 小）与病毒/人源蛋白。本次冻结的 6 个 assay 中无病毒蛋白，且**未冻结 MSA 文件**，无法训练 MSA 深度模型（EVE/MSA-Transformer）或运行带检索的 Tranception。因此对该锚做**定性**讨论：N_eff 低的 GFP 恰恰是单序列 LM 表现最差的 assay（0.108），符合论文"浅比对 + 检索/MSA上下文最能补强"的叙事；MSA 深（BLAT N_eff=47605）时 BLOSUM62 基线已可到 0.31。

---

## 4. 局限

1. **子集**：仅 6/87 替换 assay（该数据包仅冻结 6 个）；无 indel assay。
2. **模型**：用 ESM-2（650M/8M）而非 Tranception/ESM-1v；论文主模型为 Tranception w/ retrieval（autoregressive + MSA 检索）。绝对 ρ 值与论文 Tranception-ESM-1v 不同属正常，方向性结论不受影响。
3. **无 MSA**：EVE / MSA Transformer / Tranception-retrieval / EVmutation 频率模型因缺 MSA 未实现；BLOSUM62 作为"简单基线"代理。
4. **多点近似**：GFP 多重突变按独立位点求和研究（joint 校验 ρ 差异 <0.02，稳健）。
5. **统计功效**：6 个 pair 上差显著性好但非 0.05 水平显著（Wilcoxon p=0.094）；属小样本下的方向性证据。
6. **GPU 共享环境**：与其他任务并行，耗时波动不影响结果确定性。

---

## 5. 复现

见 `README.md`。一键流程：
```bash
pip install torch pandas numpy scipy transformers huggingface_hub     # 环境（transformers==4.45.0, hf_hub<=0.36; 网络可用时自动下载 ESM-2 权重）
python code/00_explore_data.py        # 数据核验 -> results/exploration_summary.json
python code/02_score_baselines.py     # 基线评分 -> results/baseline_scores/
python code/01_score_lm.py --mode tables --models esm2_t33_650M,esm2_t6_8M --device cuda|auto
python code/01_score_lm.py --mode joint --models esm2_t33_650M --assays GFP_AEQVI_Sarkisyan_2016 # GFP 保真校验
python code/03_evaluate.py            # Spearman -> results/evidence_table.csv, results/metrics.json
python code/04_make_figures.py        # 图 -> results/figures/
```
固定种子（null 基线 rng seed=1234）；评分与评估全部确定性。

## 6. 产物清单
- `claim.md` — 结论标签与关键数字
- `code/` — 00_explore_data, 01_score_lm, 02_score_baselines, 03_evaluate, 04_make_figures, common
- `results/evidence_table.csv` — 列 `assay,uniprot_id,method,spearman_rho,n_variants`（每 assay × 每方法）
- `results/metrics.json` — 每 assay 变异数/单点多点/within-position ρ/各方法 ρ、方法聚合、排序、论文锚对照、结论标签
- `results/lm_scores/**`、`results/baseline_scores/**` — 逐变异分数（中间数据）
- `results/figures/*.png` — ρ 对比、代表性散点、MSA 深度分析
- `solution.md` — 方法/结果速览