# EVAL REPORT v3: 2306.15006_dnabert2_gue

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v3（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1(20): 数据统计详尽且准确，4个任务的规模、序列长度、正负样本比例均在metrics.json和data_stats.json中正确解析。A2(20): 实现了DNABERT-2+LoRA与4-mer+LR/RF基线，同协议评估，evidence_table包含所有结果。A3(20): 基础模型在4/4任务上均优于基线（如EMP_H3 MCC 0.762 vs 0.495），promoter F1量级（0.9312, 0.8331）与论文参考值一致，主论断完全成立。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示证据等级为2，metrics.json、evidence_table.csv及多个细分JSON结果文件均存在且内部一致性极高（如prom_300_all F1在多处均为0.9312）。代码完整，证据链闭环，符合[30,40]区间，给40分。 |

## A 核心结果达成度（60/60）

A1(20): 数据统计详尽且准确，4个任务的规模、序列长度、正负样本比例均在metrics.json和data_stats.json中正确解析。A2(20): 实现了DNABERT-2+LoRA与4-mer+LR/RF基线，同协议评估，evidence_table包含所有结果。A3(20): 基础模型在4/4任务上均优于基线（如EMP_H3 MCC 0.762 vs 0.495），promoter F1量级（0.9312, 0.8331）与论文参考值一致，主论断完全成立。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示证据等级为2，metrics.json、evidence_table.csv及多个细分JSON结果文件均存在且内部一致性极高（如prom_300_all F1在多处均为0.9312）。代码完整，证据链闭环，符合[30,40]区间，给40分。

## 证据与重算说明

独立重算未执行。关键实测数：prom_300_all F1=0.9312，EMP_H3 MCC=0.7620，mouse_0 MCC=0.5237，prom_core_all F1=0.8331。数据行数与冻结包一致，论文数值与实测数值界限分明。

## 结论

- **科学结论**: `supported`
- 亮点: 证据链极其完整，提供了训练日志、checkpoint恢复脚本以及详尽的统计JSON，复现工作严谨扎实，数值内部高度自洽。
- 不足: 受限于算力采用LoRA而非全参微调，虽在局限中已充分讨论且不影响核心结论验证，但绝对数值与论文全参微调存在一定差异。