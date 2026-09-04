# EVAL REPORT v3: 2502.05832_compression_ood

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 82.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 42.0 | 60 | Agent实测关键数值：N=50 Δ=-4.11pp，N=100 Δ=-5.36pp，N=10 Δ=-1.06pp。方向与论文锚值完全一致（imbalanced < balanced），且主档位满足Δ≥1.0pp的显著性阈值，落入RUBRIC的宽松成功带。但具体数值与论文锚值（N=50 Δ=2.39，N=100 Δ=1.32）偏差均大于20%，未精确命中锚值。依据梯度化从严给分规则，严禁将宽松成功带直接给60分，故授予42分以反映核心结论达成但数值存在较大偏差。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描判定证据等级为2（齐全自洽）。提交物包含完整的evidence_table.csv、metrics.json、36个独立run的子metrics.json以及data_verification.json。特别是提供了eval_all.json进行独立重算核验，36个checkpoint全部match，证据链极其完整且内部高度自洽，符合B=40的最高档标准。 |

## A 核心结果达成度（42.0/60）

Agent实测关键数值：N=50 Δ=-4.11pp，N=100 Δ=-5.36pp，N=10 Δ=-1.06pp。方向与论文锚值完全一致（imbalanced < balanced），且主档位满足Δ≥1.0pp的显著性阈值，落入RUBRIC的宽松成功带。但具体数值与论文锚值（N=50 Δ=2.39，N=100 Δ=1.32）偏差均大于20%，未精确命中锚值。依据梯度化从严给分规则，严禁将宽松成功带直接给60分，故授予42分以反映核心结论达成但数值存在较大偏差。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描判定证据等级为2（齐全自洽）。提交物包含完整的evidence_table.csv、metrics.json、36个独立run的子metrics.json以及data_verification.json。特别是提供了eval_all.json进行独立重算核验，36个checkpoint全部match，证据链极其完整且内部高度自洽，符合B=40的最高档标准。

## 证据与重算说明

独立重算未执行（裁判侧未实际运行代码），但依据落盘的eval_all.json和逐run的metrics.json确认了复算一致性。关键实测数：N=50 balanced 25.34 / imbalanced 21.23 (Δ=-4.11)；N=100 balanced 28.21 / imbalanced 22.85 (Δ=-5.36)。

## 结论

- **科学结论**: `supported`
- 亮点: 实验设计极其严谨，提供了36个独立种子的完整checkpoint和reeval核验结果，证据链扎实；对N=10的噪声现象和教师口径差异进行了诚实且深入的机制分析。
- 不足: 实测Δ数值与论文锚值偏差较大（>20%），主要由于教师模型采用CIFAR-10从头训练而非论文的ImageNet预训练，导致绝对准确率偏低且下降幅度与论文不完全对齐。