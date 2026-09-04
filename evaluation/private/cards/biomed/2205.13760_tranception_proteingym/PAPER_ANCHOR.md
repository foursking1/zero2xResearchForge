# 论文锚：2205.13760_tranception_proteingym

> 用途：LLM judge 判分基准（私有）。数值来自 arXiv:2205.13760v5（ICML 2022），禁止臆造。

## 锚清单

| # | 指标 | 论文数值 | 出处 | 定义口径 | 容差 |
|---|---|---|---|---|---|
| 1 | ProteinGym 组成 | 87 个替换 DMS assay（~1.5M 错义突变）+ 7 个 indel assay（~0.27M）；比 DeepSequence（37 assay）大 2.5× | §5 / Table 1 | 替换突变基准 | 参照锚 |
| 2 | 主论断 | Tranception w/ retrieval 在替换突变基准整体 Spearman ρ 上优于 ESM-1v、MSA Transformer、EVE 等 | §6.2 / Fig 6 | 87 assay 平均 ρ | 方向锚 |
| 3 | 浅比对优势 | 对 MSA 浅（Neff 小）的蛋白，检索增益最大；病毒与人源蛋白上增益显著 | §6.2 / Fig 7 | 方向性 | 方向 |
| 4 | 基准数据规模 | 每个 assay 为 1000-20 万+ 突变；DMS_score 越高适应度越高（统一方向） | §E.1 | 数据处理 | 精确（冻结文件核验行数/方向） |

## 备注
- 主论断：蛋白质语言模型零样本可预测突变效应；带检索/MSA 上下文的方法整体更优。
- 判分提示：agent 只需复现「LM ≥ 简单基线」的方向（7 个 assay 内多数成立）；「w/ retrieval 最优」为加分方向（本卡未冻结 Tranception 权重时不强求）。绝对 ρ 值受模型/实现影响，不强求与论文一致。
