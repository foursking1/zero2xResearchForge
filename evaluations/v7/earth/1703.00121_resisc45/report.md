# EVAL REPORT v7: 1703.00121_resisc45

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 42.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 6.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 10.0 | 15 | |
| **A 合计** | **30.0** | 60 | A1(6)：产出了训练日志JSON和数据划分CSV，但缺失TASK强制要求的metrics.json、evidence_table.csv和标准report.md，核心交付物有明显缺口。A2(14)：10% OA落盘数据支持核心claim，但20% OA缺乏落盘证据，结论判定为partially_supported，受硬上限钳制。A3(10)：数据划分逻辑严谨，但20%训练过程无日志落盘，且缺乏完整的推理评估代码，存在轻微顾虑。 |
| B 真值一致性/可验证性 | 12.0 | 40 | truth_check=unverified | 10% OA agent数 89.45% (来自train_resnet18 JSON) vs 锚点 87.15% → 相对差2.6%在d≤10%容差内，但超出±0.45绝对容差，属合理复现；20% OA agent散文报 92.39% vs 锚点 90.36% → 磁盘无logs20等落盘文件，无法验证(unverified)。缺失metrics.json与evidence_table.csv，无法核对逐类指标，整体truth_check判为unverified。 |

## A 核心结果达成度（30.0/60 = A1 6.0 + A2 14.0 + A3 10.0）

A1(6)：产出了训练日志JSON和数据划分CSV，但缺失TASK强制要求的metrics.json、evidence_table.csv和标准report.md，核心交付物有明显缺口。A2(14)：10% OA落盘数据支持核心claim，但20% OA缺乏落盘证据，结论判定为partially_supported，受硬上限钳制。A3(10)：数据划分逻辑严谨，但20%训练过程无日志落盘，且缺乏完整的推理评估代码，存在轻微顾虑。

## B 真值一致性/可验证性（12.0/40）[truth_check=unverified]

10% OA agent数 89.45% (来自train_resnet18 JSON) vs 锚点 87.15% → 相对差2.6%在d≤10%容差内，但超出±0.45绝对容差，属合理复现；20% OA agent散文报 92.39% vs 锚点 90.36% → 磁盘无logs20等落盘文件，无法验证(unverified)。缺失metrics.json与evidence_table.csv，无法核对逐类指标，整体truth_check判为unverified。

## 证据与重算说明

独立重算未执行。关键实测数：10% best_test_oa=89.4462% (train_resnet18_r0.10_s20260813.json)，20% OA=92.39% (仅EVAL_REPORT散文提及，无落盘文件)。数据划分10%每类70/630、20%每类140/560有CSV和meta.json支撑，与论文口径一致。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `unverified`
- 亮点: 数据划分逻辑严谨，严格遵循per-class固定seed划分并提供了详实的统计CSV与meta文件；10%训练日志逐epoch记录，证明模型真实训练并收敛。
- 不足: 严重缺失任务强制要求的metrics.json和evidence_table.csv；20%训练结果仅存在于散文报告中，无落盘日志支撑，证据链断裂。