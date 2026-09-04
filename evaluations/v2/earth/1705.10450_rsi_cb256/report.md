# EVAL REPORT v2: 1705.10450_rsi_cb256

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | 锚值 95.13%，Agent 实测 label_2 测试 OA = 95.06% (0.950569)，相对差 d ≈ 0.07%，落入 d≤10% 满分带 (48-60)。报告了划分与种子，提供了 label_1 辅助指标 (93.47%)，并附带详细的混淆分析 (confusion_top_pairs.csv)。落盘 metrics.json 与 evidence_table.csv 数值严格支撑该结果，证据齐全，授予满分 60 分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘扫描显示 metrics.json 与 evidence_table.csv 均存在且完整。抽查 OVERALL 行 tp=11769 / test_size=12381 = 0.950569，与 metrics.json 严格一致；抽查 parking lot 类 precision/recall 计算均与表格数值完全吻合。代码、日志、多组变体证据链完整，无抄袭锚值或泄漏嫌疑，落入 [30,40] 区间，授予满分 40 分。 |

## A 核心结果达成度（60/60）

锚值 95.13%，Agent 实测 label_2 测试 OA = 95.06% (0.950569)，相对差 d ≈ 0.07%，落入 d≤10% 满分带 (48-60)。报告了划分与种子，提供了 label_1 辅助指标 (93.47%)，并附带详细的混淆分析 (confusion_top_pairs.csv)。落盘 metrics.json 与 evidence_table.csv 数值严格支撑该结果，证据齐全，授予满分 60 分。

## B 证据真实性/实际复现（40/40）

磁盘扫描显示 metrics.json 与 evidence_table.csv 均存在且完整。抽查 OVERALL 行 tp=11769 / test_size=12381 = 0.950569，与 metrics.json 严格一致；抽查 parking lot 类 precision/recall 计算均与表格数值完全吻合。代码、日志、多组变体证据链完整，无抄袭锚值或泄漏嫌疑，落入 [30,40] 区间，授予满分 40 分。

## 证据与重算说明

独立重算未执行，但通过内部一致性校验确认实测数真实。关键实测数：label_2 OA=0.950569，label_1 acc=0.934658，macro-F1=0.939578。evidence_table 包含 35 个细类及 OVERALL 行，列完整且数学逻辑自洽。

## 结论

- **科学结论**: `supported`
- 亮点: 复现精度极高（相对差<0.1%），证据链极其完整，对数据近重复和标签口径差异（35类vs42类）的边界讨论非常诚实且深入。
- 不足: 受限于 CPU 预算，主干微调仅进行了 2 个 epoch，虽已足够支撑 claim，但可能未完全释放模型潜力。