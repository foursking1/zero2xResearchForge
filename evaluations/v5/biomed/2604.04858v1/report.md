# EVAL REPORT v5: 2604.04858v1

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 70.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 15.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **42.0** | 60 | A1(12): 核心交付物完整，包含代码、evidence表、metrics.json及运行日志。A2(15): 受限于冻结数据仅为synthetic demo，C01/C03无法匹配锚值，C02部分匹配，C04成功复现u-values趋零效应；结论为partially_supported，触发硬上限A2≤15，给15分。A3(15): 方法严谨，正确实现FairLogue组件流程与反事实分析，无泄漏，可复算。 |
| B 证据真实性/实际复现 | 28.0 | 40 | 证据等级为2（齐全自洽），提交了metrics.json、evidence_table及多份raw_results，内部数值高度自洽，无编造痕迹。受partially_supported结论硬上限约束（B≤28），给28分。 |

## A 核心结果达成度（42.0/60 = A1 12.0 + A2 15.0 + A3 15.0）

A1(12): 核心交付物完整，包含代码、evidence表、metrics.json及运行日志。A2(15): 受限于冻结数据仅为synthetic demo，C01/C03无法匹配锚值，C02部分匹配，C04成功复现u-values趋零效应；结论为partially_supported，触发硬上限A2≤15，给15分。A3(15): 方法严谨，正确实现FairLogue组件流程与反事实分析，无泄漏，可复算。

## B 证据真实性/实际复现（28.0/40）

证据等级为2（齐全自洽），提交了metrics.json、evidence_table及多份raw_results，内部数值高度自洽，无编造痕迹。受partially_supported结论硬上限约束（B≤28），给28分。

## 证据与重算说明

独立重算未执行。关键实测数：fairselect AUROC=0.7423, DP_gap=0.1628；component3 DP_gap=0.2163；C04 u-values全为0.0，B=200。Agent明确标注了synthetic data与All of Us cohort的差异，证据真实可靠。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 诚实面对数据源差异（synthetic vs All of Us），未强行捏造锚值；完整实现了FairLogue的三个组件流程并输出了详尽的交叉验证与反事实分析结果。
- 不足: 受限于冻结数据中缺乏真实All of Us队列，未能复现C01和C03的精确临床指标数值，部分fairness gap（如TPR gap）与论文趋势存在偏差。