# EVAL REPORT v5: 2508.14107_suryabench_flare

- 执行 agent: Claude Code (deepseek-chat, 经 DeepSeek Anthropic 兼容网关)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 70.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 15.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **42.0** | 60 | A1(12): 核心交付物（claim、代码、证据表、metrics、图、报告）完整产出，完全符合TASK.md要求。A2(15): Agent测得TSS=0.5674，因冻结数据无SDO影像，与论文影像基线(0.26-0.36)不同源，但Agent准确识别了GOES persistence技能及base-rate漂移的贡献，科学结论定为partially_supported非常严谨。受该结论硬上限(A2≤15)约束，给15分。A3(15): 方法极其严谨，特征严格滞后(shift>=24)防泄漏，warm-up显式处理，包含阈值敏感性与漂移量化分解，结果可由提交物复算。 |
| B 证据真实性/实际复现 | 28.0 | 40 | 磁盘证据扫描显示证据等级为2（齐全自洽）。metrics.json与evidence_table.csv均存在且列完整，内部数值严格自洽。test期base_rate与冻结锚值一致，TSS可由混淆矩阵精确重算，无抄数嫌疑。受partially_supported结论硬上限(B≤28)约束，给28分。 |

## A 核心结果达成度（42.0/60 = A1 12.0 + A2 15.0 + A3 15.0）

A1(12): 核心交付物（claim、代码、证据表、metrics、图、报告）完整产出，完全符合TASK.md要求。A2(15): Agent测得TSS=0.5674，因冻结数据无SDO影像，与论文影像基线(0.26-0.36)不同源，但Agent准确识别了GOES persistence技能及base-rate漂移的贡献，科学结论定为partially_supported非常严谨。受该结论硬上限(A2≤15)约束，给15分。A3(15): 方法极其严谨，特征严格滞后(shift>=24)防泄漏，warm-up显式处理，包含阈值敏感性与漂移量化分解，结果可由提交物复算。

## B 证据真实性/实际复现（28.0/40）

磁盘证据扫描显示证据等级为2（齐全自洽）。metrics.json与evidence_table.csv均存在且列完整，内部数值严格自洽。test期base_rate与冻结锚值一致，TSS可由混淆矩阵精确重算，无抄数嫌疑。受partially_supported结论硬上限(B≤28)约束，给28分。

## 证据与重算说明

独立重算未执行（基于提交物静态核对与磁盘证据扫描）。关键实测数：test n=43848, base_rate=0.2943, TP=11880, FP=10932, TN=20013, FN=1023, TSS=0.5674, HSS=0.4636，均与metrics.json及evidence_table逐字一致，且TSS/HSS可由混淆矩阵精确重算。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 方法设计极其严谨，完美处理了时间序列预测中的未来泄漏与warm-up问题，对base-rate漂移的量化分解和泛化归因分析非常深入且科学。
- 不足: 受限于冻结数据模态（无SDO影像），模型TSS落入半满带，无法在数值上直接复现论文影像基线的具体区间，导致结论只能为partially_supported。