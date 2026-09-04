# EVAL REPORT v2: 2101.00269_shannon_ionic_radii_ml

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 98.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1: 数据统计1005行/Shannon 476/ML 988正确，单位换算与7折CV协议声明清晰，得20分。A2: 实现了GPR及Ridge/MLP对照，特征集包含周期/族/价电子/OS/CN/电离势，得20分。A3: GPR(F2) RMSE=0.0447Å、R²=98.6%，(F4) RMSE=0.0392Å、R²=99.0%，落入[0.02, 0.06]与[95%, 99.5%]区间，量级与方向复现，得20分。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘扫描显示metrics.json与evidence_table.csv均存在且内容完整。抽查字段1：dataset_summary.json确认1005行与476个Shannon标签；抽查字段2：evidence_table中GPR RMSE为0.0447Å与0.0392Å，落入容差区间。报告数值与落盘证据严格一致，无抄写论文数字嫌疑。 |

## A 核心结果达成度（60/60）

A1: 数据统计1005行/Shannon 476/ML 988正确，单位换算与7折CV协议声明清晰，得20分。A2: 实现了GPR及Ridge/MLP对照，特征集包含周期/族/价电子/OS/CN/电离势，得20分。A3: GPR(F2) RMSE=0.0447Å、R²=98.6%，(F4) RMSE=0.0392Å、R²=99.0%，落入[0.02, 0.06]与[95%, 99.5%]区间，量级与方向复现，得20分。

## B 证据真实性/实际复现（38.0/40）

磁盘扫描显示metrics.json与evidence_table.csv均存在且内容完整。抽查字段1：dataset_summary.json确认1005行与476个Shannon标签；抽查字段2：evidence_table中GPR RMSE为0.0447Å与0.0392Å，落入容差区间。报告数值与落盘证据严格一致，无抄写论文数字嫌疑。

## 证据与重算说明

独立重算未执行。关键实测数：总行数1005，Shannon标签476，GPR(F2_paper_full) RMSE=0.0447Å、R²=98.6%；GPR(F4_enhanced) RMSE=0.0392Å、R²=99.0%。证据文件齐全且内部一致。

## 结论

- **科学结论**: `supported`
- 亮点: 数据清洗严谨，敏锐发现并修复了冻结CSV中element列全为'H'的解析缺陷；防泄漏设计完善，额外引入按元素分组的GroupKFold以证明模型的高分并非同元素泄漏所致。
- 不足: 电离势等特征依赖外部硬编码的周期表数据，若能在代码或报告中明确注明该静态表的具体数据来源会更加严谨。