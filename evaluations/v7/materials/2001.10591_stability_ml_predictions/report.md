# EVAL REPORT v7: 2001.10591_stability_ml_predictions

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 100.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 33.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **60.0** | 60 | A1得12分，核心交付物（metrics.json, evidence_table.csv, 代码等）完整且机器可读；A2得33分，自训模型与冻结模型复算结果均完美支持论文核心论断，且与锚点真值高度吻合；A3得15分，方法严谨，使用冻结划分，early stopping防泄漏，代码可复现。 |
| B 真值一致性/可验证性 | 40 | 40 | truth_check=matched | agent数与锚点真值逐项比对：1. 数据划分：agent报出 train 59509 / val 12752 / test 12753 vs 锚点 59509/12752/12753 → 精确吻合。2. ΔHd MAE (Roost)：agent报出 0.0694 eV/atom vs 锚点 0.069 eV/atom → 在±0.01容差内吻合。3. 分类指标 (ElFrac)：agent报出 acc 0.723 / F1 0.631 / FPR 0.191 vs 锚点 0.723 / 0.631 / 0.191 → 精确吻合。4. 自训模型论断验证：agent Ef MAE 0.1495 (≤0.2)，分类 acc 0.760 (<0.8), F1 0.694 (<0.75), FPR 0.181 (>0.15) vs 锚点论断方向 → 完全吻合。truth_check判定为matched。 |

## A 核心结果达成度（60.0/60 = A1 12.0 + A2 33.0 + A3 15.0）

A1得12分，核心交付物（metrics.json, evidence_table.csv, 代码等）完整且机器可读；A2得33分，自训模型与冻结模型复算结果均完美支持论文核心论断，且与锚点真值高度吻合；A3得15分，方法严谨，使用冻结划分，early stopping防泄漏，代码可复现。

## B 真值一致性/可验证性（40/40）[truth_check=matched]

agent数与锚点真值逐项比对：1. 数据划分：agent报出 train 59509 / val 12752 / test 12753 vs 锚点 59509/12752/12753 → 精确吻合。2. ΔHd MAE (Roost)：agent报出 0.0694 eV/atom vs 锚点 0.069 eV/atom → 在±0.01容差内吻合。3. 分类指标 (ElFrac)：agent报出 acc 0.723 / F1 0.631 / FPR 0.191 vs 锚点 0.723 / 0.631 / 0.191 → 精确吻合。4. 自训模型论断验证：agent Ef MAE 0.1495 (≤0.2)，分类 acc 0.760 (<0.8), F1 0.694 (<0.75), FPR 0.181 (>0.15) vs 锚点论断方向 → 完全吻合。truth_check判定为matched。

## 证据与重算说明

独立重算未执行。关键实测数均有落盘证据支撑：自训Ef test MAE=0.1495 eV/atom，稳定性acc=0.760/F1=0.694/FPR=0.181；冻结Roost全集ΔHd MAE=0.0694 eV/atom；ElFrac分类器acc=0.723/F1=0.631/FPR=0.191。代码与运行日志完整。

## 结论

- **科学结论**: `supported`
- **可验证性**: `matched`
- 亮点: 完整复现了论文核心论断，双方法对照清晰，冻结参考模型指标与论文锚高度一致，证据链完整且代码规范。
- 不足: hull重建仅作为补充脚本在二元/三元子集上运行，未覆盖全数据集，但任务卡允许分类器替代路线，故不影响核心得分。