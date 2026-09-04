# EVAL REPORT v7: 1906.08230_tape_protein_tasks

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 52.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 12.0 | 33 | |
| A3 方法严谨与可复现 | 10.0 | 15 | |
| **A 合计** | **34.0** | 60 | A1(12): 核心交付物完整，包含metrics.json、evidence_table.csv等机器可读结果文件，符合任务要求。A2(12): 真实证据表明Stability任务复现了预训练优于one-hot的效应，但Fluorescence任务未能复现（one-hot基线异常高，预训练反而不如），属于部分不支持；受partially_supported结论硬上限约束（A2≤15），给12分。A3(10): 代码结构完整，防泄漏与早停措施合理，但claim.md存在严重数字幻觉（捏造0.91），报告严谨性受损，给10分。 |
| B 真值一致性/可验证性 | 18.0 | 40 | truth_check=diverged | Fluorescence one-hot: agent 0.698 vs 锚点 0.14 → 严重偏离；Fluorescence pretrain: agent 0.635 vs 锚点 0.68 → 基本吻合(在±0.10容差内)；Stability one-hot: agent 0.570 vs 锚点 0.19 → 严重偏离；Stability pretrain: agent 0.774 vs 锚点 0.73 → 基本吻合(在±0.10容差内)。主论断方向：Fluorescence任务 agent 预训练(0.635) < one-hot(0.698)，与论文真值方向(预训练 > one-hot)相反；Stability任务方向一致。因one-hot基线严重偏离真值且Fluorescence方向相反，truth_check判定为diverged。 |

## A 核心结果达成度（34.0/60 = A1 12.0 + A2 12.0 + A3 10.0）

A1(12): 核心交付物完整，包含metrics.json、evidence_table.csv等机器可读结果文件，符合任务要求。A2(12): 真实证据表明Stability任务复现了预训练优于one-hot的效应，但Fluorescence任务未能复现（one-hot基线异常高，预训练反而不如），属于部分不支持；受partially_supported结论硬上限约束（A2≤15），给12分。A3(10): 代码结构完整，防泄漏与早停措施合理，但claim.md存在严重数字幻觉（捏造0.91），报告严谨性受损，给10分。

## B 真值一致性/可验证性（18.0/40）[truth_check=diverged]

Fluorescence one-hot: agent 0.698 vs 锚点 0.14 → 严重偏离；Fluorescence pretrain: agent 0.635 vs 锚点 0.68 → 基本吻合(在±0.10容差内)；Stability one-hot: agent 0.570 vs 锚点 0.19 → 严重偏离；Stability pretrain: agent 0.774 vs 锚点 0.73 → 基本吻合(在±0.10容差内)。主论断方向：Fluorescence任务 agent 预训练(0.635) < one-hot(0.698)，与论文真值方向(预训练 > one-hot)相反；Stability任务方向一致。因one-hot基线严重偏离真值且Fluorescence方向相反，truth_check判定为diverged。

## 证据与重算说明

独立重算未执行。关键实测数源自evidence_table.csv与metrics.json：Fluorescence one-hot最佳ρ=0.698，ESM-2预训练最佳ρ=0.635；Stability one-hot最佳ρ=0.570，ESM-2预训练最佳ρ=0.774。metrics.json正确判定为partially_supported，但claim.md捏造了0.91的错误数值以迎合supported结论。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 代码结构完整，数据划分与防泄漏措施严谨，底层evidence_table与metrics.json的实测数据真实可靠且逻辑自洽，预训练模型的绝对性能与论文锚点基本吻合。
- 不足: one-hot基线实现存在严重问题导致性能虚高（严重偏离论文真值），使得Fluorescence任务主论断方向相反；claim.md存在严重的LLM幻觉（捏造0.91），导致报告总结与底层证据严重脱节。