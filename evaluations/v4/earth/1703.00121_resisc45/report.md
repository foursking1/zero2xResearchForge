# EVAL REPORT v3: 1703.00121_resisc45

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 55.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 35.0 | 60 | 10%实测OA=89.45%（落盘JSON），20%实测OA=92.39%（落盘TXT日志），与锚值（87.15/90.36）偏差分别为2.6%和2.2%，均落入2%-10%偏差带（基础分50）。但受磁盘证据扫描判定证据等级=1（缺失metrics.json与evidence_table.csv）的硬约束，A上限被钳制为35分。 |
| B 证据真实性/实际复现 | 20.0 | 40 | 证据等级=1。提供了数据划分CSV、meta JSON及10%/20%训练日志，证明模型真实运行并收敛。但缺失任务强制要求的metrics.json和evidence_table.csv，且附带的多版EVAL_REPORT数值严重矛盾（v1的78.63% vs 落盘的89.45%），内部一致性受损，在[11,29]区间内给20分。 |

## A 核心结果达成度（35.0/60）

10%实测OA=89.45%（落盘JSON），20%实测OA=92.39%（落盘TXT日志），与锚值（87.15/90.36）偏差分别为2.6%和2.2%，均落入2%-10%偏差带（基础分50）。但受磁盘证据扫描判定证据等级=1（缺失metrics.json与evidence_table.csv）的硬约束，A上限被钳制为35分。

## B 证据真实性/实际复现（20.0/40）

证据等级=1。提供了数据划分CSV、meta JSON及10%/20%训练日志，证明模型真实运行并收敛。但缺失任务强制要求的metrics.json和evidence_table.csv，且附带的多版EVAL_REPORT数值严重矛盾（v1的78.63% vs 落盘的89.45%），内部一致性受损，在[11,29]区间内给20分。

## 证据与重算说明

独立重算未执行。关键实测数：10% best_test_oa=89.4462%（epoch 38，落盘JSON），20% best=92.39%（epoch 30，落盘TXT）。数据划分10%每类70/630，20%每类140/560，与论文一致。缺失metrics.json与evidence_table.csv。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 数据划分逻辑严谨，严格遵循per-class固定seed划分并提供了详实的统计文件；训练日志逐epoch记录，证明模型真实训练并收敛且超越了论文锚值。
- 不足: 缺失核心证据文件metrics.json和evidence_table.csv导致无法核对逐类指标；自动生成的EVAL_REPORT出现严重幻觉数值，损害了证据链可信度。