# EVAL REPORT v3: 2408.07579_tabularbench_adv_robustness

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v3（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 90.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 50.0 | 60 | A1维度：agent报告clean spread=2.19pp，robust spread=33.38pp，满足rubric表格满分带条件（<=5且>=15）。但对照冻结参考锚值（robust spread 38.5pp），偏差约13.2%，落入5%-15%偏差区间，依据从严给分原则A1得22分。A2维度：平均鲁棒提升49.67pp，干净下降1.37pp，与参考锚值（52.0pp/1.5pp）高度吻合（偏差<5%），得28分。A维度总计50分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示证据等级为2（齐全自洽）。metrics.json与evidence_table.csv均存在且列完整，数值与报告严格一致。代码逻辑包含要求的L2投影与clip，test样本数2286与锚值完全吻合，未发现抄数行为，给予满分40分。 |

## A 核心结果达成度（50.0/60）

A1维度：agent报告clean spread=2.19pp，robust spread=33.38pp，满足rubric表格满分带条件（<=5且>=15）。但对照冻结参考锚值（robust spread 38.5pp），偏差约13.2%，落入5%-15%偏差区间，依据从严给分原则A1得22分。A2维度：平均鲁棒提升49.67pp，干净下降1.37pp，与参考锚值（52.0pp/1.5pp）高度吻合（偏差<5%），得28分。A维度总计50分。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示证据等级为2（齐全自洽）。metrics.json与evidence_table.csv均存在且列完整，数值与报告严格一致。代码逻辑包含要求的L2投影与clip，test样本数2286与锚值完全吻合，未发现抄数行为，给予满分40分。

## 证据与重算说明

独立重算未执行。关键实测数抽查：test样本数=2286；std clean跨度=2.19pp；std robust跨度=33.38pp；AT平均鲁棒提升=+49.67pp。所有数值在metrics.json、evidence_table.csv与report.md中保持严格一致，证据链完整。

## 结论

- **科学结论**: `supported`
- 亮点: 实验协议执行严谨，代码结构清晰且完全可复现；对结构性模式的验证数据详实，口径差异与局限性讨论专业。
- 不足: 标准训练下的robust spread（33.38pp）与冻结参考锚值（38.5pp）存在约13%的偏差，可能源于模型初始化或优化器浮点累积的微小差异。