# EVAL REPORT v5: 2507.12295_textadbench

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 98.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 33.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **60.0** | 60 | A1: 核心交付物（report.md, evidence_table.csv, 完整代码, 结论）全部完整产出，符合任务明确要求，得12分。A2: 实测KNN=94.85%，深度最高DPAD=94.10%，完美复现了论文“KNN最高且深度方法无优势”的核心claim，数值与裁判基准完全吻合，得33分。A3: 方法严谨，严格分离train/test，包含SHA-256校验与审计重建脚本，无泄漏，可复现性极高，得15分。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘证据等级为2。虽缺失标准的metrics.json文件，但提供了等价的summary_meta.json、完整的evidence_table.csv以及29个结果JSON/CSV文件。包含verify_knn.py等checksum脚本和aggregate_from_scores.py审计脚本，证据链完整自洽，实测数值与裁判基准分毫不差，给38分。 |

## A 核心结果达成度（60.0/60 = A1 12.0 + A2 33.0 + A3 15.0）

A1: 核心交付物（report.md, evidence_table.csv, 完整代码, 结论）全部完整产出，符合任务明确要求，得12分。A2: 实测KNN=94.85%，深度最高DPAD=94.10%，完美复现了论文“KNN最高且深度方法无优势”的核心claim，数值与裁判基准完全吻合，得33分。A3: 方法严谨，严格分离train/test，包含SHA-256校验与审计重建脚本，无泄漏，可复现性极高，得15分。

## B 证据真实性/实际复现（38.0/40）

磁盘证据等级为2。虽缺失标准的metrics.json文件，但提供了等价的summary_meta.json、完整的evidence_table.csv以及29个结果JSON/CSV文件。包含verify_knn.py等checksum脚本和aggregate_from_scores.py审计脚本，证据链完整自洽，实测数值与裁判基准分毫不差，给38分。

## 证据与重算说明

独立重算未执行。关键实测数：KNN=94.85%，DPAD=94.10%，AE=93.72%，DSVDD=75.92%。证据表与逐seed JSON及运行日志严格一致，KNN结果与裁判底层pyod 3.6.4重算基准完全吻合。

## 结论

- **科学结论**: `supported`
- 亮点: 实验执行极其严谨，KNN结果与裁判底层复现基准完全吻合，5次随机种子评估与逐seed原始分数落盘体现了极高的证据可信度与审计友好性。
- 不足: 缺失标准的metrics.json文件（虽被更详细的CSV/JSON证据链弥补）；DSVDD因上游pyod版本bug导致与论文数值偏差较大，但已在报告中做出合理且准确的科学解释。