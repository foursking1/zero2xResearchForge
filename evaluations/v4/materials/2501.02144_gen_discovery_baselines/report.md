# EVAL REPORT v3: 2501.02144_gen_discovery_baselines

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1中位ΔEd实测值（Random=409.5, IonX=85.5, CrystaLLM=442.0, CDVAE=207.0, FTCP=205.5, MatterGen=188.5）与锚值偏差均≤1meV/atom（远小于2%），排序完全正确；A2稳定性率实测值（1.4%, 9.2%, 2.4%, 1.8%, 2.0%, 3.0%）精确命中锚值，结论方向正确；A3分布分位数（如q80）落盘且权衡讨论方向正确并声明局限。全部核心子项精确命中，A=60。 |
| B 证据真实性/实际复现 | 40 | 40 | 证据等级=2（齐全自洽）。metrics.json与evidence_table.csv均落盘且数值严格一致；代码analyze_baselines.py包含完整的SHA-256校验逻辑，metrics.json中checksums_ok全部为true，无硬编码或篡改痕迹，属于有校验证据的最高档，B=40。 |

## A 核心结果达成度（60/60）

A1中位ΔEd实测值（Random=409.5, IonX=85.5, CrystaLLM=442.0, CDVAE=207.0, FTCP=205.5, MatterGen=188.5）与锚值偏差均≤1meV/atom（远小于2%），排序完全正确；A2稳定性率实测值（1.4%, 9.2%, 2.4%, 1.8%, 2.0%, 3.0%）精确命中锚值，结论方向正确；A3分布分位数（如q80）落盘且权衡讨论方向正确并声明局限。全部核心子项精确命中，A=60。

## B 证据真实性/实际复现（40/40）

证据等级=2（齐全自洽）。metrics.json与evidence_table.csv均落盘且数值严格一致；代码analyze_baselines.py包含完整的SHA-256校验逻辑，metrics.json中checksums_ok全部为true，无硬编码或篡改痕迹，属于有校验证据的最高档，B=40。

## 证据与重算说明

独立重算未执行。关键实测数：Random中位ΔEd=409.5 meV/atom，Ion-Exchange稳定性率=9.2%，MatterGen中位ΔEd=188.5 meV/atom。metrics.json与evidence_table.csv数值一致，checksums_ok全部为true，证据链完整。

## 结论

- **科学结论**: `supported`
- 亮点: 完美复现论文Table 1核心统计指标，数值与排序精确命中锚值；证据链完整，代码包含数据完整性校验（SHA-256），报告严谨区分了实测值与不可重算的上下文值。
- 不足: 代码中部分checksum初始化为None后从tsv填充，逻辑略显冗余，但不影响正确性与可运行性。