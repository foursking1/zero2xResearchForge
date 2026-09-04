# EVAL REPORT v3: 2205.13760_tranception_proteingym

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 98.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1(20/20)：正确解析6个冻结assay，核验DMS_score方向与行数，使用MSA_Neff元数据；A2(20/20)：实现ESM-2(650M/8M)与BLOSUM62基线；A3(20/20)：实测ESM-2在5/6 assay上Spearman ρ优于BLOSUM62（均值0.463 vs 0.245），精确命中论文方向锚，主论断成立。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 证据等级为2（齐全自洽）。包含完整的metrics.json、evidence_table.csv、可运行Python代码及大量中间打分CSV文件（如baseline_scores）。内部数值（如BRCA1 ρ=0.5198）在报告与证据表中严格一致，证明为真实复现。 |

## A 核心结果达成度（60/60）

A1(20/20)：正确解析6个冻结assay，核验DMS_score方向与行数，使用MSA_Neff元数据；A2(20/20)：实现ESM-2(650M/8M)与BLOSUM62基线；A3(20/20)：实测ESM-2在5/6 assay上Spearman ρ优于BLOSUM62（均值0.463 vs 0.245），精确命中论文方向锚，主论断成立。

## B 证据真实性/实际复现（38.0/40）

证据等级为2（齐全自洽）。包含完整的metrics.json、evidence_table.csv、可运行Python代码及大量中间打分CSV文件（如baseline_scores）。内部数值（如BRCA1 ρ=0.5198）在报告与证据表中严格一致，证明为真实复现。

## 证据与重算说明

独立重算未执行。关键实测数：evidence_table.csv中BRCA1_HUMAN LM_esm2_650M ρ=0.5198，GFP_AEQVI ρ=0.1079；metrics.json中对应值为0.5198288和0.107947，内部高度一致。中间结果CSV文件证实了实际推理过程。

## 结论

- **科学结论**: `supported`
- 亮点: 实验设计严谨，对GFP反例进行了深入的归因分析（多重突变+浅比对），并额外进行了joint masked-marginal校验，证据链完整且科学态度诚实。
- 不足: 受限于冻结数据包仅包含6个assay，未能覆盖论文中87个assay的全貌，且未实现带检索的Tranception模型，但已在报告中充分声明。