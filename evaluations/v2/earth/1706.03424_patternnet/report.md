# EVAL REPORT v2: 1706.03424_patternnet

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | Agent 报告 ResNet18 mAP=0.6233，ViT mAP=0.6103。以 0.61 为锚值，ResNet18 的相对差 d≈2.18%，ViT 的 d≈0.05%，均落入 d≤10% 的满分带（48-60分）。Agent 完整报告了 query/gallery 规模（30400）、种子（0）、P@5（0.9518）以及类别难度分析，无结论词矛盾。关键数值在 metrics.json 和 evidence_table.csv 中均有落盘支撑，证据齐全，故 A 维度给满分 60 分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示 metrics.json、evidence_table.csv、per_query.csv 及运行日志等实测证据文件均存在且齐全。evidence_table 中的 OVERALL mAP (0.6232987577058738) 与 metrics.json 及报告散文中的数值严格一致，内部一致性极好。代码结构完整，包含特征提取、评估和分析脚本。符合「有证据文件且数值与报告严格一致、可核对」的最高档标准，B 给 40 分。 |

## A 核心结果达成度（60/60）

Agent 报告 ResNet18 mAP=0.6233，ViT mAP=0.6103。以 0.61 为锚值，ResNet18 的相对差 d≈2.18%，ViT 的 d≈0.05%，均落入 d≤10% 的满分带（48-60分）。Agent 完整报告了 query/gallery 规模（30400）、种子（0）、P@5（0.9518）以及类别难度分析，无结论词矛盾。关键数值在 metrics.json 和 evidence_table.csv 中均有落盘支撑，证据齐全，故 A 维度给满分 60 分。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示 metrics.json、evidence_table.csv、per_query.csv 及运行日志等实测证据文件均存在且齐全。evidence_table 中的 OVERALL mAP (0.6232987577058738) 与 metrics.json 及报告散文中的数值严格一致，内部一致性极好。代码结构完整，包含特征提取、评估和分析脚本。符合「有证据文件且数值与报告严格一致、可核对」的最高档标准，B 给 40 分。

## 证据与重算说明

独立重算未执行。关键实测数：ResNet18 mAP=0.6232987577058738，P@5=0.9517763157894736；ViT mAP=0.6103277847805555，P@5=0.9476907894736843。evidence_table.csv 包含 38 个类别的逐类指标及 OVERALL 汇总行，数据字段完整，与 metrics.json 完全吻合。

## 结论

- **科学结论**: `supported`
- 亮点: 双模型（ResNet18/ViT）交叉验证，结果高度一致且完美落入满分带；证据链极其完整，包含逐类指标、质心混淆分析、运行日志及可视化，报告规范严谨。
- 不足: 受限于评测环境，裁判未能实际重跑代码验证 parquet 读取与特征提取的底层细节，但现有静态证据已足够支撑结论。