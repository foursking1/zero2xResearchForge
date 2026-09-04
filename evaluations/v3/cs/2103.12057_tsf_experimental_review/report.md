# EVAL REPORT v3: 2103.12057_tsf_experimental_review

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v3（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 43.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 35.0 | 60 | Agent报告GRU WAPE=17.7（相对锚15.182差16.58%，落入(15%,30%]得22分），MLP WAPE=20.2（相对锚21.114差4.33%，落入≤15%得30分），基础分52。优势幅度2.5<3触发0.9折扣得46.8。但因缺失evidence_table等落盘文件，证据等级为1，A受硬约束钳制至上限35分。 |
| B 证据真实性/实际复现 | 8.0 | 40 | 磁盘扫描显示metrics.json与evidence_table.csv均缺失，仅有代码和报告散文声称数值，触发空壳硬规则，B必须∈[0,10]，给予8分。 |

## A 核心结果达成度（35.0/60）

Agent报告GRU WAPE=17.7（相对锚15.182差16.58%，落入(15%,30%]得22分），MLP WAPE=20.2（相对锚21.114差4.33%，落入≤15%得30分），基础分52。优势幅度2.5<3触发0.9折扣得46.8。但因缺失evidence_table等落盘文件，证据等级为1，A受硬约束钳制至上限35分。

## B 证据真实性/实际复现（8.0/40）

磁盘扫描显示metrics.json与evidence_table.csv均缺失，仅有代码和报告散文声称数值，触发空壳硬规则，B必须∈[0,10]，给予8分。

## 证据与重算说明

独立重算未执行。关键实测数值（GRU WAPE=17.7, MLP WAPE=20.2, n_series=1427, wape_gap_mlp=2.5）仅提取自EVAL_REPORT.md散文，无对应的evidence_table.csv或metrics.json落盘支撑，属空壳证据。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 代码结构完整，正确实现了固定起点、防泄漏归一化和MIMO滑窗协议，且实测数值与论文锚值有合理区分，未直接抄袭。
- 不足: 严重缺失标准的evidence_table.csv和metrics.json等落盘证据文件，导致无法验证实际运行结果；序列模型相对MLP的优势幅度未达到论文水平。