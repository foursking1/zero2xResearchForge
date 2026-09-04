# EVAL REPORT v5: 2205.13760_tranception_proteingym

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 33.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **60.0** | 60 | A1(12): 核心交付物完整，包含代码、evidence表、metrics和报告，正确解析了6个冻结assay并核验了方向与元数据。A2(33): 完美复现了论文“LM≥简单基线”的核心claim（5/6 assay胜出，均值0.463 vs 0.245），并对GFP反例做了科学归因，结论supported。A3(15): 方法严谨，采用masked-marginal及正确的氨基酸重整化，零样本无泄漏，代码与中间结果支持复算。 |
| B 证据真实性/实际复现 | 40 | 40 | 证据等级为2（齐全自洽）。包含完整的metrics.json、evidence_table.csv、可运行Python代码及大量中间打分CSV文件。内部数值在报告与证据表中严格一致，证据链闭环，授予满分40。 |

## A 核心结果达成度（60.0/60 = A1 12.0 + A2 33.0 + A3 15.0）

A1(12): 核心交付物完整，包含代码、evidence表、metrics和报告，正确解析了6个冻结assay并核验了方向与元数据。A2(33): 完美复现了论文“LM≥简单基线”的核心claim（5/6 assay胜出，均值0.463 vs 0.245），并对GFP反例做了科学归因，结论supported。A3(15): 方法严谨，采用masked-marginal及正确的氨基酸重整化，零样本无泄漏，代码与中间结果支持复算。

## B 证据真实性/实际复现（40/40）

证据等级为2（齐全自洽）。包含完整的metrics.json、evidence_table.csv、可运行Python代码及大量中间打分CSV文件。内部数值在报告与证据表中严格一致，证据链闭环，授予满分40。

## 证据与重算说明

独立重算未执行。关键实测数：evidence_table.csv中BRCA1_HUMAN LM_esm2_650M ρ=0.5198，GFP_AEQVI ρ=0.1079；metrics.json中对应值为0.5198288和0.107947，内部高度一致。中间结果CSV文件（如baseline_scores）证实了实际推理与打分过程。

## 结论

- **科学结论**: `supported`
- 亮点: 实验设计严谨，对GFP反例进行了深入的归因分析（多重突变+浅比对），并额外进行了joint masked-marginal校验，科学态度诚实且证据链完整。
- 不足: 受限于冻结数据包仅包含6个assay，未能覆盖论文中87个assay的全貌，且未实现带检索的Tranception模型，但已在报告中充分声明，不影响核心论断验证。