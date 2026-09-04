# EVAL REPORT v2: 2508.04441_mitotic_benchmark

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 98.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1: 最优模型Weighted F1=0.6149（FT模型为0.627），落入[0.6,0.9]区间且报告了Balanced ACC=0.6013，evidence_table与metrics.json证据齐全，得20分。A2: 10%与100%数据F1差值Δ=0.0877，满足≤0.15条件，CSV与JSON均有对应数据支撑，得20分。A3: 明确统计子集正负样本为62/91，全量9501/11051，annotations_stats.json与metrics.json相互印证，得20分。A总分60。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘扫描显示metrics.json、evidence_table.csv及fold_predictions.csv等实测证据文件齐全。抽查evidence_table中最优模型F1=0.6149与metrics.json及报告散文严格一致；子集统计62/91在各JSON中完全吻合。未发现抄袭论文锚值（0.81）或测试段泄漏，证据链详实，落入[30,40]高分档，保守给38分。 |

## A 核心结果达成度（60/60）

A1: 最优模型Weighted F1=0.6149（FT模型为0.627），落入[0.6,0.9]区间且报告了Balanced ACC=0.6013，evidence_table与metrics.json证据齐全，得20分。A2: 10%与100%数据F1差值Δ=0.0877，满足≤0.15条件，CSV与JSON均有对应数据支撑，得20分。A3: 明确统计子集正负样本为62/91，全量9501/11051，annotations_stats.json与metrics.json相互印证，得20分。A总分60。

## B 证据真实性/实际复现（38.0/40）

磁盘扫描显示metrics.json、evidence_table.csv及fold_predictions.csv等实测证据文件齐全。抽查evidence_table中最优模型F1=0.6149与metrics.json及报告散文严格一致；子集统计62/91在各JSON中完全吻合。未发现抄袭论文锚值（0.81）或测试段泄漏，证据链详实，落入[30,40]高分档，保守给38分。

## 证据与重算说明

独立重算未执行。关键实测数：evidence_table.csv中ResNet18_ImageNet|linprobe 100% weighted_f1=0.6149，10%为0.5272；metrics.json中mitotic_figures=62，hard_negative=91；fold_predictions.csv提供了逐patch预测概率，内部数据一致性极高。

## 结论

- **科学结论**: `supported`
- 亮点: 实验设计严谨，诚实声明了硬件与权重限制并采用合理的替代方案，数据效率验证逻辑清晰，证据链（含逐patch预测明细）极为详实规范。
- 不足: 受限于离线环境未能使用病理基础模型及LoRA微调，绝对性能指标与论文全量口径存在必然差距，但已在报告中充分说明并合理降级为趋势验证。