# EVAL REPORT v5: 1703.00121_resisc45

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 55.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 8.0 | 12 | |
| A2 科学结论保真 | 18.0 | 33 | |
| A3 方法严谨与可复现 | 9.0 | 15 | |
| **A 合计** | **35.0** | 60 | A1(8分)：产出了训练日志和数据划分CSV，但缺失TASK强制要求的metrics.json、evidence_table.csv和标准report.md，核心交付物有明显缺口。A2(18分)：落盘JSON显示10% OA=89.45%，完美复现并超越了论文VGG16的87.15%锚值，支持核心claim；但多版报告数值矛盾且缺乏标准证据表，给中档分。A3(9分)：数据划分逻辑严谨，按per-class固定seed划分无泄漏，方法sound，但受限于证据完整性扣分。 |
| B 证据真实性/实际复现 | 20.0 | 40 | 证据等级=1。提供了数据划分CSV、meta JSON及10%训练日志，证明模型真实运行并收敛。但缺失任务强制要求的metrics.json和evidence_table.csv，且附带的多版EVAL_REPORT数值严重矛盾（v1的78.63% vs 落盘的89.45%），内部一致性受损，在[11,29]区间内给20分。 |

## A 核心结果达成度（35.0/60 = A1 8.0 + A2 18.0 + A3 9.0）

A1(8分)：产出了训练日志和数据划分CSV，但缺失TASK强制要求的metrics.json、evidence_table.csv和标准report.md，核心交付物有明显缺口。A2(18分)：落盘JSON显示10% OA=89.45%，完美复现并超越了论文VGG16的87.15%锚值，支持核心claim；但多版报告数值矛盾且缺乏标准证据表，给中档分。A3(9分)：数据划分逻辑严谨，按per-class固定seed划分无泄漏，方法sound，但受限于证据完整性扣分。

## B 证据真实性/实际复现（20.0/40）

证据等级=1。提供了数据划分CSV、meta JSON及10%训练日志，证明模型真实运行并收敛。但缺失任务强制要求的metrics.json和evidence_table.csv，且附带的多版EVAL_REPORT数值严重矛盾（v1的78.63% vs 落盘的89.45%），内部一致性受损，在[11,29]区间内给20分。

## 证据与重算说明

独立重算未执行。关键实测数：10% best_test_oa=89.4462%（epoch 38，落盘JSON），20% best=92.39%（报告提及）。数据划分10%每类70/630，20%每类140/560，与论文一致。缺失metrics.json与evidence_table.csv。

## 结论

- **科学结论**: `supported`
- 亮点: 数据划分逻辑严谨，严格遵循per-class固定seed划分并提供了详实的统计文件；训练日志逐epoch记录，证明模型真实训练并收敛且超越了论文锚值。
- 不足: 缺失核心证据文件metrics.json和evidence_table.csv导致无法直接核对逐类指标；自动生成的早期EVAL_REPORT出现严重幻觉数值，损害了证据链可信度。