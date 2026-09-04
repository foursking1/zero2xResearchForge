# EVAL REPORT v3: 2408.07579_tabularbench_adv_robustness

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 82.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 42.0 | 60 | 实测数值：clean spread=2.19pp，robust spread=33.38pp，AT平均鲁棒提升=49.67pp，AT平均干净下降=1.37pp。对照冻结协议参考锚值（clean 2.8pp，robust 38.5pp，提升 52.0pp，下降 1.5pp），核心指标 robust spread 偏差约 13.3%（|33.38-38.5|/38.5），落入 10%-20% 偏差区间；AT 提升偏差 4.5%，落入 2%-10% 区间。依据从严梯度化规则，主要结构性指标偏差处于 10%-20% 带，故 A 维度给 42 分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示证据等级为2（齐全自洽）。提交物包含 metrics.json、evidence_table.csv 及完整的可运行代码，且提供了 rerun_log.txt、rerun_compare.txt 和 data_sha256.txt 作为校验与可复算证据。内部数值高度自洽，未发现抄写论文锚值的行为，符合 tier2 最高档标准，给予满分 40 分。 |

## A 核心结果达成度（42.0/60）

实测数值：clean spread=2.19pp，robust spread=33.38pp，AT平均鲁棒提升=49.67pp，AT平均干净下降=1.37pp。对照冻结协议参考锚值（clean 2.8pp，robust 38.5pp，提升 52.0pp，下降 1.5pp），核心指标 robust spread 偏差约 13.3%（|33.38-38.5|/38.5），落入 10%-20% 偏差区间；AT 提升偏差 4.5%，落入 2%-10% 区间。依据从严梯度化规则，主要结构性指标偏差处于 10%-20% 带，故 A 维度给 42 分。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示证据等级为2（齐全自洽）。提交物包含 metrics.json、evidence_table.csv 及完整的可运行代码，且提供了 rerun_log.txt、rerun_compare.txt 和 data_sha256.txt 作为校验与可复算证据。内部数值高度自洽，未发现抄写论文锚值的行为，符合 tier2 最高档标准，给予满分 40 分。

## 证据与重算说明

独立重算未执行。关键实测数抽查：test样本数=2286（与锚值一致）；std clean跨度=2.19pp；std robust跨度=33.38pp；AT平均鲁棒提升=+49.67pp。所有数值在 metrics.json、evidence_table.csv 与 report.md 中保持严格一致，证据链完整。

## 结论

- **科学结论**: `supported`
- 亮点: 实验协议执行极其严谨，代码结构清晰且包含完整的 L2 投影与 clip 逻辑；对结构性模式（C1/C2）的验证数据详实，口径差异与局限性讨论非常专业。
- 不足: 标准训练下的 robust spread（33.38pp）与冻结参考锚值（38.5pp）存在约 13% 的偏差，可能源于模型初始化或优化器浮点累积的微小差异，导致未能达到精确命中的满分带。