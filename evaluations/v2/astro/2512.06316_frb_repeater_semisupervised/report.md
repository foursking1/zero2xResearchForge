# EVAL REPORT v2: 2512.06316_frb_repeater_semisupervised

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 98.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | 逐项核对满分带条件：(i) 样本规模 3584/94/3490 落入容差；(ii) DM 均值 445.50 < 686.44，中位数 409.74 < 584.90，方向正确；(iii) p=1.32e-10 < 1e-5；(iv) 报告详实讨论了源级与暴级口径差异及快照日期差异；(v) 给出 supported 结论。所有数值均在 metrics.json 和 evidence_table.csv 中落盘，证据绑定完整，授予满分 60。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 依据磁盘证据扫描，metrics.json、evidence_table.csv 及可运行代码(.py)均存在。evidence_table.csv 中的 class_summary 数据（如 non_repeater n=3490 mean=686.43，repeater n=94 mean=445.50）与 metrics.json 及报告散文严格一致。抽查关键数值（3584行、94个repeater、p=1.32e-10）均落盘且可核对，符合 [30,40] 区间，给 38 分。 |

## A 核心结果达成度（60/60）

逐项核对满分带条件：(i) 样本规模 3584/94/3490 落入容差；(ii) DM 均值 445.50 < 686.44，中位数 409.74 < 584.90，方向正确；(iii) p=1.32e-10 < 1e-5；(iv) 报告详实讨论了源级与暴级口径差异及快照日期差异；(v) 给出 supported 结论。所有数值均在 metrics.json 和 evidence_table.csv 中落盘，证据绑定完整，授予满分 60。

## B 证据真实性/实际复现（38.0/40）

依据磁盘证据扫描，metrics.json、evidence_table.csv 及可运行代码(.py)均存在。evidence_table.csv 中的 class_summary 数据（如 non_repeater n=3490 mean=686.43，repeater n=94 mean=445.50）与 metrics.json 及报告散文严格一致。抽查关键数值（3584行、94个repeater、p=1.32e-10）均落盘且可核对，符合 [30,40] 区间，给 38 分。

## 证据与重算说明

独立重算未执行。磁盘扫描证实代码与证据文件齐全。关键实测数：总行数3584，repeater数94，non-repeater数3490，repeater DM均值445.50，p=1.32e-10，均与 PAPER_ANCHOR 编译器探针高度吻合，无抄数嫌疑。

## 结论

- **科学结论**: `supported`
- 亮点: 数据分析极其严谨，对源级与暴级口径差异、快照日期差异以及29条空源名记录进行了深度审计与归因，证据链完整且数值高度一致。
- 不足: EVAL_REPORT 散文中误称缺失代码文件，但实际磁盘扫描证实代码存在，属于报告撰写与自动化评估脚本间的信息同步瑕疵。