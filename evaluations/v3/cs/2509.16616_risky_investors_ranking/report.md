# EVAL REPORT v3: 2509.16616_risky_investors_ranking

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v3（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 53.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 15.0 | 60 | A1(8分): 实测creditcard with-prior PA-RiskRanker F1=0.9088，Loss=100619.51；Rankformer F1=0.9357，LGBM F1=0.9550。PA被多数基准反超，不满足满分/半满带条件；因agent明确归因于缺乏专有数据预训练（replicability gap），跳出零分带，落入低分带得8分。A2(5分): 实测jobprofit with-prior PA F1=0.8046，Loss=35283.02；被XGB(0.9425)/LGBM(0.9310)/Rankformer(0.8506)反超，同样因有合理归因落入低分带得5分。A3(2分): 跨数据集方向一致（均未能复现论文最优结论），且清晰界定摘要声明与附录D边界，但A1/A2均未达半满带，落入低分带得2分。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘证据扫描显示等级=2（证据齐全自洽）。提交物包含完整代码、evidence_table.csv、metrics.json、per-fold中间结果及data_facts.json。evidence_table与metrics.json中的F1/loss均值严格一致。agent通过data_facts.json准确核验了冻结数据规模（敏锐指出jobprofit实际14479行而非manifest的9998行）及1%正类比例，证据链完整且高度可信，落入[30,40]区间，给38分。 |

## A 核心结果达成度（15.0/60）

A1(8分): 实测creditcard with-prior PA-RiskRanker F1=0.9088，Loss=100619.51；Rankformer F1=0.9357，LGBM F1=0.9550。PA被多数基准反超，不满足满分/半满带条件；因agent明确归因于缺乏专有数据预训练（replicability gap），跳出零分带，落入低分带得8分。A2(5分): 实测jobprofit with-prior PA F1=0.8046，Loss=35283.02；被XGB(0.9425)/LGBM(0.9310)/Rankformer(0.8506)反超，同样因有合理归因落入低分带得5分。A3(2分): 跨数据集方向一致（均未能复现论文最优结论），且清晰界定摘要声明与附录D边界，但A1/A2均未达半满带，落入低分带得2分。

## B 证据真实性/实际复现（38.0/40）

磁盘证据扫描显示等级=2（证据齐全自洽）。提交物包含完整代码、evidence_table.csv、metrics.json、per-fold中间结果及data_facts.json。evidence_table与metrics.json中的F1/loss均值严格一致。agent通过data_facts.json准确核验了冻结数据规模（敏锐指出jobprofit实际14479行而非manifest的9998行）及1%正类比例，证据链完整且高度可信，落入[30,40]区间，给38分。

## 证据与重算说明

独立重算未执行。关键实测数：creditcard with-prior PA F1=0.9088/Loss=100619.51，Rankformer F1=0.9357；jobprofit with-prior PA F1=0.8046/Loss=35283.02。data_facts.json证实creditcard 284807行、jobprofit 14479行，正类比例均≈1%。

## 结论

- **科学结论**: `contradicted`
- 亮点: 实验设计严谨，诚实报告了复现失败并给出了极具洞察力的归因分析（replicability gap），对数据版本差异的敏锐捕捉证明了其实际运行了代码。
- 不足: 受限于缺乏专有预训练权重及tabular adaptation的欠规范，PA-RiskRanker在公开表格数据上的表现未能复现论文的最优结论，核心claim被证伪。