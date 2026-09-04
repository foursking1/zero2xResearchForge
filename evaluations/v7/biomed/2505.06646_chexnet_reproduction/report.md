# EVAL REPORT v7: 2505.06646_chexnet_reproduction

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 59.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **41.0** | 60 | A1：核心交付物完整，包含代码、metrics.json、evidence_table.csv等机器可读结果，得12分。A2：成功复现了“高AUC、极低F1”及“现代技巧提升F1”的定性模式，但绝对数值受限于子集规模与真值有偏离；结论为partially_supported，受硬上限约束（A2≤15），给14分。A3：方法严谨，测试集严格隔离，保存了预测概率矩阵支持秒级确定性复算，得15分。 |
| B 真值一致性/可验证性 | 18.0 | 40 | truth_check=diverged | agent数 repro AUC 0.6495 vs 锚点 0.79 → 偏离（相对差17.8%，超出10%容差）；agent数 enhanced AUC 0.6558 vs 锚点 0.85 → 偏离（相对差22.8%）；agent数 repro F1 0.0507 vs 锚点 0.08 → 吻合（绝对差0.029，在±0.15容差内）；agent数 enhanced F1 0.2155 vs 锚点 0.39 → 偏离（绝对差0.1745，超出±0.15容差）。多项核心指标与全量数据真值存在明显偏离，判定为diverged。 |

## A 核心结果达成度（41.0/60 = A1 12.0 + A2 14.0 + A3 15.0）

A1：核心交付物完整，包含代码、metrics.json、evidence_table.csv等机器可读结果，得12分。A2：成功复现了“高AUC、极低F1”及“现代技巧提升F1”的定性模式，但绝对数值受限于子集规模与真值有偏离；结论为partially_supported，受硬上限约束（A2≤15），给14分。A3：方法严谨，测试集严格隔离，保存了预测概率矩阵支持秒级确定性复算，得15分。

## B 真值一致性/可验证性（18.0/40）[truth_check=diverged]

agent数 repro AUC 0.6495 vs 锚点 0.79 → 偏离（相对差17.8%，超出10%容差）；agent数 enhanced AUC 0.6558 vs 锚点 0.85 → 偏离（相对差22.8%）；agent数 repro F1 0.0507 vs 锚点 0.08 → 吻合（绝对差0.029，在±0.15容差内）；agent数 enhanced F1 0.2155 vs 锚点 0.39 → 偏离（绝对差0.1745，超出±0.15容差）。多项核心指标与全量数据真值存在明显偏离，判定为diverged。

## 证据与重算说明

独立重算未执行。关键实测数：evidence_table中enhanced mean_auc=0.6558，repro mean_f1=0.0507；metrics.json中Pneumonia enhanced F1=0.1227。各文件间数值完全一致，证据链完整，无抄袭或泄漏。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 实验设计严谨，防泄漏措施到位，保存了预测概率矩阵使得复算成本极低，对数据规模差异导致的数值偏移分析透彻。
- 不足: 受限于冻结子集极小的规模，绝对指标与全量数据论文锚点仍有较大差距，增强版AUC未能体现出相对复现版的明显提升。