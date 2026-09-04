# EVAL REPORT v2: 2211.03400_fermi_4fgl_jetted_agn

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（deepseek-v4-flash）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | 逐项核对 agent 实测数值：总行数=5,065 且唯一 Source_Name=5,065（metrics.json 中 records/unique_source_name）；全空天 CLASS1 空（无对应体）=1,336；|b|>10° 无对应体=657；论文口径重建样本=2,866；bcu 小写=1,073、bcu+BCU 合计=1,074；bll+BLL=1,067；fsrq+FSRQ=658。所有数值均落入 SCORE_RUBRIC 满分带（总行数=5,065、CLASS1 空=1,336±5、样本=2,866±10、bcu=1,073±20、BLL=1,067±20、FSRQ=658±15、|b|>10 无对应体=657±10），且均有 results/metrics.json 与 results/evidence_table.csv 落盘证据支撑，非仅报告散文，符合证据绑定规则。对『~30% 无明确分类』给出了 18.0%（仅无对应体）、37.4%（样本内 bcu）、47.5%（无对应体+bcu）及 29.5%（bcu 占 |b|>10）的多口径敏感度分析，并给出 partially_supported 四档结论，满足满分带第 (vi) 项全部附加要求。论文 2,980/40%/23% 仅作对照讨论，实测使用 2,866/37.2%/23.0% 并正确归因 DR1-vs-DR2 版本差与文献重分类缺失，未发生抄数。故 A=60。 |
| B 证据真实性/实际复现 | 40 | 40 | 依据磁盘证据扫描：metrics.json、evidence_table.csv、all_sky_class_counts.csv、sample_composition.csv、sample_vs_allsky_crosscheck.csv、sample_source_membership.csv、verify_checks.json 等 13 个结果文件均落盘，代码（analyze_4fgl.py、verify_checks.py）完整且可运行；verify_checks.json 显示 all_passed=true。证据文件内部数值（5065/1336/657/1074/2866/1067/658）与报告散文严格一致，且正确区分 CLASS1 空（1336/657）与 ASSOC1 空（1333/654）两种无对应体口径，未见抄数或测试段泄漏。符合『有证据文件且数值与报告严格一致、可核对』的最高档 [30,40]，给满分 40。 |

## A 核心结果达成度（60/60）

逐项核对 agent 实测数值：总行数=5,065 且唯一 Source_Name=5,065（metrics.json 中 records/unique_source_name）；全空天 CLASS1 空（无对应体）=1,336；|b|>10° 无对应体=657；论文口径重建样本=2,866；bcu 小写=1,073、bcu+BCU 合计=1,074；bll+BLL=1,067；fsrq+FSRQ=658。所有数值均落入 SCORE_RUBRIC 满分带（总行数=5,065、CLASS1 空=1,336±5、样本=2,866±10、bcu=1,073±20、BLL=1,067±20、FSRQ=658±15、|b|>10 无对应体=657±10），且均有 results/metrics.json 与 results/evidence_table.csv 落盘证据支撑，非仅报告散文，符合证据绑定规则。对『~30% 无明确分类』给出了 18.0%（仅无对应体）、37.4%（样本内 bcu）、47.5%（无对应体+bcu）及 29.5%（bcu 占 |b|>10）的多口径敏感度分析，并给出 partially_supported 四档结论，满足满分带第 (vi) 项全部附加要求。论文 2,980/40%/23% 仅作对照讨论，实测使用 2,866/37.2%/23.0% 并正确归因 DR1-vs-DR2 版本差与文献重分类缺失，未发生抄数。故 A=60。

## B 证据真实性/实际复现（40/40）

依据磁盘证据扫描：metrics.json、evidence_table.csv、all_sky_class_counts.csv、sample_composition.csv、sample_vs_allsky_crosscheck.csv、sample_source_membership.csv、verify_checks.json 等 13 个结果文件均落盘，代码（analyze_4fgl.py、verify_checks.py）完整且可运行；verify_checks.json 显示 all_passed=true。证据文件内部数值（5065/1336/657/1074/2866/1067/658）与报告散文严格一致，且正确区分 CLASS1 空（1336/657）与 ASSOC1 空（1333/654）两种无对应体口径，未见抄数或测试段泄漏。符合『有证据文件且数值与报告严格一致、可核对』的最高档 [30,40]，给满分 40。

## 证据与重算说明

独立重算未执行。裁判依据落盘证据核对，关键实测数：总行数=5,065、唯一源=5,065、全空天 CLASS1 空=1,336、|b|>10° 无对应体=657、|b|>10° bcu 小写=1,073/含 BCU=1,074、重建样本=2,866、bll+BLL=1,067、fsrq+FSRQ=658。这些数在 metrics.json、evidence_table.csv、verify_checks.json 中相互一致，且与编译器探针数值吻合。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 定宽解析严格按 ReadMe 字节区间且大小写敏感处理正确，三层口径统计完整，对 '~30% 无明确分类' 的多口径敏感度分析和 DR1/DR2+文献重分类的差异归因准确，证据链闭环可追溯。
- 不足: 无明显实质短板；仅提示本裁判未独立重跑代码（但磁盘证据链已充分自洽），另样本中计入大写 GAL 2 个源属口径选择，已在 ±10 容差内，不影响满分判定。