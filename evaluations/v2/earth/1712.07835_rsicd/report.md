# EVAL REPORT v2: 1712.07835_rsicd

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 5.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 0 | 60 | Agent未提交report.md，也未提交metrics.json或evidence_table.csv，完全未报告CIDEr等任何实测数值。根据 rubric 规则「未报告 CIDEr/测试集」落入 0-11 分带；因无落盘证据支撑，触及证据绑定规则下限，故 A 给 0 分。 |
| B 证据真实性/实际复现 | 5.0 | 40 | 磁盘证据扫描显示 metrics.json 与 evidence_table.csv 均缺失，无可运行代码(.py)，仅有一个包含预测与真值的 JSON 文件。属于「实测证据文件缺失」，根据硬规则 B 必须 ∈ [0,15]，故给 5 分。 |

## A 核心结果达成度（0/60）

Agent未提交report.md，也未提交metrics.json或evidence_table.csv，完全未报告CIDEr等任何实测数值。根据 rubric 规则「未报告 CIDEr/测试集」落入 0-11 分带；因无落盘证据支撑，触及证据绑定规则下限，故 A 给 0 分。

## B 证据真实性/实际复现（5.0/40）

磁盘证据扫描显示 metrics.json 与 evidence_table.csv 均缺失，无可运行代码(.py)，仅有一个包含预测与真值的 JSON 文件。属于「实测证据文件缺失」，根据硬规则 B 必须 ∈ [0,15]，故给 5 分。

## 证据与重算说明

独立重算未执行。Agent 仅提交了 e2e_resnet18_test_pred.json（含200条hyps和gts），缺失 metrics.json、evidence_table.csv、report.md 及可运行代码，无法核对任何关键实测数。

## 结论

- **科学结论**: `inconclusive`
- 亮点: 生成了200张测试图的预测描述与对应的5句参考真值，JSON数据结构本身符合后续评测脚本的输入要求。
- 不足: 严重缺失核心交付物，未提供评测指标计算结果、证据表、实验报告及可复现代码，完全无法验证其核心claim与复现真实性。