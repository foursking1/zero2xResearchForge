# EVAL REPORT: 2307.11958_transferability_estimation_seg

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判（qwen3.7-max）
- 评测时间: 2026-08-19

## 总分: 65.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 30.0 | 60 | A1: agent 报告 CC-FV Pearson=0.3827, τ=0.4000；rubric band 表：[Pearson≥0.5 或 τ≥0.3 → 20分]，[Pearson 0.3-0.5 → 10分]。虽然 τ=0.4 满足满分条件，但 Pearson=0.3827 明确落入 0.3-0.5 半满带，且 n=5 极小样本下 τ=0.4 统计意义较弱，保守判定落入半满带 → 10分。A2: agent 报告 CC-FV Pearson 0.3827，基线 LogME 0.2728 / LEEP 0.2042 / GBC 0.1707，满足优于至少一个基线 → 20分。A3: agent 报告 top-1 未命中（选 l08_s1，实际最优 l16_short）→ 0分。 |
| B 证据真实性 | 22.0 | 25 | 提交物齐全（code/results/report/claim），论文数值与实测严格区分（metrics.json 含 paper_anchor 字段对照），内部数值一致。独立重算未执行。抽查关键实测：metrics.json 中 CC-FV Pearson=0.3827，evidence_table.csv 中 liver_l16_short ft_dice=0.85857，均真实可信。因未实际重跑代码验证，且 evidence_table 存在多余 direction 列，微扣 3 分。 |
| C 方法与报告 | 13.0 | 15 | C1 方法合理：采用 2D 切片简化与伪标签 source-free 估计，协议设计合理且有详细说明（5分）。C2 防泄漏：目标标注未用于 TE 训练，划分固定，source-free 实现正确（4分）。C3 报告：详实讨论了数据 gzip 截断缺陷、2D 近似及子集规模对 3D 任务的影响，结论边界清晰（4分）。 |

## A 核心结果达成度（30.0/60）

A1: agent 报告 CC-FV Pearson=0.3827, τ=0.4000；rubric band 表：[Pearson≥0.5 或 τ≥0.3 → 20分]，[Pearson 0.3-0.5 → 10分]。虽然 τ=0.4 满足满分条件，但 Pearson=0.3827 明确落入 0.3-0.5 半满带，且 n=5 极小样本下 τ=0.4 统计意义较弱，保守判定落入半满带 → 10分。A2: agent 报告 CC-FV Pearson 0.3827，基线 LogME 0.2728 / LEEP 0.2042 / GBC 0.1707，满足优于至少一个基线 → 20分。A3: agent 报告 top-1 未命中（选 l08_s1，实际最优 l16_short）→ 0分。

## B 证据真实性（22.0/25）

提交物齐全（code/results/report/claim），论文数值与实测严格区分（metrics.json 含 paper_anchor 字段对照），内部数值一致。独立重算未执行。抽查关键实测：metrics.json 中 CC-FV Pearson=0.3827，evidence_table.csv 中 liver_l16_short ft_dice=0.85857，均真实可信。因未实际重跑代码验证，且 evidence_table 存在多余 direction 列，微扣 3 分。

## C 方法与报告（13.0/15）

C1 方法合理：采用 2D 切片简化与伪标签 source-free 估计，协议设计合理且有详细说明（5分）。C2 防泄漏：目标标注未用于 TE 训练，划分固定，source-free 实现正确（4分）。C3 报告：详实讨论了数据 gzip 截断缺陷、2D 近似及子集规模对 3D 任务的影响，结论边界清晰（4分）。

## 证据与重算说明

独立重算未执行。抽查关键实测数值：CC-FV Pearson=0.3827（metrics.json），liver_l16_short ft_dice=0.85857（evidence_table.csv），LogME Pearson=0.2728。论文锚值（Pearson 0.7003）仅用于对照讨论，未混入实测结果。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 诚实且详尽地记录了冻结数据的 gzip 截断缺陷及其对源池规模的毁灭性影响，TE 方法的 source-free 伪标签实现逻辑严密，基线对比完整。
- 不足: 受限于数据缺陷，源池退化至仅 2 个有效病例，导致 top-1 选择未命中且相关系数绝对值远低于论文锚值；2D 简化对 3D 分割迁移性的表征能力有限。