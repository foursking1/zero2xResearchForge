# EVAL REPORT v2: 2509.16616_risky_investors_ranking

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 53.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 15.0 | 60 | A1: agent 报告 creditcard with-prior PA-RiskRanker F1=0.9088，被 LGBM(0.9550)/XGB(0.9556)/Rankformer(0.9357) 反超。因 agent 明确归因于缺乏专有数据预训练（replicability gap），跳出“无法归因”的零分带，落入低分带得 8 分。A2: jobprofit 上 PA F1=0.8046，同样被多数基准反超且已归因，落入低分带得 5 分。A3: 跨数据集方向一致（均被反超），且清晰界定摘要声明与附录D边界，但 A1/A2 均未达半满带，落入低分带得 2 分。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘证据扫描显示 metrics.json、evidence_table.csv 及大量 per-fold 中间结果均存在。evidence_table 与 metrics.json 中的 F1/loss 均值严格一致（如 creditcard PA F1≈0.9088，jobprofit PA F1≈0.8046）。agent 还通过 data_facts.json 准确核验了冻结数据规模（指出 jobprofit 实际 14479 行而非 manifest 的 9998 行）及 1% 正类比例，证据链完整且高度可信，落入 [30,40] 区间，给 38 分。 |

## A 核心结果达成度（15.0/60）

A1: agent 报告 creditcard with-prior PA-RiskRanker F1=0.9088，被 LGBM(0.9550)/XGB(0.9556)/Rankformer(0.9357) 反超。因 agent 明确归因于缺乏专有数据预训练（replicability gap），跳出“无法归因”的零分带，落入低分带得 8 分。A2: jobprofit 上 PA F1=0.8046，同样被多数基准反超且已归因，落入低分带得 5 分。A3: 跨数据集方向一致（均被反超），且清晰界定摘要声明与附录D边界，但 A1/A2 均未达半满带，落入低分带得 2 分。

## B 证据真实性/实际复现（38.0/40）

磁盘证据扫描显示 metrics.json、evidence_table.csv 及大量 per-fold 中间结果均存在。evidence_table 与 metrics.json 中的 F1/loss 均值严格一致（如 creditcard PA F1≈0.9088，jobprofit PA F1≈0.8046）。agent 还通过 data_facts.json 准确核验了冻结数据规模（指出 jobprofit 实际 14479 行而非 manifest 的 9998 行）及 1% 正类比例，证据链完整且高度可信，落入 [30,40] 区间，给 38 分。

## 证据与重算说明

独立重算未执行。关键实测数：creditcard with-prior PA F1=0.9088/Loss=100619.51，Rankformer F1=0.9357；jobprofit with-prior PA F1=0.8046/Loss=35283.02。data_facts.json 证实 creditcard 284807 行、jobprofit 14479 行，正类比例均 ≈1%。

## 结论

- **科学结论**: `contradicted`
- 亮点: 实验设计严谨，诚实报告了复现失败并给出了极具洞察力的归因分析（replicability gap），对数据版本差异的敏锐捕捉证明了其实际运行了代码。
- 不足: 受限于缺乏专有预训练权重，PA-RiskRanker 在公开表格数据上的表现未能复现论文的最优结论，核心 claim 被证伪。