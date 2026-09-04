# EVAL REPORT v2: 2306.15006_dnabert2_gue

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1(20分): 数据统计详尽且准确，4个任务的train/val/test规模、序列长度、正负样本比例均在metrics.json和data_stats.json中正确解析，落入满分带。A2(20分): 实现了DNABERT-2+LoRA基础模型与4-mer+LR/RF浅层基线，同协议同划分评估，evidence_table中包含所有方法结果，落入满分带。A3(20分): 基础模型在4/4任务上均优于基线（如EMP_H3 MCC 0.762 vs 0.4952），promoter F1量级（0.9312, 0.8331）与论文参考值一致，主论断完全成立，落入满分带。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示metrics.json、evidence_table.csv、详细训练日志及多个细分JSON结果文件均存在。内部一致性极高：evidence_table、finetune json、日志文件(logs_finetune_saved2.log)中prom_300_all的F1均为0.9312，数据行数统计与冻结包一致。证据链完整可信，数值与报告严格一致，符合[30,40]区间，给40分。 |

## A 核心结果达成度（60/60）

A1(20分): 数据统计详尽且准确，4个任务的train/val/test规模、序列长度、正负样本比例均在metrics.json和data_stats.json中正确解析，落入满分带。A2(20分): 实现了DNABERT-2+LoRA基础模型与4-mer+LR/RF浅层基线，同协议同划分评估，evidence_table中包含所有方法结果，落入满分带。A3(20分): 基础模型在4/4任务上均优于基线（如EMP_H3 MCC 0.762 vs 0.4952），promoter F1量级（0.9312, 0.8331）与论文参考值一致，主论断完全成立，落入满分带。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示metrics.json、evidence_table.csv、详细训练日志及多个细分JSON结果文件均存在。内部一致性极高：evidence_table、finetune json、日志文件(logs_finetune_saved2.log)中prom_300_all的F1均为0.9312，数据行数统计与冻结包一致。证据链完整可信，数值与报告严格一致，符合[30,40]区间，给40分。

## 证据与重算说明

独立重算未执行。关键实测数：prom_300_all F1=0.9312 (日志与JSON一致)，EMP_H3 MCC=0.7620，mouse_0 MCC=0.5237，prom_core_all F1=0.8331。数据行数如prom_300_all train=47356均与冻结包一致。提供了checkpoint恢复脚本及详尽的统计JSON，论文数值与实测数值界限分明。

## 结论

- **科学结论**: `supported`
- 亮点: 证据链极其完整，提供了训练日志、checkpoint恢复脚本以及详尽的统计JSON，论文数值与实测数值界限分明，复现工作严谨扎实。
- 不足: 受限于算力采用LoRA而非全参微调，虽在局限中已充分讨论且不影响核心结论验证，但绝对数值与论文全参微调存在一定差异。