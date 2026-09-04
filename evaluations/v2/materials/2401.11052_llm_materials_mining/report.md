# EVAL REPORT v2: 2401.11052_llm_materials_mining

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 59.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 44.0 | 60 | A1: 材料NER strict F1=17.01落入≈17.0区间（达成），formula F1=34.9与增益+17.9未达锚值，达成1项得10分；A2: 性质NER zero-shot无LLM超基线结论正确，GPT-4 zero-shot soft F1=58.97复现，得20分；A3: RE FT strict F1=84.64落入84-86区间，GPT-3.5 zero-shot shuffled效应-5.9达成，但few-shot与FT差距6-8点未达15-18%锚值，达成2项得14分。各项均有落盘json/csv证据支撑。A总分44。 |
| B 证据真实性/实际复现 | 15.0 | 40 | 依据系统【磁盘证据扫描】强制结论，metrics.json/evidence_table.csv等标准实测证据文件缺失，触发「B必须∈[0,15]」硬规则。尽管提交物中实际包含evidence_table.md及多个summary.csv/json结果文件，但受限于硬规则上限，B给15分。 |

## A 核心结果达成度（44.0/60）

A1: 材料NER strict F1=17.01落入≈17.0区间（达成），formula F1=34.9与增益+17.9未达锚值，达成1项得10分；A2: 性质NER zero-shot无LLM超基线结论正确，GPT-4 zero-shot soft F1=58.97复现，得20分；A3: RE FT strict F1=84.64落入84-86区间，GPT-3.5 zero-shot shuffled效应-5.9达成，但few-shot与FT差距6-8点未达15-18%锚值，达成2项得14分。各项均有落盘json/csv证据支撑。A总分44。

## B 证据真实性/实际复现（15.0/40）

依据系统【磁盘证据扫描】强制结论，metrics.json/evidence_table.csv等标准实测证据文件缺失，触发「B必须∈[0,15]」硬规则。尽管提交物中实际包含evidence_table.md及多个summary.csv/json结果文件，但受限于硬规则上限，B给15分。

## 证据与重算说明

独立重算未执行。关键实测数：材料NER strict F1=17.01（ner_runs.json），MeasEval GPT-4 zero-shot soft F1=58.97（measeval_runs.json），RE FT strict F1=84.64（re_ft_variants.csv）。数值与报告一致，但受限于磁盘扫描硬规则判定为证据文件缺失。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 诚实披露离线环境下formula matching的近似局限，三场景核心结论与多数关键数值复现准确，代码与中间结果文件结构完整。
- 不足: 未能完全复现RE场景few-shot与FT的15-18%性能差距，且未生成metrics.json等标准格式证据文件导致触发扫描硬规则扣分。