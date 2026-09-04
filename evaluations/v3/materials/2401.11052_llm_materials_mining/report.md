# EVAL REPORT v3: 2401.11052_llm_materials_mining

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v3（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 57.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 35.0 | 60 | 材料NER strict F1=17.01达成，formula未达成(10分)；性质NER结论与数值均达成(20分)；RE FT F1=84.64与shuffled效应达成，few-shot差距未达成(14分)。原始计算44分，受证据等级1硬约束钳制至最高35分。 |
| B 证据真实性/实际复现 | 22.0 | 40 | 提交了evidence_table.md及多个summary.csv/json结果文件，但缺失标准的metrics.json与evidence_table.csv，触发证据等级1硬约束。B给22分，落入[11,29]区间。 |

## A 核心结果达成度（35.0/60）

材料NER strict F1=17.01达成，formula未达成(10分)；性质NER结论与数值均达成(20分)；RE FT F1=84.64与shuffled效应达成，few-shot差距未达成(14分)。原始计算44分，受证据等级1硬约束钳制至最高35分。

## B 证据真实性/实际复现（22.0/40）

提交了evidence_table.md及多个summary.csv/json结果文件，但缺失标准的metrics.json与evidence_table.csv，触发证据等级1硬约束。B给22分，落入[11,29]区间。

## 证据与重算说明

独立重算未执行。关键实测数：材料NER strict F1=17.01（ner_runs.json），MeasEval GPT-4 zero-shot soft F1=58.97（measeval_runs.json），RE FT strict F1=84.64（re_ft_variants.csv）。数值与报告一致，但缺少标准metrics.json。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 诚实披露离线环境下formula matching的近似局限，三场景核心结论与多数关键数值复现准确，代码与中间结果文件结构完整。
- 不足: 未能完全复现RE场景few-shot与FT的15-18%性能差距，且未生成metrics.json等标准格式证据文件导致触发扫描硬规则扣分。