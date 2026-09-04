# EVAL REPORT v2: 2308.05572_gaia_wd_xp_class

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（deepseek-v4-flash）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | 逐项核对满分带（60分）条件：数值证据均来自落盘的 metrics.json 与 evidence_table.csv，逐字核对如下——(i) total_rows=100886、unique_gaia=100886，满足唯一源数=行数；(ii) SpType 无冒号口径六类 high-confidence 计数 DA 77330 / DB 5688 / DC 4082 / DO 215 / DQ 601 / DZ 1272，全部落入 Table 2 ±50 区间（如 DA∈[77280,77380]、DB∈[5638,5738] 等），合计 89188（±10 内），uncertain=11698（±10 内）；(iii) da_fraction=0.7665087326 即 76.65% ∈ [76.0%,77.3%]，high_conf_fraction=0.8840473406 即 88.40% ∈ [87.9%,88.9%]；(iv) 同时报告 argmax 口径（DA 83963 等）并解释两位小数舍入与冒号判定基于未舍入概率的差异；n_max_prob_ge_065=89388 亦与冒号规则（89188）明确区分；(v) n_teff_neg999=1396、n_da_teff_gt_300000_all=68，与论文 §4.2（1080/34）如实对照并做版本漂移讨论。五条件全中且数值均有落盘证据支撑，A=60。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示：metrics.json 存在、evidence_table.csv 存在（含 class,n_high_conf,n_uncertain,n_argmax,frac_high_conf 全部要求列）、可运行代码 analyze_gaia_wd.py 存在；证据文件内部数值与报告严格一致（如 DA high-conf=77330、Teff=-999=1396、uncertain 逐类合计 11698），无抄论文数字嫌疑（论文锚值 1080/34 与实测 1396/68 被明确区分）。符合『有证据文件且数值与报告严格一致、可核对』最高档，B=40。独立重算未执行：本裁判未实际运行该 Python 脚本从冻结数据重算，依据提交物内部一致性与代码逻辑判定，特此标注。 |

## A 核心结果达成度（60/60）

逐项核对满分带（60分）条件：数值证据均来自落盘的 metrics.json 与 evidence_table.csv，逐字核对如下——(i) total_rows=100886、unique_gaia=100886，满足唯一源数=行数；(ii) SpType 无冒号口径六类 high-confidence 计数 DA 77330 / DB 5688 / DC 4082 / DO 215 / DQ 601 / DZ 1272，全部落入 Table 2 ±50 区间（如 DA∈[77280,77380]、DB∈[5638,5738] 等），合计 89188（±10 内），uncertain=11698（±10 内）；(iii) da_fraction=0.7665087326 即 76.65% ∈ [76.0%,77.3%]，high_conf_fraction=0.8840473406 即 88.40% ∈ [87.9%,88.9%]；(iv) 同时报告 argmax 口径（DA 83963 等）并解释两位小数舍入与冒号判定基于未舍入概率的差异；n_max_prob_ge_065=89388 亦与冒号规则（89188）明确区分；(v) n_teff_neg999=1396、n_da_teff_gt_300000_all=68，与论文 §4.2（1080/34）如实对照并做版本漂移讨论。五条件全中且数值均有落盘证据支撑，A=60。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示：metrics.json 存在、evidence_table.csv 存在（含 class,n_high_conf,n_uncertain,n_argmax,frac_high_conf 全部要求列）、可运行代码 analyze_gaia_wd.py 存在；证据文件内部数值与报告严格一致（如 DA high-conf=77330、Teff=-999=1396、uncertain 逐类合计 11698），无抄论文数字嫌疑（论文锚值 1080/34 与实测 1396/68 被明确区分）。符合『有证据文件且数值与报告严格一致、可核对』最高档，B=40。独立重算未执行：本裁判未实际运行该 Python 脚本从冻结数据重算，依据提交物内部一致性与代码逻辑判定，特此标注。

## 证据与重算说明

独立重算未执行。关键实测数抽查（来自落盘证据）：total_rows=100886，unique_gaia=100886；DA high-conf=77330，DB=5688，DC=4082，DO=215，DQ=601，DZ=1272，合计 89188，uncertain=11698；DA 占比 76.65%（0.7665087326），HC 占比 88.40%（0.8840473406）；argmax DA=83963；max(P)≥0.65=89388；Teff=-999=1396；DA Teff>300000K 全部=68、high-conf 子集=54。metrics.json 与 evidence_table.csv、report.md/claim.md 中数值完全一致。

## 结论

- **科学结论**: `supported`
- 亮点: 核心统计（行数、逐类 high-confidence 计数、89,188/11,698）与论文 Table 2 完全一致，且同时完成 SpType 冒号与 argmax 两种口径交叉验证并清晰归因舍入差异；对 Teff=-999 与 68/34 的版本漂移做了如实报告和归因，证据链完整。
- 不足: 本裁判未执行独立重算，B 维度满分依据为证据文件存在、列完整且内部数值与报告严格一致，而非裁判亲自跑代码验证；提交物本身未见明显弱点。