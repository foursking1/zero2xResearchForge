# EVAL REPORT v7: 2604.08131_gnn_misinfo

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 45.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 5.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **32.0** | 60 | A1(12分)：交付了完整的代码、evidence_table.csv及多级metrics文件，机器可读结果完整且规范。A2(5分)：Agent实测公平训练下MLP F1达92.87%，与论文真值66.8%严重矛盾，结论判定为contradicted，按“不支持/矛盾”档给5分，且受硬上限规则限制A2≤5。A3(15分)：方法严谨，防泄漏设计完善（TF-IDF仅train拟合，k-NN图仅用train构建，val/test隔离），并进行了多组探针实验和鲁棒性检验，过程极其sound。 |
| B 真值一致性/可验证性 | 13.0 | 40 | truth_check=diverged | 真值比对：1) GraphSAGE F1: agent报92.10% vs 锚点91.9% → 吻合；2) MLP F1: agent报92.87% vs 锚点66.8% → 严重偏离（绝对差26.07pp，远超容差）；3) F1 Gap: agent报-0.77pp vs 锚点+25.1pp → 方向与幅度均严重偏离。因MLP数值及优势方向与论文真值矛盾，truth_check判定为diverged，受contradicted总分≤45硬上限钳制，B给13分。 |

## A 核心结果达成度（32.0/60 = A1 12.0 + A2 5.0 + A3 15.0）

A1(12分)：交付了完整的代码、evidence_table.csv及多级metrics文件，机器可读结果完整且规范。A2(5分)：Agent实测公平训练下MLP F1达92.87%，与论文真值66.8%严重矛盾，结论判定为contradicted，按“不支持/矛盾”档给5分，且受硬上限规则限制A2≤5。A3(15分)：方法严谨，防泄漏设计完善（TF-IDF仅train拟合，k-NN图仅用train构建，val/test隔离），并进行了多组探针实验和鲁棒性检验，过程极其sound。

## B 真值一致性/可验证性（13.0/40）[truth_check=diverged]

真值比对：1) GraphSAGE F1: agent报92.10% vs 锚点91.9% → 吻合；2) MLP F1: agent报92.87% vs 锚点66.8% → 严重偏离（绝对差26.07pp，远超容差）；3) F1 Gap: agent报-0.77pp vs 锚点+25.1pp → 方向与幅度均严重偏离。因MLP数值及优势方向与论文真值矛盾，truth_check判定为diverged，受contradicted总分≤45硬上限钳制，B给13分。

## 证据与重算说明

独立重算未执行。关键实测数：GraphSAGE F1=92.10% (evidence_table.csv), MLP F1=92.87% (evidence_table.csv), f1_gap_pp=-0.77。多份文件（metrics_aggregate, metrics_perseed, 多个history日志）数值高度自洽，证据真实可信。

## 结论

- **科学结论**: `contradicted`
- **可验证性**: `diverged`
- 亮点: 完美复现了GraphSAGE的锚值，并通过严密的探针实验和防泄漏设计揭示了原论文MLP基线可能严重欠训练的问题，展现了卓越的批判性思维与工程能力。
- 不足: 受限于评分系统对“与论文真值矛盾”的硬规则惩罚及conclusion=contradicted时总分≤45的强制约束，尽管科学发现深刻且证据确凿，总分仍被机械截断。