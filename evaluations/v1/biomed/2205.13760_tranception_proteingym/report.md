# EVAL REPORT: 2205.13760_tranception_proteingym

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判（qwen3.7-max）
- 评测时间: 2026-08-19

## 总分: 83.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1（20/20）：agent 报告解析了 6 个冻结 assay（ADRB2/BLAT/BRCA1/GAL4/GFP/PTEN），核验了 DMS_score 方向（更高=更高适应度）并使用了参考文件元数据（MSA_Neff等），符合满分标准。A2（20/20）：实现了 ESM-2（650M/8M）LM 零样本评分与 BLOSUM62 简单基线，两类方法均具备，得满分。A3（20/20）：agent 报告 ESM-2 650M 在 5/6 assay 上 Spearman ρ 优于 BLOSUM62 基线（平均 0.463 vs 0.245），多数 assay 成立且整体方向与论文一致，得满分。 |
| B 证据真实性 | 8.0 | 25 | 提交物包含完整的 results/ 和 evidence/ 目录（含 evidence_table.csv, metrics.json 及中间打分 csv），内部数值高度一致（如 BRCA1 LM ρ=0.5198 与 0.519828 的微小精度差异），证明非抄数。但提交物文本证据中完全缺失 code/ 目录下的 Python 源码文件，触发 rubric 中“无代码”降档规则（0-10分），故给 8 分。独立重算未执行。 |
| C 方法与报告 | 15 | 15 | C1（5/5）：方法合理，详细说明了 masked-marginal 评分公式与 BLOSUM62 基线定义；C2（5/5）：防泄漏措施到位，明确声明零样本推理且未使用 DMS 分数训练；C3（5/5）：报告结构完整，包含方法、结果、局限（如 6/87 子集、无 MSA）及结论标签（supported）。 |

## A 核心结果达成度（60/60）

A1（20/20）：agent 报告解析了 6 个冻结 assay（ADRB2/BLAT/BRCA1/GAL4/GFP/PTEN），核验了 DMS_score 方向（更高=更高适应度）并使用了参考文件元数据（MSA_Neff等），符合满分标准。A2（20/20）：实现了 ESM-2（650M/8M）LM 零样本评分与 BLOSUM62 简单基线，两类方法均具备，得满分。A3（20/20）：agent 报告 ESM-2 650M 在 5/6 assay 上 Spearman ρ 优于 BLOSUM62 基线（平均 0.463 vs 0.245），多数 assay 成立且整体方向与论文一致，得满分。

## B 证据真实性（8.0/25）

提交物包含完整的 results/ 和 evidence/ 目录（含 evidence_table.csv, metrics.json 及中间打分 csv），内部数值高度一致（如 BRCA1 LM ρ=0.5198 与 0.519828 的微小精度差异），证明非抄数。但提交物文本证据中完全缺失 code/ 目录下的 Python 源码文件，触发 rubric 中“无代码”降档规则（0-10分），故给 8 分。独立重算未执行。

## C 方法与报告（15/15）

C1（5/5）：方法合理，详细说明了 masked-marginal 评分公式与 BLOSUM62 基线定义；C2（5/5）：防泄漏措施到位，明确声明零样本推理且未使用 DMS 分数训练；C3（5/5）：报告结构完整，包含方法、结果、局限（如 6/87 子集、无 MSA）及结论标签（supported）。

## 证据与重算说明

独立重算未执行。抽查关键实测数值：evidence_table.csv 中 BRCA1_HUMAN LM_esm2_650M ρ=0.5198，GFP_AEQVI ρ=0.1079；metrics.json 中对应值为 0.5198288 和 0.107947，内部一致。平均 ρ_LM=0.4634，基线=0.2446。因缺失代码源码无法重算核对，但中间结果文件（baseline_scores csv）存在。

## 结论

- **科学结论**: `supported`
- 亮点: 实验设计严谨，对 GFP 反例（多重突变+浅比对）进行了深入的归因分析，并额外进行了 joint masked-marginal 校验，科学态度诚实且结论可靠。
- 不足: 提交物中遗漏了 code/ 目录下的核心 Python 脚本源码，导致复现闭环在文件层面不完整，影响了证据真实性维度的得分。