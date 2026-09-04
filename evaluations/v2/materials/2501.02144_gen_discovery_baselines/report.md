# EVAL REPORT v2: 2501.02144_gen_discovery_baselines

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（deepseek-v4-flash）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1：agent报告中位ΔEd实测值（meV/atom）为 Random=409.5、Ion-Exchange=85.5、CrystaLLM=442.0、CDVAE=207.0、FTCP=205.5、MatterGen=188.5。逐项对照PAPER_ANCHOR容差：Random 409.5∈[399,419]✓、IonX 85.5∈[80,90]✓、CrystaLLM 442.0∈[432,452]✓、CDVAE 207.0∈[202,212]✓、FTCP 205.5∈[200,210]✓（论文205，容差含舍入差）、MatterGen 188.5∈[183,193]✓；排序为 IonX<MatterGen<FTCP<CDVAE<Random<CrystaLLM，与rubric满分排序完全一致。证据绑定：metrics.json 与 evidence_table.csv 均落盘且数值一致，故给满分带20分。A2：稳定性率实测值 Random=1.4%、IonX=9.2%、CrystaLLM=2.4%、CDVAE=1.8%、FTCP=2.0%、MatterGen=3.0%，全部在±1.0pp容差内（如9.2%∈[8.2,10.2]✓）；结论明确区分'仅离子交换显著更优'、生成模型居间，方向正确，证据落盘，给20分。A3：分布证据落盘（q80：IonX=190.0、Random=804.2、CrystaLLM=806.2，均>600量级；CDVAE=340.2、FTCP=345.2、MatterGen=311.4居中），IonX分布最紧、CrystaLLM/Random最分散，与论文锚E方向一致；权衡讨论基于论文上下文明确标注'新颖性率无法从冻结数据重算'并给出方向性支持，符合rubric满分条件，给20分。综上A=60。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示 metrics.json 与 evidence_table.csv 均存在且内容完整，可核对；evidence_table.csv 中 Random 中位 Ed=409.5、Ion-Exchange 稳定性率=9.2% 与 metrics.json 和 solution.md 报告严格一致，其余4方法稳定性率（2.4/1.8/2.0/3.0）亦与报告一致。提交代码 analyze_baselines.py 从CSV直接计算中位数/稳定性率/分位数并做SHA-256校验，无硬编码数值或篡改痕迹，属于'有证据文件且数值与报告严格一致、可核对'的最高档，故B=40。未进行独立重算（在证据说明中标注）。 |

## A 核心结果达成度（60/60）

A1：agent报告中位ΔEd实测值（meV/atom）为 Random=409.5、Ion-Exchange=85.5、CrystaLLM=442.0、CDVAE=207.0、FTCP=205.5、MatterGen=188.5。逐项对照PAPER_ANCHOR容差：Random 409.5∈[399,419]✓、IonX 85.5∈[80,90]✓、CrystaLLM 442.0∈[432,452]✓、CDVAE 207.0∈[202,212]✓、FTCP 205.5∈[200,210]✓（论文205，容差含舍入差）、MatterGen 188.5∈[183,193]✓；排序为 IonX<MatterGen<FTCP<CDVAE<Random<CrystaLLM，与rubric满分排序完全一致。证据绑定：metrics.json 与 evidence_table.csv 均落盘且数值一致，故给满分带20分。A2：稳定性率实测值 Random=1.4%、IonX=9.2%、CrystaLLM=2.4%、CDVAE=1.8%、FTCP=2.0%、MatterGen=3.0%，全部在±1.0pp容差内（如9.2%∈[8.2,10.2]✓）；结论明确区分'仅离子交换显著更优'、生成模型居间，方向正确，证据落盘，给20分。A3：分布证据落盘（q80：IonX=190.0、Random=804.2、CrystaLLM=806.2，均>600量级；CDVAE=340.2、FTCP=345.2、MatterGen=311.4居中），IonX分布最紧、CrystaLLM/Random最分散，与论文锚E方向一致；权衡讨论基于论文上下文明确标注'新颖性率无法从冻结数据重算'并给出方向性支持，符合rubric满分条件，给20分。综上A=60。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示 metrics.json 与 evidence_table.csv 均存在且内容完整，可核对；evidence_table.csv 中 Random 中位 Ed=409.5、Ion-Exchange 稳定性率=9.2% 与 metrics.json 和 solution.md 报告严格一致，其余4方法稳定性率（2.4/1.8/2.0/3.0）亦与报告一致。提交代码 analyze_baselines.py 从CSV直接计算中位数/稳定性率/分位数并做SHA-256校验，无硬编码数值或篡改痕迹，属于'有证据文件且数值与报告严格一致、可核对'的最高档，故B=40。未进行独立重算（在证据说明中标注）。

## 证据与重算说明

独立重算未执行。磁盘扫描确认 metrics.json 与 results/evidence_table.csv 存在。关键实测数：Random 中位ΔEd=409.5 meV/atom（锚值409–410）、Ion-Exchange 稳定性率=9.2%（与锚值9.2%一致）、MatterGen 中位ΔEd=188.5 meV/atom、FTCP 中位ΔEd=205.5 meV/atom（论文205，舍入差）。代码中SHA-256 computed 与 expected 全部一致，证据链完整。

## 结论

- **科学结论**: `supported`
- 亮点: 完美复现论文Table 1核心统计（中位ΔEd与稳定性率），数值、排序与容差全部命中，且分布分析与'仅离子交换显著更优'的结论方向正确；证据文件落盘且与报告严格一致。
- 不足: 报告引用论文新颖性率等上下文值时虽明确标注无法重算，但未在evidence表中区分实测/引用列，建议以显式列隔离；代码中部分checksum初始化为None后从tsv填充，逻辑略有冗余但无功能缺陷。