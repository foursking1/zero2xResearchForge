# EVAL REPORT v3: 1703.00121_resisc45

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v3（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 55.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 35.0 | 60 | 落盘实测关键数：10% OA=89.4462%（train_resnet18 json），20% OA=92.39%（logs20 txt）。与锚值（87.15/90.36）相对偏差分别为2.6%和2.2%，均落入d≤10%满分带（48-60）。但因缺失metrics.json与evidence_table.csv，证据等级判定为1，A受硬约束上限钳制为35分。 |
| B 证据真实性/实际复现 | 20.0 | 40 | 提交物包含完整的划分CSV、counts统计及逐epoch训练日志（JSON与TXT），证明模型真实运行且划分符合论文口径。但缺失任务强制要求的metrics.json和evidence_table.csv，且EVAL_REPORT v1与v2/v3数值严重矛盾（78.63% vs 89.45%），内部一致性受损。属『有结果文件但关键证据缺失/内部不一致』，B落入[11,29]区间，给20分。 |

## A 核心结果达成度（35.0/60）

落盘实测关键数：10% OA=89.4462%（train_resnet18 json），20% OA=92.39%（logs20 txt）。与锚值（87.15/90.36）相对偏差分别为2.6%和2.2%，均落入d≤10%满分带（48-60）。但因缺失metrics.json与evidence_table.csv，证据等级判定为1，A受硬约束上限钳制为35分。

## B 证据真实性/实际复现（20.0/40）

提交物包含完整的划分CSV、counts统计及逐epoch训练日志（JSON与TXT），证明模型真实运行且划分符合论文口径。但缺失任务强制要求的metrics.json和evidence_table.csv，且EVAL_REPORT v1与v2/v3数值严重矛盾（78.63% vs 89.45%），内部一致性受损。属『有结果文件但关键证据缺失/内部不一致』，B落入[11,29]区间，给20分。

## 证据与重算说明

独立重算未执行。关键实测数：10% best_test_oa=89.4462%（epoch 38），20% best=92.39%（epoch 30）。数据划分10%每类70/630，20%每类140/560，与论文一致。缺失metrics.json与evidence_table.csv。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 数据划分逻辑严谨，严格遵循per-class固定seed划分；训练日志详实，逐epoch记录了loss与OA，证明模型真实训练并收敛。
- 不足: 缺失核心证据文件metrics.json与evidence_table.csv导致无法核对逐类指标；多版EVAL_REPORT数值相互矛盾，严重损害证据链可信度。