# EVAL REPORT v7: 2311.04765_voraus_ad

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 55.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 10.0 | 12 | |
| A2 科学结论保真 | 12.0 | 33 | |
| A3 方法严谨与可复现 | 13.0 | 15 | |
| **A 合计** | **35.0** | 60 | A1: 产出了完整的训练脚本及结果表格（mvtflow_table.csv, baseline_table.csv, mvtflow_meta.json等），核心交付物实质完整且机器可读，但因未使用标准命名（如metrics.json/evidence_table.csv）且缺claim.md，给10分。A2: 科学结论方向上支持论文claim（深度方法显著优于基线，类别特异性模式吻合），但核心绝对数值（平均AUROC 85.14%、PCA 67.87%）与论文锚点（93.6%、80.0%）存在明显偏离，属于部分支持，给12分。A3: 防泄漏规则严格遵守（仅用setting==72训练，z-score仅拟合训练集），代码逻辑sound，可复现性强，给13分。 |
| B 真值一致性/可验证性 | 20.0 | 40 | truth_check=diverged | 逐条比对：1. 平均AUROC：agent 85.14% vs 锚点 93.6% → 偏离8.46pp；2. PCA基线：agent 67.87% vs 锚点 80.0% → 偏离12.13pp；3. 1-NN基线：agent 75.16% vs 锚点 77.5% → 偏离2.34pp；4. miss_can样本数：agent 11 vs 锚点 72 → 严重偏离（agent诚实记录了冻结数据实际分布，但与论文锚值不符）；5. entangled(8) AUROC：agent 1.0 vs 锚点 100.0 → 吻合；6. invalid_position(9) AUROC：agent 1.0 vs 锚点 100.0 → 吻合。因核心指标超出容差带且样本基数存在差异，truth_check判定为diverged，B给20分。 |

## A 核心结果达成度（35.0/60 = A1 10.0 + A2 12.0 + A3 13.0）

A1: 产出了完整的训练脚本及结果表格（mvtflow_table.csv, baseline_table.csv, mvtflow_meta.json等），核心交付物实质完整且机器可读，但因未使用标准命名（如metrics.json/evidence_table.csv）且缺claim.md，给10分。A2: 科学结论方向上支持论文claim（深度方法显著优于基线，类别特异性模式吻合），但核心绝对数值（平均AUROC 85.14%、PCA 67.87%）与论文锚点（93.6%、80.0%）存在明显偏离，属于部分支持，给12分。A3: 防泄漏规则严格遵守（仅用setting==72训练，z-score仅拟合训练集），代码逻辑sound，可复现性强，给13分。

## B 真值一致性/可验证性（20.0/40）[truth_check=diverged]

逐条比对：1. 平均AUROC：agent 85.14% vs 锚点 93.6% → 偏离8.46pp；2. PCA基线：agent 67.87% vs 锚点 80.0% → 偏离12.13pp；3. 1-NN基线：agent 75.16% vs 锚点 77.5% → 偏离2.34pp；4. miss_can样本数：agent 11 vs 锚点 72 → 严重偏离（agent诚实记录了冻结数据实际分布，但与论文锚值不符）；5. entangled(8) AUROC：agent 1.0 vs 锚点 100.0 → 吻合；6. invalid_position(9) AUROC：agent 1.0 vs 锚点 100.0 → 吻合。因核心指标超出容差带且样本基数存在差异，truth_check判定为diverged，B给20分。

## 证据与重算说明

独立重算未执行。关键实测数（据落盘文件）：样本总数2122，训练集948，miss_can异常样本数11（与论文锚72不符，但忠于冻结数据实际分布），主方法平均AUROC=0.8514，PCA=0.6787，1-NN=0.7516。存在mvtflow_meta.json等实质结果文件，但缺失标准命名的metrics.json/evidence_table.csv。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 严格遵守防泄漏规则，代码结构清晰，诚实记录并解释了冻结数据与论文锚值在特定类别样本数上的差异，核心相对优势claim被数据支持。
- 不足: 未按TASK.md规范命名标准证据文件导致证据等级降级；部分基线（PCA）和主方法平均AUROC与论文真值存在明显偏离，且miss_can样本数与论文锚值严重不符。