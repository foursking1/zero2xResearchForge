# EVAL REPORT v7: 2209.07805_covid_ehr_bench

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 67.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 15.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **42.0** | 60 | A1: 核心交付物完整，包含metrics.json、evidence_table.csv等机器可读结果文件，得12分。A2: 成功复现高判别力论断(AUROC量级吻合)，但AUPRC及TA提升未显著，结论判定为partially_supported客观准确，受结论级硬上限约束得15分。A3: 方法严谨，明确识别数据特征缺失限制并严格执行防泄漏设计，代码逻辑清晰可复现，得15分。 |
| B 真值一致性/可验证性 | 25.0 | 40 | truth_check=diverged | agent数 96.64 vs 锚点 97.70±2.06 (GRU-TA AUROC) → 吻合；agent数 96.35 vs 锚点 96.58±2.20 (RF AUROC) → 吻合；agent数 86.77 vs 锚点 96.50±3.04 (GRU-TA AUPRC) → 偏离（超出容差下限93.46）；agent数 p=0.25 vs 锚点 p<0.05 (TA显著性) → 偏离；agent数 110 vs 锚点 110 (测试集规模) → 吻合。核心AUROC吻合，但AUPRC与TA显著性偏离，故truth_check为diverged。 |

## A 核心结果达成度（42.0/60 = A1 12.0 + A2 15.0 + A3 15.0）

A1: 核心交付物完整，包含metrics.json、evidence_table.csv等机器可读结果文件，得12分。A2: 成功复现高判别力论断(AUROC量级吻合)，但AUPRC及TA提升未显著，结论判定为partially_supported客观准确，受结论级硬上限约束得15分。A3: 方法严谨，明确识别数据特征缺失限制并严格执行防泄漏设计，代码逻辑清晰可复现，得15分。

## B 真值一致性/可验证性（25.0/40）[truth_check=diverged]

agent数 96.64 vs 锚点 97.70±2.06 (GRU-TA AUROC) → 吻合；agent数 96.35 vs 锚点 96.58±2.20 (RF AUROC) → 吻合；agent数 86.77 vs 锚点 96.50±3.04 (GRU-TA AUPRC) → 偏离（超出容差下限93.46）；agent数 p=0.25 vs 锚点 p<0.05 (TA显著性) → 偏离；agent数 110 vs 锚点 110 (测试集规模) → 吻合。核心AUROC吻合，但AUPRC与TA显著性偏离，故truth_check为diverged。

## 证据与重算说明

独立重算未执行。抽查evidence_table.csv中gru_ta auroc=0.96637，rf auroc=0.96352；metrics.json中testing_set_size_patients=110，test_positives=13。实测数值与论文锚值严格区分，证据链闭环且真实可靠。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 诚实且详尽地揭示了冻结测试集仅含3个特征的致命数据限制，并在此约束下完成了严谨的防泄漏建模与多维度敏感性分析，科学素养极高。
- 不足: 受限于数据包本身的特征缺失，未能完全复现论文74维全特征及4C临床评分的原始口径，导致AUPRC偏离及TA损失的验证缺乏统计显著性。