# EVAL REPORT v3: 2308.05572_gaia_wd_xp_class

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v3（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | 逐项核对满分带条件：(i) total_rows=100886, unique_gaia=100886，满足；(ii) 六类high-confidence计数(DA 77330/DB 5688/DC 4082/DO 215/DQ 601/DZ 1272)与Table 2完全一致，总数89188，uncertain 11698，满足；(iii) DA占比76.65%，HC占比88.40%，落入指定区间，满足；(iv) 报告了argmax口径(DA 83963)并解释了舍入差异，满足；(v) 如实报告Teff=-999为1396、DA Teff>300000K为68并做了版本漂移讨论，满足。所有数值均有metrics.json和evidence_table.csv落盘支撑，A=60。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示证据等级为2（齐全自洽）。metrics.json与evidence_table.csv均存在且包含所有要求列，数值与报告严格一致。代码采用正确的定宽字节切片解析，内部逻辑严密，无抄数嫌疑（如实区分了论文锚值与实测漂移值）。符合最高档标准，B=40。 |

## A 核心结果达成度（60/60）

逐项核对满分带条件：(i) total_rows=100886, unique_gaia=100886，满足；(ii) 六类high-confidence计数(DA 77330/DB 5688/DC 4082/DO 215/DQ 601/DZ 1272)与Table 2完全一致，总数89188，uncertain 11698，满足；(iii) DA占比76.65%，HC占比88.40%，落入指定区间，满足；(iv) 报告了argmax口径(DA 83963)并解释了舍入差异，满足；(v) 如实报告Teff=-999为1396、DA Teff>300000K为68并做了版本漂移讨论，满足。所有数值均有metrics.json和evidence_table.csv落盘支撑，A=60。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示证据等级为2（齐全自洽）。metrics.json与evidence_table.csv均存在且包含所有要求列，数值与报告严格一致。代码采用正确的定宽字节切片解析，内部逻辑严密，无抄数嫌疑（如实区分了论文锚值与实测漂移值）。符合最高档标准，B=40。

## 证据与重算说明

独立重算未执行。关键实测数抽查（来自落盘证据）：total_rows=100886，DA high-conf=77330，Teff=-999=1396，DA Teff>300000K=68。metrics.json、evidence_table.csv与报告中的数值完全一致，证据链完整自洽。

## 结论

- **科学结论**: `supported`
- 亮点: 完美复现了论文的所有核心统计数据，代码解析逻辑严谨规范，对版本漂移和口径差异的分析极其透彻，证据文件齐全且内部高度一致。
- 不足: 无明显弱点，各项指标与提交物均高质量达标，裁判未执行独立代码重算但落盘证据已充分支撑结论。