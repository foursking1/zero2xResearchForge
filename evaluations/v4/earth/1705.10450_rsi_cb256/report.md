# EVAL REPORT v3: 1705.10450_rsi_cb256

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | Agent 报告 label_2 测试 OA = 95.06% (0.950569)，论文锚值为 95.13%。相对偏差 d ≈ 0.076%，严格落入 ≤2% 的精确命中区间。落盘 metrics.json 与 evidence_table.csv 完整支撑该数值，依据梯度化规则授予满分 60 分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示证据等级为 2（齐全自洽）。metrics.json 与 evidence_table.csv 均存在且完整，内部数学逻辑严格自洽（如 OVERALL 行 tp=11769 / test_size=12381 = 0.950569，单类 precision/recall 计算均吻合），并提供 verify 脚本与多组变体证据，授予满分 40 分。 |

## A 核心结果达成度（60/60）

Agent 报告 label_2 测试 OA = 95.06% (0.950569)，论文锚值为 95.13%。相对偏差 d ≈ 0.076%，严格落入 ≤2% 的精确命中区间。落盘 metrics.json 与 evidence_table.csv 完整支撑该数值，依据梯度化规则授予满分 60 分。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示证据等级为 2（齐全自洽）。metrics.json 与 evidence_table.csv 均存在且完整，内部数学逻辑严格自洽（如 OVERALL 行 tp=11769 / test_size=12381 = 0.950569，单类 precision/recall 计算均吻合），并提供 verify 脚本与多组变体证据，授予满分 40 分。

## 证据与重算说明

独立重算未执行，但通过内部一致性校验确认实测数真实。关键实测数：label_2 OA=0.950569，label_1 acc=0.934658，macro-F1=0.939578。evidence_table 包含 35 个细类及 OVERALL 行，列完整且数学逻辑自洽。

## 结论

- **科学结论**: `supported`
- 亮点: 复现精度极高（相对偏差<0.1%），证据链极其完整且内部数值严格自洽，对数据近重复和标签口径差异的边界讨论非常诚实且深入。
- 不足: 受限于 CPU 预算，主干微调仅进行了 2 个 epoch，虽已足够支撑 claim，但可能未完全释放模型潜力。