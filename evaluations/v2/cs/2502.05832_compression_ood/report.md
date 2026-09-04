# EVAL REPORT v2: 2502.05832_compression_ood

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 98.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1: Agent 报告 N=50 Δ=-4.11pp，N=100 Δ=-5.36pp，均满足 imbalanced < balanced 且 |Δ| ≥ 1.0pp。教师来源（从头训练VGG-16）与压缩管线（logit KD）声明清晰，且有 `results/evidence_table.csv` 落盘证据支撑。落入满分带，得 35 分。A2: Agent 报告了 N=10/50/100 三个档位，其中 N=50 和 N=100 两个主档位 12/12 重复方向完全一致（imbalanced < balanced），且 Δ ≥ 1.0pp；N=10 均值方向亦为负。提供了详细的逐类样本量表（`per_class_counts.csv`）。满足“≥2个N档全部方向一致”条件，落入满分带，得 25 分。A 总计 60 分。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘扫描显示 metrics.json、evidence_table.csv 及大量逐 run 的 metrics.json 均存在。报告中的关键数值（如 N=50 Δ=-4.11，N=100 Δ=-5.36）与 `evidence_table.csv` 和 `metrics.json` 严格一致。`eval_all.json` 提供了 36 个 checkpoint 的独立重算核验，全部 match。数据核验脚本输出 `data_verification.json` 证实 CIFAR-10 训练/测试集分布正确。无抄数或泄漏迹象。落入 [30,40] 区间，给 38 分。 |

## A 核心结果达成度（60/60）

A1: Agent 报告 N=50 Δ=-4.11pp，N=100 Δ=-5.36pp，均满足 imbalanced < balanced 且 |Δ| ≥ 1.0pp。教师来源（从头训练VGG-16）与压缩管线（logit KD）声明清晰，且有 `results/evidence_table.csv` 落盘证据支撑。落入满分带，得 35 分。A2: Agent 报告了 N=10/50/100 三个档位，其中 N=50 和 N=100 两个主档位 12/12 重复方向完全一致（imbalanced < balanced），且 Δ ≥ 1.0pp；N=10 均值方向亦为负。提供了详细的逐类样本量表（`per_class_counts.csv`）。满足“≥2个N档全部方向一致”条件，落入满分带，得 25 分。A 总计 60 分。

## B 证据真实性/实际复现（38.0/40）

磁盘扫描显示 metrics.json、evidence_table.csv 及大量逐 run 的 metrics.json 均存在。报告中的关键数值（如 N=50 Δ=-4.11，N=100 Δ=-5.36）与 `evidence_table.csv` 和 `metrics.json` 严格一致。`eval_all.json` 提供了 36 个 checkpoint 的独立重算核验，全部 match。数据核验脚本输出 `data_verification.json` 证实 CIFAR-10 训练/测试集分布正确。无抄数或泄漏迹象。落入 [30,40] 区间，给 38 分。

## 证据与重算说明

独立重算未执行（裁判侧未实际运行代码，但依据落盘的 `eval_all.json` 和 36 个独立 `metrics.json` 确认了一致性）。关键实测数：N=50 balanced 25.345 / imbalanced 21.233 (Δ=-4.112)；N=100 balanced 28.207 / imbalanced 22.852 (Δ=-5.355)。证据链完整，数值严格对应。

## 结论

- **科学结论**: `supported`
- 亮点: 实验设计严谨，提供了 36 个独立种子的完整 checkpoint 和 reeval 核验结果，证据链极其扎实；对 N=10 的噪声现象和教师口径差异导致的绝对值偏低进行了诚实且深入的机制分析。
- 不足: N=10 档位由于极端稀疏导致 2/6 重复方向反转，虽作了合理解释，但在严格意义上使得全档位无瑕疵一致略有妥协（但不影响满分带判定）。