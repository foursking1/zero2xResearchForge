# EVAL REPORT v5: 2607.18127_cloudens

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 93.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 28.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **55.0** | 60 | A1：核心交付物完整产出，包含完整的训练/评估脚本、evidence_table、详细报告及验证运行结果。A2：完美复现了论文的核心效应（ClouDens NAB 显著优于 GRU，两 profile 比值均>1.3），数值落入合理容差带（偏差约17-19%），但逐点TP/FP未严格优于基线，故略扣分。A3：方法严谨，防泄漏措施完备，数据划分与预处理严格遵循论文协议，且提供batch16交叉验证证明管线无误。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 证据等级2（齐全自洽）。虽无标准metrics.json，但提供了meta_*.json、data_facts.json、完整的grid CSV及evidence_table，且包含batch16的验证运行精确复现GRU锚值，证据链极其扎实，内部数值严格自洽。 |

## A 核心结果达成度（55.0/60 = A1 12.0 + A2 28.0 + A3 15.0）

A1：核心交付物完整产出，包含完整的训练/评估脚本、evidence_table、详细报告及验证运行结果。A2：完美复现了论文的核心效应（ClouDens NAB 显著优于 GRU，两 profile 比值均>1.3），数值落入合理容差带（偏差约17-19%），但逐点TP/FP未严格优于基线，故略扣分。A3：方法严谨，防泄漏措施完备，数据划分与预处理严格遵循论文协议，且提供batch16交叉验证证明管线无误。

## B 证据真实性/实际复现（38.0/40）

证据等级2（齐全自洽）。虽无标准metrics.json，但提供了meta_*.json、data_facts.json、完整的grid CSV及evidence_table，且包含batch16的验证运行精确复现GRU锚值，证据链极其扎实，内部数值严格自洽。

## 证据与重算说明

独立重算未执行。关键实测数：data_facts确认39365行/2406特征/26488测试点；evidence_table中MD 99.8 ClouDens NAB Standard=16.84, LowFN=21.76；validation_batch16中GRU MD NAB Standard=5.89（与论文锚值绝对差<0.01）。

## 结论

- **科学结论**: `supported`
- 亮点: 代码管线完整且提供了batch16的交叉验证，精确复现了论文GRU基线数值，极大增强了证据可信度；对局限性和batch敏感性的分析非常诚实且深入。
- 不足: 主运行（batch 32）下ClouDens的逐点TP/FP未能严格优于GRU基线（14/39 vs 15/38），导致检测质量的次要claim仅部分成立。