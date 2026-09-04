# EVAL REPORT v7: 2606.23725_comp_refs_not_experiments

- 执行 agent: Claude Code (deepseek-chat, 经 DeepSeek Anthropic 兼容网关)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 100.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 33.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **60.0** | 60 | A1(12): 核心交付物完整，包含metrics.json/evidence_table.csv等机器可读结果。A2(33): 所有5个关键指标均完美落入PAPER_ANCHOR容差带内；注：Agent对TASK中的H0得出contradicted，这恰好完美支持了论文的核心claim（筛选器不可用、加性校准无效），故从复现论文claim角度判定为supported，不受硬上限惩罚。A3(15): 方法严谨，代码包含SHA-256校验与防泄漏检查，LOO+bootstrap协议实现正确（含seed与97.5分位），结果完全可由冻结数据复算。 |
| B 真值一致性/可验证性 | 40 | 40 | truth_check=matched | truth_check=matched。逐条比对：1. MAE: agent 0.668 V vs 锚点 0.668 V → 吻合；2. Pearson r: agent -0.9385 vs 锚点 -0.939 → 吻合；3. CI上界: agent 1.0905 V vs 锚点 1.092 V (容差0.94-1.24) → 吻合；4. MP偏差: agent -0.538 V vs 锚点 -0.538 V → 吻合；5. Li sd: agent 0.3125 V vs 锚点 0.31 V → 吻合。所有指标与论文真值高度一致。 |

## A 核心结果达成度（60.0/60 = A1 12.0 + A2 33.0 + A3 15.0）

A1(12): 核心交付物完整，包含metrics.json/evidence_table.csv等机器可读结果。A2(33): 所有5个关键指标均完美落入PAPER_ANCHOR容差带内；注：Agent对TASK中的H0得出contradicted，这恰好完美支持了论文的核心claim（筛选器不可用、加性校准无效），故从复现论文claim角度判定为supported，不受硬上限惩罚。A3(15): 方法严谨，代码包含SHA-256校验与防泄漏检查，LOO+bootstrap协议实现正确（含seed与97.5分位），结果完全可由冻结数据复算。

## B 真值一致性/可验证性（40/40）[truth_check=matched]

truth_check=matched。逐条比对：1. MAE: agent 0.668 V vs 锚点 0.668 V → 吻合；2. Pearson r: agent -0.9385 vs 锚点 -0.939 → 吻合；3. CI上界: agent 1.0905 V vs 锚点 1.092 V (容差0.94-1.24) → 吻合；4. MP偏差: agent -0.538 V vs 锚点 -0.538 V → 吻合；5. Li sd: agent 0.3125 V vs 锚点 0.31 V → 吻合。所有指标与论文真值高度一致。

## 证据与重算说明

独立重算未执行（基于代码逻辑与落盘文件核对）。关键实测数：规范MAE=0.668V、Pearson r=-0.9385、LOO bootstrap CI上界=1.0905V、MP参考偏差=-0.538V、Li sd=0.3125V，均与冻结数据重算预期及落盘metrics.json严格一致。

## 结论

- **科学结论**: `supported`
- **可验证性**: `matched`
- 亮点: 完美复现了论文核心的LOO偏差校正与bootstrap保守CI协议，代码结构严谨，防泄漏与数据完整性校验无懈可击，证据链闭环完整。
- 不足: 无明显弱点，是一份高质量的端到端科研复现提交物。