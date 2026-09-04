# EVAL REPORT v3: 2307.11958_transferability_estimation_seg

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v3（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 66.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 30.0 | 60 | 逐字引用实测数值：CC-FV Pearson=0.3827, τ=0.4000。对照Rubric，Pearson落入0.3-0.5半满带，τ满足≥0.3条件，但距离锚值(0.7003/0.4986)偏差明显(>40%)，依从严原则A1给12分；A2实测CC-FV(0.3827)优于LogME(0.2728)等基线，满足相对优势，给18分；A3明确报告top-1未命中(选l08_s1，实际l16_short)，得0分。A总分30。 |
| B 证据真实性/实际复现 | 36.0 | 40 | 磁盘扫描显示metrics.json与evidence_table.csv齐全，证据等级为2。抽查CC-FV Pearson=0.3827与liver_l16_short ft_dice=0.85857，与报告散文严格一致，论文锚值独立存放未混入实测。证据真实自洽，落入[30,40]区间，给36分。 |

## A 核心结果达成度（30.0/60）

逐字引用实测数值：CC-FV Pearson=0.3827, τ=0.4000。对照Rubric，Pearson落入0.3-0.5半满带，τ满足≥0.3条件，但距离锚值(0.7003/0.4986)偏差明显(>40%)，依从严原则A1给12分；A2实测CC-FV(0.3827)优于LogME(0.2728)等基线，满足相对优势，给18分；A3明确报告top-1未命中(选l08_s1，实际l16_short)，得0分。A总分30。

## B 证据真实性/实际复现（36.0/40）

磁盘扫描显示metrics.json与evidence_table.csv齐全，证据等级为2。抽查CC-FV Pearson=0.3827与liver_l16_short ft_dice=0.85857，与报告散文严格一致，论文锚值独立存放未混入实测。证据真实自洽，落入[30,40]区间，给36分。

## 证据与重算说明

独立重算未执行。关键实测数：CC-FV Pearson=0.3827，τ=0.4000（metrics.json）；liver_l16_short ft_dice=0.85857（evidence_table.csv）。数据截断问题有详细审计记录，证据链完整自洽。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 诚实记录并处理了冻结数据的gzip截断缺陷，TE方法的source-free伪标签实现逻辑严密，基线对比完整且证据链高度一致。
- 不足: 受限于数据缺陷导致源池退化，top-1选择未命中，且相关系数绝对值未能复现论文锚值的量级，偏差较大。