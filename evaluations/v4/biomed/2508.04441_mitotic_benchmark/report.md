# EVAL REPORT v3: 2508.04441_mitotic_benchmark

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | 逐项核对Rubric与CALIBRATION：A1实测F1=0.6149落入子集口径满分档[0.6,0.9]且报告BACC=0.6013，得20分；A2实测10%与100%数据F1差值0.0877≤0.15，得20分；A3子集统计62/91自洽，得20分。根据CALIBRATION明确说明，0.6-0.9即为子集任务等效精确命中锚值，故A总分60。 |
| B 证据真实性/实际复现 | 40 | 40 | 证据等级为2（齐全自洽）。metrics.json与evidence_table.csv内部高度自洽，且提供了fold_predictions.csv逐patch预测概率作为强复算证据，证据链完整详实，符合B=40最高档标准。 |

## A 核心结果达成度（60/60）

逐项核对Rubric与CALIBRATION：A1实测F1=0.6149落入子集口径满分档[0.6,0.9]且报告BACC=0.6013，得20分；A2实测10%与100%数据F1差值0.0877≤0.15，得20分；A3子集统计62/91自洽，得20分。根据CALIBRATION明确说明，0.6-0.9即为子集任务等效精确命中锚值，故A总分60。

## B 证据真实性/实际复现（40/40）

证据等级为2（齐全自洽）。metrics.json与evidence_table.csv内部高度自洽，且提供了fold_predictions.csv逐patch预测概率作为强复算证据，证据链完整详实，符合B=40最高档标准。

## 证据与重算说明

独立重算未执行。关键实测数：evidence_table.csv中ResNet18_ImageNet|linprobe 100% weighted_f1=0.6149，10%为0.5272；metrics.json中mitotic_figures=62，hard_negative=91；fold_predictions.csv提供逐patch预测明细，支撑复算。

## 结论

- **科学结论**: `supported`
- 亮点: 实验设计严谨，诚实声明硬件限制并采用合理替代方案；提供逐patch预测概率文件，证据链极为详实规范，可复算性极强。
- 不足: 受限于离线环境未能使用病理基础模型及LoRA微调，绝对性能指标与论文全量口径存在必然差距，仅能验证趋势与可行性。