# EVAL REPORT v7: 2110.08733_loveda

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 32.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 4.0 | 12 | |
| A2 科学结论保真 | 10.0 | 33 | |
| A3 方法严谨与可复现 | 10.0 | 15 | |
| **A 合计** | **24.0** | 60 | A1：核心交付物 metrics.json、evidence_table.csv 及标准 report.md 均缺失，仅有代码和数据划分文件，核心产物缺失，给4分。A2：散文声称 mIoU=38.5%，与锚点 49.79% 偏离 22.67%，且无落盘证据支撑，受 partially_supported 结论硬上限（A2≤15）及证据绑定规则约束，给10分。A3：代码逻辑包含固定种子划分和防泄漏设计（如类别权重仅用训练集计算），方法 sound，但缺乏结果文件无法直接复算验证，给10分。 |
| B 真值一致性/可验证性 | 8.0 | 40 | truth_check=unverified | Agent数：mIoU = 38.5%（来源：EVAL_REPORT 散文声称） vs 锚点 Y：mIoU = 49.79%（来源：PAPER_ANCHOR.md，HRNet W32） → 偏离（相对差 22.67%）。由于缺失 metrics.json 和 evidence_table.csv，该数值无法通过机器可读证据验证，判定为 unverified，B 维度严格限制在低分区间，给8分。 |

## A 核心结果达成度（24.0/60 = A1 4.0 + A2 10.0 + A3 10.0）

A1：核心交付物 metrics.json、evidence_table.csv 及标准 report.md 均缺失，仅有代码和数据划分文件，核心产物缺失，给4分。A2：散文声称 mIoU=38.5%，与锚点 49.79% 偏离 22.67%，且无落盘证据支撑，受 partially_supported 结论硬上限（A2≤15）及证据绑定规则约束，给10分。A3：代码逻辑包含固定种子划分和防泄漏设计（如类别权重仅用训练集计算），方法 sound，但缺乏结果文件无法直接复算验证，给10分。

## B 真值一致性/可验证性（8.0/40）[truth_check=unverified]

Agent数：mIoU = 38.5%（来源：EVAL_REPORT 散文声称） vs 锚点 Y：mIoU = 49.79%（来源：PAPER_ANCHOR.md，HRNet W32） → 偏离（相对差 22.67%）。由于缺失 metrics.json 和 evidence_table.csv，该数值无法通过机器可读证据验证，判定为 unverified，B 维度严格限制在低分区间，给8分。

## 证据与重算说明

独立重算未执行。关键实测数值 mIoU=38.5% 仅见于 EVAL_REPORT 散文，无 metrics.json 或 evidence_table.csv 支撑；训练集478样本、验证集84样本的划分文件（seed=2026）存在，但核心指标无法独立核验。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `unverified`
- 亮点: 代码结构完整，包含数据解码、固定种子划分及训练流程，防泄漏逻辑严谨。
- 不足: 严重缺失核心证据文件（metrics.json、evidence_table.csv）和标准报告，导致关键指标无法独立核验，未生成任务要求的标准交付物。