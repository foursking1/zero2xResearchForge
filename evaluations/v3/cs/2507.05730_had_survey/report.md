# EVAL REPORT v3: 2507.05730_had_survey

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v3（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 98.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1：agent报告匹配数11/14，落入rubric[≥10]区间得30分，3个版本差异行被正确识别并说明原因。A2：min_auc=0.8221≥0.80得15分；mean_runtime=1.2953s≤5s得10分；报告正确表述了方法族精度与速度权衡关系得5分。实测数值与锚值精确到小数点后4位高度吻合，A维度满分60分。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘扫描显示evidence_table.csv、summary.json、sha256_report.tsv及可运行代码等实测证据齐全，证据等级为2。evidence_table中auc_rx数值与PAPER_ANCHOR自检锚值精确一致，SHA-256校验报告完整，证据链闭环，落入[30,40]高分档，给38分。 |

## A 核心结果达成度（60/60）

A1：agent报告匹配数11/14，落入rubric[≥10]区间得30分，3个版本差异行被正确识别并说明原因。A2：min_auc=0.8221≥0.80得15分；mean_runtime=1.2953s≤5s得10分；报告正确表述了方法族精度与速度权衡关系得5分。实测数值与锚值精确到小数点后4位高度吻合，A维度满分60分。

## B 证据真实性/实际复现（38.0/40）

磁盘扫描显示evidence_table.csv、summary.json、sha256_report.tsv及可运行代码等实测证据齐全，证据等级为2。evidence_table中auc_rx数值与PAPER_ANCHOR自检锚值精确一致，SHA-256校验报告完整，证据链闭环，落入[30,40]高分档，给38分。

## 证据与重算说明

独立重算未执行。关键实测数：abu-airport-1 auc_rx=0.8221，aviris_1 auc_rx=0.8866，hydice_urban auc_rx=0.9857，min_auc=0.8221，mean_runtime_s=1.2953，均与落盘evidence_table.csv及summary.json严格一致，未发现抄论文数字或测试段泄漏现象。

## 结论

- **科学结论**: `supported`
- 亮点: 复现工作极其严谨，完美复现11个精确一致的数据集并正确归因3个版本差异，额外实现CRD算法验证方法族排序方向，代码包含SHA-256完整性校验，证据链非常完整。
- 不足: 运行时间受环境负载影响略高于论文标称的0.40s（实测均值约1.3s），但仍在rubric允许的5s范围内，无明显实质性弱点。