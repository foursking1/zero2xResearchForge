# EVAL REPORT v7: 2003.07333_rsvqa

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 46.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 6.0 | 12 | |
| A2 科学结论保真 | 12.0 | 33 | |
| A3 方法严谨与可复现 | 10.0 | 15 | |
| **A 合计** | **28.0** | 60 | A1(6分)：产出了metrics.json和代码，但evidence_table.csv中prediction和correct列完全为空，导致核心证据表存在明显缺口，无法直接用于逐行核对。A2(12分)：结论为partially_supported（硬上限A2≤15），OA(68.10%)与锚点(79.08%)相对偏差约14%，Count子任务(26.87%)与锚点(67.01%)严重偏离，仅Presence等部分指标吻合，给12分。A3(10分)：采用image-level split防泄漏，方法设计sound且诚实报告了局限性，但证据表关键列缺失导致直接验证受阻，存在轻微顾虑，给10分。 |
| B 真值一致性/可验证性 | 18.0 | 40 | truth_check=diverged | agent数 vs 锚点逐条比对：1) OA: agent 68.10% vs 锚点 79.08% → 偏离(d=13.9%)；2) Count: agent 26.87% vs 锚点 67.01% → 严重偏离；3) Presence: agent 87.93% vs 锚点 87.46% → 吻合；4) Comparison: agent 86.67% vs 锚点 81.50% → 偏离；5) 随机换图消融: agent 32.14% vs 锚点 73.78% → 偏离（agent说明了口径差异：推理时shuffle vs 训练时换图，但数字仍不匹配）。整体truth_check判定为diverged，B给18分。 |

## A 核心结果达成度（28.0/60 = A1 6.0 + A2 12.0 + A3 10.0）

A1(6分)：产出了metrics.json和代码，但evidence_table.csv中prediction和correct列完全为空，导致核心证据表存在明显缺口，无法直接用于逐行核对。A2(12分)：结论为partially_supported（硬上限A2≤15），OA(68.10%)与锚点(79.08%)相对偏差约14%，Count子任务(26.87%)与锚点(67.01%)严重偏离，仅Presence等部分指标吻合，给12分。A3(10分)：采用image-level split防泄漏，方法设计sound且诚实报告了局限性，但证据表关键列缺失导致直接验证受阻，存在轻微顾虑，给10分。

## B 真值一致性/可验证性（18.0/40）[truth_check=diverged]

agent数 vs 锚点逐条比对：1) OA: agent 68.10% vs 锚点 79.08% → 偏离(d=13.9%)；2) Count: agent 26.87% vs 锚点 67.01% → 严重偏离；3) Presence: agent 87.93% vs 锚点 87.46% → 吻合；4) Comparison: agent 86.67% vs 锚点 81.50% → 偏离；5) 随机换图消融: agent 32.14% vs 锚点 73.78% → 偏离（agent说明了口径差异：推理时shuffle vs 训练时换图，但数字仍不匹配）。整体truth_check判定为diverged，B给18分。

## 证据与重算说明

独立重算未执行。关键实测数提取自metrics.json：OA=0.68095，presence=0.8793，comparison=0.8667，count=0.2687，rural_urban=1.0，随机换图消融=0.32143。evidence_table.csv存在但缺失prediction和correct列的实际数据，破坏了逐行核对的条件。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 防泄漏设计严谨（image-level split），对Count子任务性能瓶颈及语言先验的消融分析深入且诚实，代码结构完整。
- 不足: evidence_table.csv的prediction和correct列为空，破坏了证据链的完整性，导致裁判无法直接基于表格进行结果抽查与重算；核心指标OA和Count与论文真值存在明显差距。