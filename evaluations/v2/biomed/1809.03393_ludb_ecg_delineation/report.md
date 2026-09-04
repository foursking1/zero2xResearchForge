# EVAL REPORT v2: 1809.03393_ludb_ecg_delineation

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 98.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1：agent报告解析200条×12导联，波计数P=16797/QRS=21965/T=19661，与论文差异0.01%，metrics.json与wave_counts.csv证据齐全，得20分。A2：完整实现多导联与单导联(II)两类方法，evidence_table.csv包含所有9个关键点的Se/PPV/m±σ，得20分。A3：实测多导联P onset Se 99.46% vs 单导联96.43%，T peak 98.68% vs 89.16%，方向与论文主论断完全一致且QRS保持高精度，得20分。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘扫描显示metrics.json、evidence_table.csv及代码文件均存在。抽查字段1（record 1 lead ii符号统计）在spot_check.txt中明确记录为('=16, N=6, )=16, t=5, p=5，与代码逻辑一致；抽查字段2（多导联QRS onset Se=99.931%, PPV=99.562%）在evidence_table.csv、metrics.json与报告中严格一致。证据真实且内部自洽，给38分。 |

## A 核心结果达成度（60/60）

A1：agent报告解析200条×12导联，波计数P=16797/QRS=21965/T=19661，与论文差异0.01%，metrics.json与wave_counts.csv证据齐全，得20分。A2：完整实现多导联与单导联(II)两类方法，evidence_table.csv包含所有9个关键点的Se/PPV/m±σ，得20分。A3：实测多导联P onset Se 99.46% vs 单导联96.43%，T peak 98.68% vs 89.16%，方向与论文主论断完全一致且QRS保持高精度，得20分。

## B 证据真实性/实际复现（38.0/40）

磁盘扫描显示metrics.json、evidence_table.csv及代码文件均存在。抽查字段1（record 1 lead ii符号统计）在spot_check.txt中明确记录为('=16, N=6, )=16, t=5, p=5，与代码逻辑一致；抽查字段2（多导联QRS onset Se=99.931%, PPV=99.562%）在evidence_table.csv、metrics.json与报告中严格一致。证据真实且内部自洽，给38分。

## 证据与重算说明

独立重算未执行。关键实测数：多导联P onset Se 99.464%，单导联P onset Se 96.431%；多导联QRS onset Se 99.931%，PPV 99.562%；波总数58423。所有数值在metrics.json、evidence_table.csv及报告中严格对齐。

## 结论

- **科学结论**: `supported`
- 亮点: 数据解析精确，双方法对比控制变量纯净，跨导联一致性校正逻辑清晰，证据文件详实且内部数值高度一致。
- 不足: 单导联基线未使用论文原对比工具ecg-kit而是自实现检测器，导致单导联绝对PPV高于论文锚值，但不影响方向性结论。