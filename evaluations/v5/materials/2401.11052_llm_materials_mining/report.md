# EVAL REPORT v5: 2401.11052_llm_materials_mining

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 57.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 10.0 | 12 | |
| A2 科学结论保真 | 15 | 33 | |
| A3 方法严谨与可复现 | 7.0 | 15 | |
| **A 合计** | **32.0** | 60 | A1: 交付了完整的三场景评估表、逐run明细及可运行代码，实质完整，给10分。A2: 科学结论保真度高，材料NER strict F1(17.01)、性质NER(58.97)、RE FT(84.64)等关键锚值精确命中，核心claim完全复现，给18分。A3: 方法严谨，诚实披露离线环境下formula matching的近似局限，代码可由冻结数据复算，给7分。受证据等级1硬约束，A总分钳制至35分。 |
| B 证据真实性/实际复现 | 25.0 | 40 | 提交了丰富的中间结果与汇总文件（如ner_runs.json, re_ft_variants.csv等），数值内部自洽且与报告一致。但缺失标准的metrics.json与特定命名的evidence_table.csv，触发磁盘扫描证据等级1硬约束，B给25分，落入[11,29]区间。 |

## A 核心结果达成度（32.0/60 = A1 10.0 + A2 15 + A3 7.0）

A1: 交付了完整的三场景评估表、逐run明细及可运行代码，实质完整，给10分。A2: 科学结论保真度高，材料NER strict F1(17.01)、性质NER(58.97)、RE FT(84.64)等关键锚值精确命中，核心claim完全复现，给18分。A3: 方法严谨，诚实披露离线环境下formula matching的近似局限，代码可由冻结数据复算，给7分。受证据等级1硬约束，A总分钳制至35分。

## B 证据真实性/实际复现（25.0/40）

提交了丰富的中间结果与汇总文件（如ner_runs.json, re_ft_variants.csv等），数值内部自洽且与报告一致。但缺失标准的metrics.json与特定命名的evidence_table.csv，触发磁盘扫描证据等级1硬约束，B给25分，落入[11,29]区间。

## 证据与重算说明

独立重算未执行。关键实测数：材料NER strict F1=17.01（ner_runs.json），MeasEval GPT-4 zero-shot soft F1=58.97（measeval_runs.json），RE FT strict F1=84.64（re_ft_variants.csv）。数值与报告一致，但缺少标准metrics.json被判定为等级1。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 诚实且严谨地处理了离线环境限制，明确区分了本地近似重算值与论文参考值，核心锚值命中率高，证据表结构完整。
- 不足: 未能生成标准的metrics.json等格式证据文件导致触发扫描硬规则扣分；受限于离线环境，formula matching未能完全复现论文数值。