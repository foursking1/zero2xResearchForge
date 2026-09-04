# EVAL REPORT v2: 1703.00121_resisc45

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（deepseek-v4-flash）
- 评测时间: 2026-08-21

## 总分: 60.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 48.0 | 60 | A维度按实际落盘证据判定：10%训练比例实测OA=89.4462%（train_resnet18_r0.10_s20260813.json中的best_test_oa，best_epoch=38），20%训练比例实测OA=92.39%（logs20_s20260813.txt中best@30）。两项均落入满分带（d≤10%：10%相对差=(89.4462-87.15)/87.15=2.64%≤10%；20%相对差=(92.39-90.36)/90.36=2.25%≤10%），基础分应取band下限48。但任务要求提交的submission/results/metrics.json与evidence_table.csv均缺失，触发证据绑定限制，A不能取band上限或附加分，故A=48（不额外扣除20%未报告，因20%OA实际有落盘log支撑；但若视该log为有效实测证据，则两比例均已报告）。结论词与实测数据一致（均超锚值），不扣结论词矛盾分。 |
| B 证据真实性/实际复现 | 12.0 | 40 | 磁盘扫描确认metrics.json与evidence_table.csv缺失，属『产生了文件但未真实复现』，触发B∈[0,15]硬规则。虽有train_resnet18_r0.10_s20260813.json及logs10/logs20训练日志证明模型确实运行并产生逐epoch实测OA，但任务要求的核心证据文件（metrics.json、evidence_table.csv）未落盘，且两份EVAL_REPORT散文数值相互矛盾（v1声称10%OA=78.63%，v2声称10%OA=89.45%），证据链不完整。按分层规则，有证据文件但关键指标文件缺失、报告数值不一致，B给12分（∈[0,15]）。 |

## A 核心结果达成度（48.0/60）

A维度按实际落盘证据判定：10%训练比例实测OA=89.4462%（train_resnet18_r0.10_s20260813.json中的best_test_oa，best_epoch=38），20%训练比例实测OA=92.39%（logs20_s20260813.txt中best@30）。两项均落入满分带（d≤10%：10%相对差=(89.4462-87.15)/87.15=2.64%≤10%；20%相对差=(92.39-90.36)/90.36=2.25%≤10%），基础分应取band下限48。但任务要求提交的submission/results/metrics.json与evidence_table.csv均缺失，触发证据绑定限制，A不能取band上限或附加分，故A=48（不额外扣除20%未报告，因20%OA实际有落盘log支撑；但若视该log为有效实测证据，则两比例均已报告）。结论词与实测数据一致（均超锚值），不扣结论词矛盾分。

## B 证据真实性/实际复现（12.0/40）

磁盘扫描确认metrics.json与evidence_table.csv缺失，属『产生了文件但未真实复现』，触发B∈[0,15]硬规则。虽有train_resnet18_r0.10_s20260813.json及logs10/logs20训练日志证明模型确实运行并产生逐epoch实测OA，但任务要求的核心证据文件（metrics.json、evidence_table.csv）未落盘，且两份EVAL_REPORT散文数值相互矛盾（v1声称10%OA=78.63%，v2声称10%OA=89.45%），证据链不完整。按分层规则，有证据文件但关键指标文件缺失、报告数值不一致，B给12分（∈[0,15]）。

## 证据与重算说明

独立重算未执行。关键实测数（来自落盘文件）：10%训练OA=89.4462%（best_test_oa，epoch38，json）；20%训练OA=92.39%（best@30，logs20_s20260813.txt）；数据划分统计：10%每类train=70/test=630（总计3150/28350），20%每类train=140/test=560（总计6300/25200），与论文per-class 10%/20%口径一致，counts CSV与split CSV可对应。缺失：submission/results/metrics.json、evidence_table.csv；EVAL_REPORT_v1中78.63%与落盘json的89.4462%严重矛盾，以落盘log为准。

## 结论

- **科学结论**: `supported`
- 亮点: 实际完成了10%与20%两个训练比例的ResNet18微调，并留下逐epoch训练日志与JSON记录，10%/20%OA均超过论文VGGNet-16锚值（87.15/90.36）；数据划分严格按per-class固定seed（20260813）执行，每类数量统计与论文口径一致。
- 不足: 任务要求的关键证据文件metrics.json与evidence_table.csv缺失，无法进行OA重算与逐类指标核对；自动生成的EVAL_REPORT出现幻觉数值（78.63% vs 落盘89.45%），严重损害证据可信度，且两份报告结论不一致。