# EVAL REPORT v7: 1705.10450_rsi_cb256

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 99.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 33.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **60.0** | 60 | A1: 交付了完整的代码、report.md、metrics.json和evidence_table.csv，机器可读结果完整且符合TASK要求，得12分。A2: 实测细类OA 95.06%与论文锚点95.13%高度吻合，相对差<0.1%，完美支持核心claim，得33分。A3: 方法严谨，采用多任务ResNet-18，固定种子，防泄漏协议清晰，提供verify脚本和详尽的混淆/近重复分析，得15分。 |
| B 真值一致性/可验证性 | 39.0 | 40 | truth_check=matched | agent报出 overall_accuracy = 0.950569 (95.06%)，vs 论文锚点 VGG-16 测试 OA = 95.13% → 相对差约0.07%，严格吻合（在10%容差带内）；agent报出 label1_accuracy = 0.934658 作为辅助层次指标，符合论文两级标签设定；evidence_table中单类指标（如 parking lot precision 0.9426, recall 0.9829）内部计算自洽（230/244, 230/234），且整体OA 11769/12381=0.950569 与 metrics.json 严格一致。证据链完整，无抄袭锚值嫌疑。 |

## A 核心结果达成度（60.0/60 = A1 12.0 + A2 33.0 + A3 15.0）

A1: 交付了完整的代码、report.md、metrics.json和evidence_table.csv，机器可读结果完整且符合TASK要求，得12分。A2: 实测细类OA 95.06%与论文锚点95.13%高度吻合，相对差<0.1%，完美支持核心claim，得33分。A3: 方法严谨，采用多任务ResNet-18，固定种子，防泄漏协议清晰，提供verify脚本和详尽的混淆/近重复分析，得15分。

## B 真值一致性/可验证性（39.0/40）[truth_check=matched]

agent报出 overall_accuracy = 0.950569 (95.06%)，vs 论文锚点 VGG-16 测试 OA = 95.13% → 相对差约0.07%，严格吻合（在10%容差带内）；agent报出 label1_accuracy = 0.934658 作为辅助层次指标，符合论文两级标签设定；evidence_table中单类指标（如 parking lot precision 0.9426, recall 0.9829）内部计算自洽（230/244, 230/234），且整体OA 11769/12381=0.950569 与 metrics.json 严格一致。证据链完整，无抄袭锚值嫌疑。

## 证据与重算说明

独立重算未执行，但通过内部一致性校验确认实测数真实。关键实测数：label_2 OA=0.950569，label_1 acc=0.934658，macro-F1=0.939578。evidence_table包含35个细类及OVERALL行，列完整且数学逻辑自洽。

## 结论

- **科学结论**: `supported`
- **可验证性**: `matched`
- 亮点: 复现精度极高，与论文锚点几乎完全一致；对数据近重复和标签口径差异的边界讨论非常诚实且深入，证据链极其完整。
- 不足: 受限于CPU预算，主干微调仅进行了2个epoch，虽已足够支撑claim，但可能未完全释放模型潜力。