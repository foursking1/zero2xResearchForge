# EVAL REPORT v3: 2501.02144_gen_discovery_baselines

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v3（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1：6个方法中位ΔEd实测值（Random=409.5, IonX=85.5, CrystaLLM=442.0, CDVAE=207.0, FTCP=205.5, MatterGen=188.5）全部落入满分容差带，排序完全正确，得20分。A2：稳定性率实测值（1.4%, 9.2%, 2.4%, 1.8%, 2.0%, 3.0%）全部在±1.0pp容差内，结论准确指出仅离子交换显著更优，得20分。A3：分布证据落盘（q80等），IonX最紧、Random/CrystaLLM最分散，方向与论文一致，权衡讨论明确标注不可重算的局限并给出方向性支持，得20分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示metrics.json与evidence_table.csv均存在且内容完整、数值严格一致；代码analyze_baselines.py从CSV直接计算统计量并做SHA-256校验，无硬编码或篡改痕迹，属于证据齐全自洽的最高档，给40分。 |

## A 核心结果达成度（60/60）

A1：6个方法中位ΔEd实测值（Random=409.5, IonX=85.5, CrystaLLM=442.0, CDVAE=207.0, FTCP=205.5, MatterGen=188.5）全部落入满分容差带，排序完全正确，得20分。A2：稳定性率实测值（1.4%, 9.2%, 2.4%, 1.8%, 2.0%, 3.0%）全部在±1.0pp容差内，结论准确指出仅离子交换显著更优，得20分。A3：分布证据落盘（q80等），IonX最紧、Random/CrystaLLM最分散，方向与论文一致，权衡讨论明确标注不可重算的局限并给出方向性支持，得20分。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示metrics.json与evidence_table.csv均存在且内容完整、数值严格一致；代码analyze_baselines.py从CSV直接计算统计量并做SHA-256校验，无硬编码或篡改痕迹，属于证据齐全自洽的最高档，给40分。

## 证据与重算说明

独立重算未执行。关键实测数：Random中位ΔEd=409.5 meV/atom、Ion-Exchange稳定性率=9.2%、MatterGen中位ΔEd=188.5 meV/atom；metrics.json与evidence_table.csv数值一致，checksums_ok全部为true，证据链完整。

## 结论

- **科学结论**: `supported`
- 亮点: 核心统计指标与论文Table 1高度吻合且排序完全正确，分布分析详实并明确区分实测值与论文上下文引用值，证据链完整且代码可复现。
- 不足: IonX q80实测190.0 meV/atom与论文CHGNet筛选后~100 meV/atom量级存在口径差异，但属方向性一致，不构成扣分；自评报告存在一定冗余。