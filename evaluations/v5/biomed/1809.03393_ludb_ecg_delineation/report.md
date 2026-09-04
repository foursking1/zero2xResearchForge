# EVAL REPORT v5: 1809.03393_ludb_ecg_delineation

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 33.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **60.0** | 60 | A1(12): 完整交付了claim.md, code/, results/evidence_table.csv, metrics.json及report.md等所有核心产物，符合任务明确要求。A2(33): 实测多导联P/T波Se/PPV全面优于单导联（如P onset 99.46% vs 96.43%，T peak 98.68% vs 89.16%），QRS保持高精度，完美复现了论文的核心claim，效应匹配度极高。A3(15): 方法设计严谨，采用同一核心检测器对比跨导联校正的增益，控制变量纯净；评估窗口修正有效避免了残缺波导致的系统性FP，无数据泄漏，可复现性强。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示证据等级为2（齐全自洽）。metrics.json与evidence_table.csv数据详实且内部严格对齐，spot_check.py及spot_check.txt提供了明确的抽查复算证据（如record 1 lead ii符号统计及QRS onset Se=99.931%），无抄袭论文数字行为，给满分40。 |

## A 核心结果达成度（60.0/60 = A1 12.0 + A2 33.0 + A3 15.0）

A1(12): 完整交付了claim.md, code/, results/evidence_table.csv, metrics.json及report.md等所有核心产物，符合任务明确要求。A2(33): 实测多导联P/T波Se/PPV全面优于单导联（如P onset 99.46% vs 96.43%，T peak 98.68% vs 89.16%），QRS保持高精度，完美复现了论文的核心claim，效应匹配度极高。A3(15): 方法设计严谨，采用同一核心检测器对比跨导联校正的增益，控制变量纯净；评估窗口修正有效避免了残缺波导致的系统性FP，无数据泄漏，可复现性强。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示证据等级为2（齐全自洽）。metrics.json与evidence_table.csv数据详实且内部严格对齐，spot_check.py及spot_check.txt提供了明确的抽查复算证据（如record 1 lead ii符号统计及QRS onset Se=99.931%），无抄袭论文数字行为，给满分40。

## 证据与重算说明

独立重算未执行。关键实测数：多导联P onset Se 99.464%，单导联P onset Se 96.431%；多导联QRS onset Se 99.931%，PPV 99.562%；波总数58423。所有数值在metrics.json、evidence_table.csv及spot_check.txt中严格对齐。

## 结论

- **科学结论**: `supported`
- 亮点: 数据解析精确，双方法对比控制变量纯净，跨导联一致性校正逻辑清晰，证据文件详实且内部数值高度一致。
- 不足: 单导联基线未使用论文原对比工具ecg-kit而是自实现检测器，导致单导联绝对PPV高于论文锚值，但在方法学对照上逻辑自洽且不影响方向性结论。