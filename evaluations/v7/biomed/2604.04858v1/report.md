# EVAL REPORT v7: 2604.04858v1

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 52.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 10.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **37.0** | 60 | A1(12): 核心交付物完整，包含metrics.json、evidence_table.csv及可运行代码，机器可读结果齐全。A2(10): 受限于冻结数据为synthetic demo，核心临床指标（AUROC、Accuracy、各组TPR/FPR）与论文真值严重偏离，仅反事实分析u值吻合，结论判定为partially_supported，触发硬上限A2≤15，给10分。A3(15): 方法严谨，Agent诚实识别出数据源差异并未强行捏造锚值，代码逻辑sound且可复算。 |
| B 真值一致性/可验证性 | 15.0 | 40 | truth_check=diverged | agent数 AUROC=0.7423 vs 锚点 0.709 → 偏离；agent数 accuracy=0.7316 vs 锚点 0.651 → 偏离；agent数 TPR gap=0.0543 vs 锚点 0.33 → 严重偏离；agent数 Black Female TPR=0.523 vs 锚点 0.66 → 偏离；agent数 u-values=0.0 vs 锚点 0.0 → 吻合；agent数 B=200 vs 锚点 200 → 吻合。因大部分核心指标超出容差带，truth_check判定为diverged。 |

## A 核心结果达成度（37.0/60 = A1 12.0 + A2 10.0 + A3 15.0）

A1(12): 核心交付物完整，包含metrics.json、evidence_table.csv及可运行代码，机器可读结果齐全。A2(10): 受限于冻结数据为synthetic demo，核心临床指标（AUROC、Accuracy、各组TPR/FPR）与论文真值严重偏离，仅反事实分析u值吻合，结论判定为partially_supported，触发硬上限A2≤15，给10分。A3(15): 方法严谨，Agent诚实识别出数据源差异并未强行捏造锚值，代码逻辑sound且可复算。

## B 真值一致性/可验证性（15.0/40）[truth_check=diverged]

agent数 AUROC=0.7423 vs 锚点 0.709 → 偏离；agent数 accuracy=0.7316 vs 锚点 0.651 → 偏离；agent数 TPR gap=0.0543 vs 锚点 0.33 → 严重偏离；agent数 Black Female TPR=0.523 vs 锚点 0.66 → 偏离；agent数 u-values=0.0 vs 锚点 0.0 → 吻合；agent数 B=200 vs 锚点 200 → 吻合。因大部分核心指标超出容差带，truth_check判定为diverged。

## 证据与重算说明

独立重算未执行。关键实测数：fairselect AUROC=0.7423, accuracy=0.7316, DP_gap=0.1628, TPR_gap=0.0543；component3 u-values全为0.0，B=200。Agent在evidence_table中明确标注了synthetic data与All of Us cohort的差异。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 诚实面对数据源差异（synthetic vs All of Us），未强行捏造锚值以迎合论文；完整实现了FairLogue组件流程并输出了详尽的交叉验证与反事实分析结果。
- 不足: 受限于冻结数据中缺乏真实All of Us队列，未能复现C01和C03的精确临床指标数值，导致核心结果与论文真值严重偏离。