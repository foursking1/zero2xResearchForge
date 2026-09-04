# EVAL REPORT v2: 2209.07805_covid_ehr_bench

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1: agent报告时序模型GRU AUROC=96.56，≥90落入满分带，得20分；证据见于evidence_table.csv与metrics.json。A2: agent报告ML基线RF AUROC=96.35，≥85落入满分带，得20分；证据见于evidence_table.csv与metrics.json。A3: agent给出了清晰的72h早期预测任务定义，并提供了GRU与GRU-TA的数值对比及显著性检验（p=0.25），满足“清晰定义且有对比”条件，得20分；证据见于metrics.json中的ta_comparison。A总分60分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示metrics.json与evidence_table.csv均存在，且包含完整的实测数据。抽查evidence_table.csv中gru auroc=0.96558，metrics.json中testing_set_size_patients=110，与报告散文及claim.md中的数值严格一致。agent诚实反映了冻结测试集仅含3个特征的客观限制，未抄袭论文锚值（97.70），证据真实可靠，落入[30,40]满分档，得40分。 |

## A 核心结果达成度（60/60）

A1: agent报告时序模型GRU AUROC=96.56，≥90落入满分带，得20分；证据见于evidence_table.csv与metrics.json。A2: agent报告ML基线RF AUROC=96.35，≥85落入满分带，得20分；证据见于evidence_table.csv与metrics.json。A3: agent给出了清晰的72h早期预测任务定义，并提供了GRU与GRU-TA的数值对比及显著性检验（p=0.25），满足“清晰定义且有对比”条件，得20分；证据见于metrics.json中的ta_comparison。A总分60分。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示metrics.json与evidence_table.csv均存在，且包含完整的实测数据。抽查evidence_table.csv中gru auroc=0.96558，metrics.json中testing_set_size_patients=110，与报告散文及claim.md中的数值严格一致。agent诚实反映了冻结测试集仅含3个特征的客观限制，未抄袭论文锚值（97.70），证据真实可靠，落入[30,40]满分档，得40分。

## 证据与重算说明

独立重算未执行。关键实测数：evidence_table.csv中gru auroc=0.96558287，gru_ta auroc=0.96637589，rf auroc=0.963521；metrics.json中testing_set_size_patients=110，test_positives=13。所有实测数值与论文锚值严格区分，内部一致性极好，无泄漏或抄袭。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 诚实且详尽地揭示了冻结测试集仅含3/74特征的致命数据限制，并在此约束下完成了严谨的防泄漏建模与多维度敏感性分析，报告极具科学素养与透明度。
- 不足: 受限于数据包本身的特征缺失，未能完全复现论文74维全特征及4C临床评分的原始口径，导致TA损失的验证缺乏统计显著性，但这属于数据源限制而非agent方法缺陷。