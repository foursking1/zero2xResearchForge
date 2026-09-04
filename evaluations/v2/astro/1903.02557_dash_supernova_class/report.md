# EVAL REPORT v2: 1903.02557_dash_supernova_class

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（deepseek-v4-flash）
- 评测时间: 2026-08-21

## 总分: 86.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 50.0 | 60 | A1(20/25)：evidence_table.csv 提供 69 条逐条结果（对象/历元/红移/ATel 标签/DASH top-1/概率/Reliable/是否匹配），匹配口径已明确（大类归并、? 归入大类、Ic-broad 单列），总体匹配率 56/64=0.875 有落盘 metrics.json 支撑；但未按 rubric 要求单独给出 Ia?/II?/Ibc? 的分型匹配率（仅在数据分布中列出 Ia? 9、II? 2、Ibc? 1，未报告这些子类的匹配率），故扣 5 分。A2(17/20)：明确给出 supported 结论，依据为总体 0.875>=0.80 且 Ia 0.907>=0.90，符合主张成立阈值；与 Table 1 对比显示 Ia 绝对差 7.7pp、II 差 14.3pp、Ibc 差 50pp（Ibc 仅 n=2）基本在 15pp 容差内；但未完成 Table 2 全量逐对象复现一致率，仅对 DES16C3bq/DES16E2aoh 两个对象做 spot-check，按 rubric 扣 3 分（得 2 分）。A3(15/15)：精确报告 69 条单批次墙钟 3.59s（setup 1.55s + forward 2.03s），远低于 <20s/212 阈值，并讨论了线性外推（约 11s/212）与机器/模型版本可迁移性。合计 20+17+15=52；由于 A1 缺分型分解、A2 未做 Table 2 全量对比，不满足'所有子项均满分带且证据齐全'，故按上述 band 给出 50/60。 |
| B 证据真实性/实际复现 | 36.0 | 40 | 磁盘证据扫描显示 metrics.json、evidence_table.csv、dash_predictions.csv、critical_checks.json、uncertainty.json、spectrum_table.csv、data_facts.json 等实测证据文件均存在，且关键数值（56/64=0.875、Ia 49/54=0.907、耗时 3.59s）在 metrics.json、evidence_table.csv、run_dash.log、report.md 之间严格一致可核对，符合 [30,40] 得分带，给 36 分。evidence_table 中 rlap 列全部为 rlap-failed: ValueError（numpy 2.x 兼容问题），但不影响核心 top-1 分类与匹配指标，且 agent 已透明标注；B2 抽查对象 DES16C3bq→Ia-norm（与论文 Ia-norm 同子类型）一致，DES16E2aoh→Ia-91bg（与论文 Ia-91T 同大类，子类型不同，已注明 v06 模型版本差异），故在 30-40 带内不取满分。独立重算未执行，本项评分仅基于磁盘证据与内部一致性核验。 |

## A 核心结果达成度（50.0/60）

A1(20/25)：evidence_table.csv 提供 69 条逐条结果（对象/历元/红移/ATel 标签/DASH top-1/概率/Reliable/是否匹配），匹配口径已明确（大类归并、? 归入大类、Ic-broad 单列），总体匹配率 56/64=0.875 有落盘 metrics.json 支撑；但未按 rubric 要求单独给出 Ia?/II?/Ibc? 的分型匹配率（仅在数据分布中列出 Ia? 9、II? 2、Ibc? 1，未报告这些子类的匹配率），故扣 5 分。A2(17/20)：明确给出 supported 结论，依据为总体 0.875>=0.80 且 Ia 0.907>=0.90，符合主张成立阈值；与 Table 1 对比显示 Ia 绝对差 7.7pp、II 差 14.3pp、Ibc 差 50pp（Ibc 仅 n=2）基本在 15pp 容差内；但未完成 Table 2 全量逐对象复现一致率，仅对 DES16C3bq/DES16E2aoh 两个对象做 spot-check，按 rubric 扣 3 分（得 2 分）。A3(15/15)：精确报告 69 条单批次墙钟 3.59s（setup 1.55s + forward 2.03s），远低于 <20s/212 阈值，并讨论了线性外推（约 11s/212）与机器/模型版本可迁移性。合计 20+17+15=52；由于 A1 缺分型分解、A2 未做 Table 2 全量对比，不满足'所有子项均满分带且证据齐全'，故按上述 band 给出 50/60。

## B 证据真实性/实际复现（36.0/40）

磁盘证据扫描显示 metrics.json、evidence_table.csv、dash_predictions.csv、critical_checks.json、uncertainty.json、spectrum_table.csv、data_facts.json 等实测证据文件均存在，且关键数值（56/64=0.875、Ia 49/54=0.907、耗时 3.59s）在 metrics.json、evidence_table.csv、run_dash.log、report.md 之间严格一致可核对，符合 [30,40] 得分带，给 36 分。evidence_table 中 rlap 列全部为 rlap-failed: ValueError（numpy 2.x 兼容问题），但不影响核心 top-1 分类与匹配指标，且 agent 已透明标注；B2 抽查对象 DES16C3bq→Ia-norm（与论文 Ia-norm 同子类型）一致，DES16E2aoh→Ia-91bg（与论文 Ia-91T 同大类，子类型不同，已注明 v06 模型版本差异），故在 30-40 带内不取满分。独立重算未执行，本项评分仅基于磁盘证据与内部一致性核验。

## 证据与重算说明

独立重算未执行。关键实测数（均来自落盘证据）：总体匹配率 56/64=0.875；Ia 49/54=0.9074；II 6/8=0.75；Ibc 1/2=0.50；5 条 Ic-broad 预测按论文口径排除；全批次墙钟 3.59s（setup 1.55s + forward 2.03s）；evidence_table 含 69 条完整行，metrics.json 数值与 report.md/run_dash.log 逐字一致。未发现抄论文数值或数据泄漏迹象；rlap 列全部为 rlap-failed 属兼容性缺陷而非数据造假，已在报告中透明声明。

## 结论

- **科学结论**: `supported`
- 亮点: 完整执行了 69 条冻结光谱的 DASH v06 推理，逐条证据表、指标 JSON 与运行日志三方一致，匹配口径和子集/模型版本局限说明清晰，速度主张（3.59s/69 条）有实测支撑。
- 不足: 未按 rubric 单独报告带?分型（Ia?/II?/Ibc?）匹配率，且未完成 Table 2 全量逐对象复现一致率（仅 spot-check 两对象）；rlap 可靠性诊断因 numpy 2.x 全部失败，削弱了 Reliable 标志的可验证性。