# EVAL REPORT: 2306.15006_dnabert2_gue

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判（qwen3.7-max）
- 评测时间: 2026-08-20

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1(20分): 数据统计详尽，4个任务的train/val/test规模、序列长度、正负样本比例均解析正确。A2(20分): 实现了DNABERT-2+LoRA基础模型与4-mer+LR/RF浅层基线，同协议同划分评估。A3(20分): 基础模型在4/4任务上均优于基线（如EMP_H3 MCC 0.762 vs 0.495），promoter F1量级（0.9312, 0.8331）与论文参考值一致，主论断完全成立。 |
| B 证据真实性 | 25 | 25 | 独立重算未执行。提交物极其齐全（代码、详细日志、多维度JSON结果、evidence_table）。论文锚值与实测数值严格区分（metrics.json中单列paper_anchors）。内部一致性极高：evidence_table、finetune json、日志文件(logs_finetune_saved2.log)中prom_300_all的F1均为0.9312，数据行数统计与冻结包一致，证据链完整可信。 |
| C 方法与报告 | 15 | 15 | C1(5分): 方法合理，针对MosaicBERT结构做了合理的LoRA目标模块适配，基线选择符合规范。C2(5分): 防泄漏措施严密，代码逻辑确保test集仅用于最终评估，固定种子42。C3(5分): 报告结构完整，包含方法、结果、局限（LoRA与全参差异、子集限制）及明确的结论标签(supported)。 |

## A 核心结果达成度（60/60）

A1(20分): 数据统计详尽，4个任务的train/val/test规模、序列长度、正负样本比例均解析正确。A2(20分): 实现了DNABERT-2+LoRA基础模型与4-mer+LR/RF浅层基线，同协议同划分评估。A3(20分): 基础模型在4/4任务上均优于基线（如EMP_H3 MCC 0.762 vs 0.495），promoter F1量级（0.9312, 0.8331）与论文参考值一致，主论断完全成立。

## B 证据真实性（25/25）

独立重算未执行。提交物极其齐全（代码、详细日志、多维度JSON结果、evidence_table）。论文锚值与实测数值严格区分（metrics.json中单列paper_anchors）。内部一致性极高：evidence_table、finetune json、日志文件(logs_finetune_saved2.log)中prom_300_all的F1均为0.9312，数据行数统计与冻结包一致，证据链完整可信。

## C 方法与报告（15/15）

C1(5分): 方法合理，针对MosaicBERT结构做了合理的LoRA目标模块适配，基线选择符合规范。C2(5分): 防泄漏措施严密，代码逻辑确保test集仅用于最终评估，固定种子42。C3(5分): 报告结构完整，包含方法、结果、局限（LoRA与全参差异、子集限制）及明确的结论标签(supported)。

## 证据与重算说明

独立重算未执行。关键实测数：prom_300_all F1=0.9312 (日志与JSON一致)，EMP_H3 MCC=0.7620，mouse_0 MCC=0.5237，prom_core_all F1=0.8331。数据行数如prom_300_all train=47356均与冻结包一致。

## 结论

- **科学结论**: `supported`
- 亮点: 证据链极其完整，提供了训练日志、checkpoint恢复脚本以及详尽的统计JSON，论文数值与实测数值界限分明，复现工作严谨扎实。
- 不足: 受限于算力采用LoRA而非全参微调，虽在局限中已充分讨论且不影响核心结论验证，但绝对数值与论文全参微调存在一定差异。