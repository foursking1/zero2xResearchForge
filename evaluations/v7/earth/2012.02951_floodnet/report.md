# EVAL REPORT v7: 2012.02951_floodnet

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 59.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 10.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **37.0** | 60 | A1: 交付了完整的代码、metrics.json和4511行的evidence_table.csv，机器可读结果完整，给12分。A2: 结论为supported，但核心OA(0.8127)与锚点(0.72)相对差12.88%，超出10%容差带，属于数字与锚点偏离。根据硬约束“结论=supported但数字偏离，A2必须≤10”，给10分。A3: 采用图级85/15划分防泄漏，并进行了随机换图和纯语言基线消融，方法严谨sound，给15分。 |
| B 真值一致性/可验证性 | 22.0 | 40 | truth_check=diverged | agent数 0.8127 vs 锚点 0.72 (Overall Accuracy) → 偏离 (d=12.88% > 10%容差)；agent数 0.9851 vs 锚点 0.98 (Yes/No) → 吻合；agent数 0.9915 vs 锚点 0.96 (Condition) → 偏离；agent数 0.3571 vs 锚点 0.31 (Simple Counting) → 偏离；agent数 0.3011 vs 锚点 0.28 (Complex Counting) → 偏离。因核心OA及多个子项超出10%容差带，truth_check判为diverged，B给22分。 |

## A 核心结果达成度（37.0/60 = A1 12.0 + A2 10.0 + A3 15.0）

A1: 交付了完整的代码、metrics.json和4511行的evidence_table.csv，机器可读结果完整，给12分。A2: 结论为supported，但核心OA(0.8127)与锚点(0.72)相对差12.88%，超出10%容差带，属于数字与锚点偏离。根据硬约束“结论=supported但数字偏离，A2必须≤10”，给10分。A3: 采用图级85/15划分防泄漏，并进行了随机换图和纯语言基线消融，方法严谨sound，给15分。

## B 真值一致性/可验证性（22.0/40）[truth_check=diverged]

agent数 0.8127 vs 锚点 0.72 (Overall Accuracy) → 偏离 (d=12.88% > 10%容差)；agent数 0.9851 vs 锚点 0.98 (Yes/No) → 吻合；agent数 0.9915 vs 锚点 0.96 (Condition) → 偏离；agent数 0.3571 vs 锚点 0.31 (Simple Counting) → 偏离；agent数 0.3011 vs 锚点 0.28 (Complex Counting) → 偏离。因核心OA及多个子项超出10%容差带，truth_check判为diverged，B给22分。

## 证据与重算说明

独立重算未执行。关键实测数提取自metrics.json：OA=0.8127，Yes/No=0.9851，Condition=0.9915，Simple=0.3571，Complex=0.3011。evidence_table.csv包含4511行逐条记录，数据落盘完整且内部自洽。

## 结论

- **科学结论**: `supported`
- **可验证性**: `diverged`
- 亮点: 证据链极其完整，防泄漏设计严谨（图级划分），语言偏差消融实验详实，对计数类难点和口径差异的分析非常深入且客观。
- 不足: 受限于离线环境使用了ResNet+ViT替代论文的VGG16，且自划分数据集导致整体OA偏高（12.88%偏差），未能严格落入锚点容差带。