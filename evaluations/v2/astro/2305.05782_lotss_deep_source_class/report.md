# EVAL REPORT v2: 2305.05782_lotss_deep_source_class

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（deepseek-v4-flash）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | 逐项核对满分带：(i) 三场行数 31,610 / 31,162 / 19,179，总计 81,951，精确命中；(ii) 五类×三场计数与 Table 2 全部一致（差 0，如 en1 SFG=22,720、lockman RQAGN=2,633、bootes Unc=1,551，总计 SFG=55,680、RQAGN=7,442、LERG=12,749、HERG=1,744、Unc=4,336），命中；(iii) 百分比 SFG 67.9% / RQAGN 9.1% / LERG 15.6% / HERG 2.1% / Unc 5.3%，均在 ±0.5pt 容差内；(iv) 可靠分类率 94.7%（∈[93%,96%]）；(v) ELAIS-N1 流量分箱 SFG 占比 84.1%→79.2%→66.0%→41.4%→19.2% 单调下降，50% 交叉点 0.99 mJy（∈[0.5,2.5] mJy），并对论文『>90% 极限流量』与实测 84.1% 做了完整性修正/极限流量定义的口径归因；(vi) 给出四档结论 supported。所有关键数值均有 results/metrics.json 与 results/evidence_table.csv 落盘证据支撑，满足证据绑定，授予满分带 60 分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示 metrics.json、evidence_table.csv、per_field_summary.csv、morphology_by_class.csv、crosscheck_metrics.json 等结果文件齐全，代码 analyze_lotss_deep.py 与 crosscheck_lotss_deep.py 可运行且逻辑为纯 FITS 读取计数；报告中的关键实测数与落盘 evidence/metrics 数值严格一致，未发现抄论文数字或硬编码污染，符合『有证据文件且数值与报告严格一致、可核对』的 [30,40] 带，给 40 分。 |

## A 核心结果达成度（60/60）

逐项核对满分带：(i) 三场行数 31,610 / 31,162 / 19,179，总计 81,951，精确命中；(ii) 五类×三场计数与 Table 2 全部一致（差 0，如 en1 SFG=22,720、lockman RQAGN=2,633、bootes Unc=1,551，总计 SFG=55,680、RQAGN=7,442、LERG=12,749、HERG=1,744、Unc=4,336），命中；(iii) 百分比 SFG 67.9% / RQAGN 9.1% / LERG 15.6% / HERG 2.1% / Unc 5.3%，均在 ±0.5pt 容差内；(iv) 可靠分类率 94.7%（∈[93%,96%]）；(v) ELAIS-N1 流量分箱 SFG 占比 84.1%→79.2%→66.0%→41.4%→19.2% 单调下降，50% 交叉点 0.99 mJy（∈[0.5,2.5] mJy），并对论文『>90% 极限流量』与实测 84.1% 做了完整性修正/极限流量定义的口径归因；(vi) 给出四档结论 supported。所有关键数值均有 results/metrics.json 与 results/evidence_table.csv 落盘证据支撑，满足证据绑定，授予满分带 60 分。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示 metrics.json、evidence_table.csv、per_field_summary.csv、morphology_by_class.csv、crosscheck_metrics.json 等结果文件齐全，代码 analyze_lotss_deep.py 与 crosscheck_lotss_deep.py 可运行且逻辑为纯 FITS 读取计数；报告中的关键实测数与落盘 evidence/metrics 数值严格一致，未发现抄论文数字或硬编码污染，符合『有证据文件且数值与报告严格一致、可核对』的 [30,40] 带，给 40 分。

## 证据与重算说明

独立重算未执行；关键实测数 total_rows=81,951、en1 SFG=22,720、总计 RQAGN=7,442 在 results/metrics.json 与 results/evidence_table.csv 中均一致体现；代码中 TABLE2 仅用于比对输出，实测统计逻辑独立；证据文件含逐类计数表（field,class,n）与流量分箱表（field,flux_bin_uJy,n,n_sfg,frac_sfg），列完整。

## 结论

- **科学结论**: `supported`
- 亮点: 精确复现论文 Table 2 全部计数与百分比，并通过主/扩展表逐行比对、AGN_final×RadioAGN_final 规则重建、形态学扩展射电占比等多重交叉验证，低流量端 84% vs 90% 的口径归因专业且合理。
- 不足: 裁判未独立重跑代码验证抽查数（仅做文件与报告一致性核对）；ELAIS-N1 最暗箱样本量较小（n=681）且开关点由 5 箱线性插值得到，存在约 ±0.2 mJy 的插值敏感性。