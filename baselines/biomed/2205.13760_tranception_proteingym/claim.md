# claim.md — 关键论断判定（L1）

**task_id**：`2205.13760_tranception_proteingym`
**被测论断**（Notin et al., Tranception, ICML 2022 / ProteinGym）：
> 蛋白质语言模型的**零样本**突变效应预测（Spearman ρ ≤> DMS_score）能有效预测实验适应度，且（基于单序列 masked-LM 的）LM 类评分器在大多数拼装 assay 上优于简单、无信息的 site-independent 基线（如 BLOSUM62 / 位置频率型）。

## 结论标签：`supported`

判定依据（冻结的 6 个替换突变 assay，全部 71,625 个变异，未用任何 DMS 数据训练）：

| 指标 | 实测 |
|---|---|
| 主 LM（ESM-2 650M 掩码边际）平均 ρ | **0.463** |
| 简单基线（BLOSUM62 site-independent）平均 ρ | **0.245** |
| LM 胜出的 assay 数 / 总数 | **5 / 6**（GAL4 0.667, BLAT 0.528, BRCA1 0.520, ADRB2 0.492, PTEN 0.465 胜；GFP 输） |
| 平均 Δρ（LM − 基线） | +0.219 |
| 小 LM（ESM-2 8M）平均 ρ | 0.227（能力缩放符合论文「更大 LM 更好」） |
| 基线自检 | 噪声 null 基线 ρ≈0（−0.0008） |

**方向与论文一致**：单序列蛋白 LMs 零样本预测与 DMS 适应度显著正相关（除 GFP），并在 5/6 assay 上稳定胜过 BLOSUM62 基线；平均提升约 0.22（Wilcoxon signed-rank p=0.09，6 个小样本下为方向性支持）。

**四档说明（supported/partially_supported/contradicted/inconclusive）**：
选了 **supported**。A3 判分规则为「LM ρ ≥ 基线 ρ 在多数 assay 成立（→满分）」。ESM-2 650M 在 5/6 assay 满足，均值差为正且幅度大，与论文整体方向一致。

**已知不一致项（诚实披露）**：
- **GFP_AEQVI_Sarkisyan_2016**：ESM-2 650M ρ=0.108 < BLOSUM62 ρ=0.339。原因分析见 report：该 assay 以**多重突变**为主（50,630/51,714），且为浅比对（MSA N_eff=14.9, category=low）。GFP 多重突变体的独立位点 log-odds 与成像/折叠表型的对齐弱；连 joint masked-marginal（ρ=0.094）也不随希望改进。此单一反例不推翻整体结论，论文 Fig.6 也显示 GFP 属难例。
- 未复现「检索/MSA 上下文」加分方向（无冻结 MSA、无 Tranception 权重），本卡不强求。

**无泄漏声明**：所有评分均为零样本/预训练权重推理；未用任何 DMS_score 拟合任何参数；评估只使用冻结 assay 数据。

**关键产物**：`code/`（00–04）、`results/evidence_table.csv`、`results/metrics.json`、`report.md`。