# EVAL REPORT v2: 2111.10009_exominer_tess_vetting

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（deepseek-v4-flash）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | 逐项核对满分带条件：总行数 11,289（含表头）且 16 列，命中 11,289±5 与 16 列要求；score 中位 0.755（锚 0.755±0.05）、≥0.5 占比 64.0%（锚 64.0%±1.0pt）、>0.99 占比 9.5%（锚 9.5%±0.5pt），均落盘于 metrics.json；MES<10.5 中 >0.99 占比 0.93%（30/3242），落入 [0.3%,2.5%] 且严格低于 MES≥10.5 组的 12.92%（1040/8047）；score>0.99 且 MES>10.5 = 1040（锚 1040±30）；MES 分箱 >0.99 占比单调上升（0.69%→19.13%）并与论文 Kepler 2.1% 做了归因对比；四档结论 supported 明确给出。所有满分带数值均有 metrics.json/evidence_table 实测证据支撑，非仅散文，故按满分带 60 授予。论文 precision/recall 需金标不可重算，agent 已正确说明聚焦评分行为，满足加分讨论要求。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示 metrics.json 与 evidence_table.csv 等实测证据文件齐全，evidence_table 含完整 MES 分箱表（mes_bin, n_tce, n_score_gt099, frac_score_gt099）与分数分布统计行；metrics.json 中的关键数（总行数 11289、score>0.99 计数 1070、MES<10.5 且 score>0.99 计数 30）与 report.md、claim.md、evidence_table、low_mes_score_gt_099_subset.csv（正好 30 行）严格一致，证据链完整可核对，未见抄论文数字或测试段泄漏。按「有证据文件且数值与报告严格一致、可核对」授予 [30,40] 区间上限 40 分。 |

## A 核心结果达成度（60/60）

逐项核对满分带条件：总行数 11,289（含表头）且 16 列，命中 11,289±5 与 16 列要求；score 中位 0.755（锚 0.755±0.05）、≥0.5 占比 64.0%（锚 64.0%±1.0pt）、>0.99 占比 9.5%（锚 9.5%±0.5pt），均落盘于 metrics.json；MES<10.5 中 >0.99 占比 0.93%（30/3242），落入 [0.3%,2.5%] 且严格低于 MES≥10.5 组的 12.92%（1040/8047）；score>0.99 且 MES>10.5 = 1040（锚 1040±30）；MES 分箱 >0.99 占比单调上升（0.69%→19.13%）并与论文 Kepler 2.1% 做了归因对比；四档结论 supported 明确给出。所有满分带数值均有 metrics.json/evidence_table 实测证据支撑，非仅散文，故按满分带 60 授予。论文 precision/recall 需金标不可重算，agent 已正确说明聚焦评分行为，满足加分讨论要求。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示 metrics.json 与 evidence_table.csv 等实测证据文件齐全，evidence_table 含完整 MES 分箱表（mes_bin, n_tce, n_score_gt099, frac_score_gt099）与分数分布统计行；metrics.json 中的关键数（总行数 11289、score>0.99 计数 1070、MES<10.5 且 score>0.99 计数 30）与 report.md、claim.md、evidence_table、low_mes_score_gt_099_subset.csv（正好 30 行）严格一致，证据链完整可核对，未见抄论文数字或测试段泄漏。按「有证据文件且数值与报告严格一致、可核对」授予 [30,40] 区间上限 40 分。

## 证据与重算说明

独立重算未执行（本裁判未在同一环境运行提交代码）；依据磁盘证据扫描与提交物内部一致性判定。关键实测数抽查：总行数=11,289（含表头，metrics.json 同时给出原始文件行数 11,290）；score>0.99 计数=1,070（evidence_table 亦列出 1070）；MES<10.5 且 score>0.99 计数=30（与 evidence/low_mes_score_gt_099_subset.csv 行数 30 一致）。其余锚值：低 MES 占比 0.925%（30/3242）、高分人口 1040、半径中位 6.79、周期中位 3.92、Spearman(score,MES)=0.183、Spearman(score,SNR)=0.197，均与 evidence 文件互洽。

## 结论

- **科学结论**: `supported`
- 亮点: 核心数值全部落入满分带且证据文件（metrics.json/evidence_table/证据子集 CSV）与报告逐字一致；对 score>0.1 子集上界偏差、TESS 扇区窗口对周期上限 ~125 d 的物理归因、以及无金标不能重算 precision/recall 的局限说明精准到位。
- 不足: 仅有的保留点是裁判未实际运行 code/run_analysis.py 做独立重算，B 维依赖证据文件交叉核对而非进程级验证；但磁盘证据链完整，不构成扣分依据。