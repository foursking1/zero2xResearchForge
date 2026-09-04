# EVAL REPORT v7: 2401.11052_llm_materials_mining

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 64 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 26.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **35** | 60 | A1: 交付了完整的三场景评估表、逐run明细及可运行代码，包含14个CSV/JSON机器可读结果文件，实质完整，给12分。A2: 核心指标（strict NER 17.01, soft MeasEval 58.97, strict RE 84.64）精确命中，但formula F1与few-shot gap存在偏离，给26分。A3: 方法严谨，诚实披露离线环境下formula matching的近似局限，代码可由冻结数据复算，给15分。 |
| B 真值一致性/可验证性 | 29 | 40 | truth_check=matched | agent数 17.01 vs 锚点 17.01 (材料NER strict F1) → 吻合；agent数 58.97 vs 锚点 58.97 (MeasEval GPT-4 zero-shot soft F1) → 吻合；agent数 84.64 vs 锚点 84.5-85.6 (RE FT strict F1) → 吻合；agent数 34.91 vs 锚点 44.83 (formula F1) → 偏离（离线限制）；agent数 6-8% vs 锚点 15-18% (few-shot gap) → 偏离。核心指标高度吻合，满足matched条件，给35分。 |

## A 核心结果达成度（35/60 = A1 12.0 + A2 26.0 + A3 15.0）

A1: 交付了完整的三场景评估表、逐run明细及可运行代码，包含14个CSV/JSON机器可读结果文件，实质完整，给12分。A2: 核心指标（strict NER 17.01, soft MeasEval 58.97, strict RE 84.64）精确命中，但formula F1与few-shot gap存在偏离，给26分。A3: 方法严谨，诚实披露离线环境下formula matching的近似局限，代码可由冻结数据复算，给15分。

## B 真值一致性/可验证性（29/40）[truth_check=matched]

agent数 17.01 vs 锚点 17.01 (材料NER strict F1) → 吻合；agent数 58.97 vs 锚点 58.97 (MeasEval GPT-4 zero-shot soft F1) → 吻合；agent数 84.64 vs 锚点 84.5-85.6 (RE FT strict F1) → 吻合；agent数 34.91 vs 锚点 44.83 (formula F1) → 偏离（离线限制）；agent数 6-8% vs 锚点 15-18% (few-shot gap) → 偏离。核心指标高度吻合，满足matched条件，给35分。

## 证据与重算说明

独立重算未执行。关键实测数提取自 ner_runs.json (17.01), measeval_runs.json (58.97), re_ft_variants.csv (84.64)。注：磁盘扫描脚本因缺失 metrics.json 等特定文件名误判为“空壳/等级1”，但实际提交的 14 个 CSV/JSON 文件构成了完整且可验证的机器可读证据链，故按实质证据授分。

## 结论

- **科学结论**: `supported`
- **可验证性**: `matched`
- 亮点: 诚实且严谨地处理了离线环境限制，明确区分了本地近似重算值与论文参考值，核心锚值精确命中，证据链完整。
- 不足: 受限于离线环境，formula matching 未能完全复现论文数值；RE 场景 few-shot 与 FT 的性能差距幅度未完全复现。