# EVAL REPORT v7: 2508.04441_mitotic_benchmark

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 98.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 33.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **60.0** | 60 | A1(12)：完整产出TASK要求的所有核心交付物（metrics.json、evidence_table.csv、claim.md及完整可运行代码），机器可读结果齐全。A2(33)：在子集口径及PAPER_ANCHOR明确规定的放宽容差（0.6-0.9）下，实测F1=0.6149命中满分档；数据效率ΔF1=0.088满足≤0.15要求；统计数字与真值完全一致，结论supported成立。A3(15)：采用分层5折CV与bagging，特征冻结与轻量头设计合理，无数据泄漏，代码可复现性强。 |
| B 真值一致性/可验证性 | 38.0 | 40 | truth_check=matched | 1. 分类性能(F1)：agent报最优 F1=0.6149 (evidence_table.csv) vs 锚点1 Virchow2-LoRA 0.81。绝对数值有差距，但PAPER_ANCHOR容差列明确规定“提交 F1 落 0.6-0.9 满分档（子集口径放宽）”，故 0.6149 落在容差带内 → 吻合。2. 数据效率：agent报 ΔF1=0.0877 (0.6149-0.5272) vs 锚点4与Rubric ≤0.15 容差 → 吻合。3. 数据集规模：agent报全量 9501 MF / 11051 HN (metrics.json) vs 锚点6 9501/11051 → 完全吻合。 |

## A 核心结果达成度（60.0/60 = A1 12.0 + A2 33.0 + A3 15.0）

A1(12)：完整产出TASK要求的所有核心交付物（metrics.json、evidence_table.csv、claim.md及完整可运行代码），机器可读结果齐全。A2(33)：在子集口径及PAPER_ANCHOR明确规定的放宽容差（0.6-0.9）下，实测F1=0.6149命中满分档；数据效率ΔF1=0.088满足≤0.15要求；统计数字与真值完全一致，结论supported成立。A3(15)：采用分层5折CV与bagging，特征冻结与轻量头设计合理，无数据泄漏，代码可复现性强。

## B 真值一致性/可验证性（38.0/40）[truth_check=matched]

1. 分类性能(F1)：agent报最优 F1=0.6149 (evidence_table.csv) vs 锚点1 Virchow2-LoRA 0.81。绝对数值有差距，但PAPER_ANCHOR容差列明确规定“提交 F1 落 0.6-0.9 满分档（子集口径放宽）”，故 0.6149 落在容差带内 → 吻合。2. 数据效率：agent报 ΔF1=0.0877 (0.6149-0.5272) vs 锚点4与Rubric ≤0.15 容差 → 吻合。3. 数据集规模：agent报全量 9501 MF / 11051 HN (metrics.json) vs 锚点6 9501/11051 → 完全吻合。

## 证据与重算说明

独立重算未执行。关键实测数：evidence_table.csv中ResNet18_ImageNet|linprobe 100% weighted_f1=0.6149，10%为0.5272；metrics.json中子集统计mitotic_figures=62，hard_negative=91，全量9501/11051；fold_predictions.csv提供逐patch预测明细，支撑复算。

## 结论

- **科学结论**: `supported`
- **可验证性**: `matched`
- 亮点: 实验设计严谨，诚实声明了硬件与权重限制并采用合理的替代方案；提供逐patch预测概率文件，证据链极为详实规范，可复算性极强。
- 不足: 受限于离线环境未能使用病理基础模型及LoRA微调，绝对性能指标与论文全量口径存在必然差距，仅能验证趋势与可行性。