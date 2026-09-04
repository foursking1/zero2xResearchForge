# EVAL REPORT v3: 2509.16616_risky_investors_ranking

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 48.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 10.0 | 60 | Agent实测creditcard with-prior PA-RiskRanker F1=0.9088，被LGBM(0.9550)和Rankformer(0.9357)反超；jobprofit PA F1=0.8046，被XGB(0.9425)和Rankformer(0.8506)反超。与论文锚值（PA-RiskRanker在两个数据集上均为F1最高且loss最低）方向完全相反，属于明显不达标，依梯度规则A≤15，综合给10分。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘证据扫描显示等级=2（证据齐全自洽）。提交物包含metrics.json、evidence_table.csv、data_facts.json及大量per-fold中间结果，内部数值高度一致。Agent准确核验了冻结数据规模（指出jobprofit实际14479行而非manifest的9998行），证据链完整且高度可信，给38分。 |

## A 核心结果达成度（10.0/60）

Agent实测creditcard with-prior PA-RiskRanker F1=0.9088，被LGBM(0.9550)和Rankformer(0.9357)反超；jobprofit PA F1=0.8046，被XGB(0.9425)和Rankformer(0.8506)反超。与论文锚值（PA-RiskRanker在两个数据集上均为F1最高且loss最低）方向完全相反，属于明显不达标，依梯度规则A≤15，综合给10分。

## B 证据真实性/实际复现（38.0/40）

磁盘证据扫描显示等级=2（证据齐全自洽）。提交物包含metrics.json、evidence_table.csv、data_facts.json及大量per-fold中间结果，内部数值高度一致。Agent准确核验了冻结数据规模（指出jobprofit实际14479行而非manifest的9998行），证据链完整且高度可信，给38分。

## 证据与重算说明

独立重算未执行。关键实测数：creditcard with-prior PA F1=0.9088/Loss=100619.51；jobprofit with-prior PA F1=0.8046/Loss=35283.02。data_facts.json证实数据规模与1%正类比例，证据真实可靠。

## 结论

- **科学结论**: `contradicted`
- 亮点: 实验设计严谨，诚实报告了复现失败并给出了极具洞察力的归因分析，对数据版本差异的敏锐捕捉证明了其实际运行了代码。
- 不足: 受限于缺乏专有预训练权重及tabular adaptation的欠规范，PA-RiskRanker在公开表格数据上的表现未能复现论文的最优结论，核心claim被证伪。