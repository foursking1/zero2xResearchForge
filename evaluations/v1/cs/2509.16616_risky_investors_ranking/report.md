# EVAL REPORT: 2509.16616_risky_investors_ranking

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判（qwen3.7-max）
- 评测时间: 2026-08-20

## 总分: 55.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 15.0 | 60 | A1: agent 报告 creditcard with-prior PA-RiskRanker F1=0.9088，被 LGBM(0.9550)/XGB(0.9556)/Rankformer(0.9357) 反超。rubric 零分带要求“被反超且无法归因”，agent 明确归因于缺乏专有数据预训练及 tabular adaptation 欠规范（replicability gap），故跳出零分带，落入低分带（实现了且有对照但非最高）得 8 分。A2: jobprofit 上 PA F1=0.8046，同样被多数基准反超且已归因，落入低分带得 5 分。A3: 跨数据集方向一致（均被反超），且 agent 极其清晰地界定了摘要声明（专有数据）与附录 D（公开数据）的边界，未将摘要误作本实验结论，但 A1/A2 均未达半满带，故落入低分带得 2 分。 |
| B 证据真实性 | 25 | 25 | 提交物极其齐全（代码、evidence_table、metrics.json、per-seed 中间结果、data_facts）。独立重算未执行，但 agent 敏锐指出冻结数据 jobprofit 实际为 14479 行（manifest 标注 9998 为 stale），并给出了正确的 SHA-256 和 1% 正类比例验证，内部数值（metrics.json 与 evidence_table）高度一致，确保证据为真实跑批而非抄写论文。给满分 25。 |
| C 方法与报告 | 15 | 15 | C1(5): 标签/划分/group 构造严格遵循附录 D，PA-BCE 与 cross-attention 实现合理，with-prior 口径清晰。C2(6): 3-fold CV 与多 seed 集成严谨，防泄漏措施明确，financial loss 计罚口径正确。C3(4): 结论诚实判定为 contradicted，深入剖析了 replicability gap 的根源（预训练缺失），边界讨论极为出色。 |

## A 核心结果达成度（15.0/60）

A1: agent 报告 creditcard with-prior PA-RiskRanker F1=0.9088，被 LGBM(0.9550)/XGB(0.9556)/Rankformer(0.9357) 反超。rubric 零分带要求“被反超且无法归因”，agent 明确归因于缺乏专有数据预训练及 tabular adaptation 欠规范（replicability gap），故跳出零分带，落入低分带（实现了且有对照但非最高）得 8 分。A2: jobprofit 上 PA F1=0.8046，同样被多数基准反超且已归因，落入低分带得 5 分。A3: 跨数据集方向一致（均被反超），且 agent 极其清晰地界定了摘要声明（专有数据）与附录 D（公开数据）的边界，未将摘要误作本实验结论，但 A1/A2 均未达半满带，故落入低分带得 2 分。

## B 证据真实性（25/25）

提交物极其齐全（代码、evidence_table、metrics.json、per-seed 中间结果、data_facts）。独立重算未执行，但 agent 敏锐指出冻结数据 jobprofit 实际为 14479 行（manifest 标注 9998 为 stale），并给出了正确的 SHA-256 和 1% 正类比例验证，内部数值（metrics.json 与 evidence_table）高度一致，确保证据为真实跑批而非抄写论文。给满分 25。

## C 方法与报告（15/15）

C1(5): 标签/划分/group 构造严格遵循附录 D，PA-BCE 与 cross-attention 实现合理，with-prior 口径清晰。C2(6): 3-fold CV 与多 seed 集成严谨，防泄漏措施明确，financial loss 计罚口径正确。C3(4): 结论诚实判定为 contradicted，深入剖析了 replicability gap 的根源（预训练缺失），边界讨论极为出色。

## 证据与重算说明

独立重算未执行。关键实测数：creditcard with-prior PA F1=0.9088/Loss=100619.51，Rankformer F1=0.9357；jobprofit with-prior PA F1=0.8046/Loss=35283.02。data_facts.json 证实 creditcard 284807 行、jobprofit 14479 行，正类比例均 ≈1%。

## 结论

- **科学结论**: `contradicted`
- 亮点: 实验设计严谨，诚实报告了复现失败并给出了极具洞察力的归因分析（replicability gap），对数据版本差异（9998 vs 14479）的敏锐捕捉证明了其实际运行了代码。
- 不足: 受限于缺乏专有预训练权重，PA-RiskRanker 在公开表格数据上的表现未能复现论文的最优结论，核心 claim 被证伪。