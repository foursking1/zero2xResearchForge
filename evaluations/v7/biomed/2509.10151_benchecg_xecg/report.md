# EVAL REPORT v7: 2509.10151_benchecg_xecg

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 46.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 8.0 | 12 | |
| A2 科学结论保真 | 8.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **31.0** | 60 | A1(8分)：产出了完整的代码管线、数据审计和辅助任务结果，但由于冻结数据缺失诊断标签，核心交付物（诊断分类复现结果）缺失，属于有机器可读结果但存在明显缺口。A2(8分)：受限于数据缺陷未能复现论文效应，结论判定为inconclusive，准确反映客观事实，受inconclusive硬上限（≤8）约束给上限8分。A3(15分)：方法严谨，防泄漏措施（train-only归一化）到位，数据审计和SHA-256校验完整，结果可由提交物复算。 |
| B 真值一致性/可验证性 | 15.0 | 40 | truth_check=unverified | truth_check=unverified。agent数 诊断AUROC: NA vs 锚点 0.853 → 无法核对(unverified)；agent数 诊断F1: NA vs 锚点 0.674 → 无法核对(unverified)；agent数 辅助AUROC: 0.8171 vs 锚点 无对应真值 → 无法核对(unverified)。因核心指标为null/NA，无法与论文真值匹配，落入unverified档，但Agent诚实记录NA且未伪造，给该档上限15分。 |

## A 核心结果达成度（31.0/60 = A1 8.0 + A2 8.0 + A3 15.0）

A1(8分)：产出了完整的代码管线、数据审计和辅助任务结果，但由于冻结数据缺失诊断标签，核心交付物（诊断分类复现结果）缺失，属于有机器可读结果但存在明显缺口。A2(8分)：受限于数据缺陷未能复现论文效应，结论判定为inconclusive，准确反映客观事实，受inconclusive硬上限（≤8）约束给上限8分。A3(15分)：方法严谨，防泄漏措施（train-only归一化）到位，数据审计和SHA-256校验完整，结果可由提交物复算。

## B 真值一致性/可验证性（15.0/40）[truth_check=unverified]

truth_check=unverified。agent数 诊断AUROC: NA vs 锚点 0.853 → 无法核对(unverified)；agent数 诊断F1: NA vs 锚点 0.674 → 无法核对(unverified)；agent数 辅助AUROC: 0.8171 vs 锚点 无对应真值 → 无法核对(unverified)。因核心指标为null/NA，无法与论文真值匹配，落入unverified档，但Agent诚实记录NA且未伪造，给该档上限15分。

## 证据与重算说明

独立重算未执行。关键实测数：evidence_table.csv中诊断任务指标诚实标记为NA，辅助任务cnn_multitask的macro_auroc=0.8171；metrics.json中train_samples=1000，sex正类535。data_audit.json证实冻结包确无诊断标签列，SHA-256校验通过。

## 结论

- **科学结论**: `inconclusive`
- **可验证性**: `unverified`
- 亮点: 科学诚信极高，准确发现冻结数据缺失核心诊断标签的致命缺陷，未伪造数据，并通过辅助任务完整验证了代码管线与防泄漏机制。
- 不足: 受限于数据包本身的缺陷，未能提供任何诊断口径的实测结果，导致核心论断在科学上只能判定为inconclusive，无法直接验证论文真值。