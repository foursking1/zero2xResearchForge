# EVAL REPORT v3: 2110.08733_loveda

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 33.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 25.0 | 60 | 报告mIoU=38.5%，锚值49.79%，偏差22.67%。落入10%-30%区间。因缺失metrics.json和evidence_table落盘证据，触发证据绑定规则，A取该band下限或降级至弱达成档位，且受等级1约束(A≤35)，最终给25分。 |
| B 证据真实性/实际复现 | 8.0 | 40 | metrics.json与evidence_table.csv等核心证据均缺失，仅凭代码和报告散文声称，触发空壳/关键证据缺失硬规则，B限制在[0,10]区间，给8分。 |

## A 核心结果达成度（25.0/60）

报告mIoU=38.5%，锚值49.79%，偏差22.67%。落入10%-30%区间。因缺失metrics.json和evidence_table落盘证据，触发证据绑定规则，A取该band下限或降级至弱达成档位，且受等级1约束(A≤35)，最终给25分。

## B 证据真实性/实际复现（8.0/40）

metrics.json与evidence_table.csv等核心证据均缺失，仅凭代码和报告散文声称，触发空壳/关键证据缺失硬规则，B限制在[0,10]区间，给8分。

## 证据与重算说明

独立重算未执行。关键实测数值mIoU=38.5%仅见于EVAL_REPORT散文，无metrics.json支撑；划分文件与代码存在，但核心指标无法独立核验。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 代码结构完整，包含数据解码、固定种子划分及训练流程，防泄漏逻辑严谨。
- 不足: 严重缺失metrics.json和evidence_table等核心落盘证据，导致关键指标无法独立核验，且报告缺乏每类IoU详细数据。