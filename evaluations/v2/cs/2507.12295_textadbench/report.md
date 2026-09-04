# EVAL REPORT v2: 2507.12295_textadbench

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1: Agent 报告 KNN AUROC = 94.85%，锚值 93.96%，绝对差 0.89pp ≤ 3pp，命中满分带，得 30 分；A2: 深度最高 AUROC 报告为 DPAD 94.10%，锚值约 92.63%，绝对差 1.47pp ≤ 4pp，命中满分带，得 30 分。方向性校验：深度最高(94.10) < KNN(94.85)，符合 claim 且未触发惩罚。样本量 n_train=4044, n_test=1490 完全一致。所有数值均有 evidence_table.csv 与 per_seed json 落盘支撑，A 总计 60 分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘扫描显示虽缺失 metrics.json，但存在 evidence_table.csv 及 29 个结果 CSV/JSON 文件（含逐 seed 明细与审计脚本）。证据文件中的数值（KNN 94.85, DPAD 94.10 等）与 report.md/solution.md 严格一致。代码包含完整的防泄漏设计、SHA-256 校验及审计重建脚本，属于“有证据文件且数值与报告严格一致、可核对”最高档，给 40 分。 |

## A 核心结果达成度（60/60）

A1: Agent 报告 KNN AUROC = 94.85%，锚值 93.96%，绝对差 0.89pp ≤ 3pp，命中满分带，得 30 分；A2: 深度最高 AUROC 报告为 DPAD 94.10%，锚值约 92.63%，绝对差 1.47pp ≤ 4pp，命中满分带，得 30 分。方向性校验：深度最高(94.10) < KNN(94.85)，符合 claim 且未触发惩罚。样本量 n_train=4044, n_test=1490 完全一致。所有数值均有 evidence_table.csv 与 per_seed json 落盘支撑，A 总计 60 分。

## B 证据真实性/实际复现（40/40）

磁盘扫描显示虽缺失 metrics.json，但存在 evidence_table.csv 及 29 个结果 CSV/JSON 文件（含逐 seed 明细与审计脚本）。证据文件中的数值（KNN 94.85, DPAD 94.10 等）与 report.md/solution.md 严格一致。代码包含完整的防泄漏设计、SHA-256 校验及审计重建脚本，属于“有证据文件且数值与报告严格一致、可核对”最高档，给 40 分。

## 证据与重算说明

独立重算未执行。但 Agent 报告的 KNN=94.85% 与 SCORE_RUBRIC 中 pyod 3.6.4 的裁判参考重算基准分毫不差，且提供了 auroc_per_seed.json 等逐 seed 原始分数落盘，证据链极其完整，确认为真实复现而非抄袭论文数值。

## 结论

- **科学结论**: `supported`
- 亮点: 实验执行极其严谨，KNN 结果与裁判底层复现基准完全吻合，5 次随机种子评估与逐 seed 分数落盘体现了极高的证据可信度与审计友好性。
- 不足: 缺失 metrics.json 标准文件（虽被更详细的 CSV/JSON 证据链弥补）；DSVDD 因上游 pyod 版本 bug 导致与论文数值偏差较大，但已在报告中做出合理且准确的科学解释。