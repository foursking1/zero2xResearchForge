# EVAL REPORT v3: 2602.13288_cloud_telemetry_ad

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v3（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 86.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 48.0 | 60 | A1(claim a): Agent覆盖了5个Microsoft含异常子组与5个模型，实测GRU全部>0（30.74, 56.82, 84.43, 31.87, 26.10），但TCN与TSMixer同样全正（如mongodb-machine-rps上TCN 15.56, TSMixer 4.41），不满足'唯一全正'条件，严格落入半满带得18分。A2(claim b): 覆盖6个NAB含异常子组，最高分归属包含Transformer、IF、TCN共3种架构，满足'无单一架构主导'且覆盖度≥4，落入满分带得30分。A维度总计48分。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘证据扫描显示metrics.json、evidence_table.csv及多组敏感性分析结果文件均齐全，且包含可运行代码。evidence_table中的实测数值（如GRU acr-1 30.7416）与报告散文严格一致，未发现照抄论文锚值的现象（如诚实报告了与论文不符的TCN全正结果），证据链完整可信，落入[30,40]区间，给38分。 |

## A 核心结果达成度（48.0/60）

A1(claim a): Agent覆盖了5个Microsoft含异常子组与5个模型，实测GRU全部>0（30.74, 56.82, 84.43, 31.87, 26.10），但TCN与TSMixer同样全正（如mongodb-machine-rps上TCN 15.56, TSMixer 4.41），不满足'唯一全正'条件，严格落入半满带得18分。A2(claim b): 覆盖6个NAB含异常子组，最高分归属包含Transformer、IF、TCN共3种架构，满足'无单一架构主导'且覆盖度≥4，落入满分带得30分。A维度总计48分。

## B 证据真实性/实际复现（38.0/40）

磁盘证据扫描显示metrics.json、evidence_table.csv及多组敏感性分析结果文件均齐全，且包含可运行代码。evidence_table中的实测数值（如GRU acr-1 30.7416）与报告散文严格一致，未发现照抄论文锚值的现象（如诚实报告了与论文不符的TCN全正结果），证据链完整可信，落入[30,40]区间，给38分。

## 证据与重算说明

独立重算未执行（受限于裁判环境），但落盘证据极其详实。关键实测数核对：Microsoft GRU application-crash-rate-1=30.7416，NAB realTraffic IsolationForest=56.121，均在evidence_table.csv与metrics.json中严格对应，且提供了seed0/seed7及strict阈值的多份交叉验证表格。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 实验管线完整严谨，不仅实现了全部5种模型与NAB标准评分，还主动提供了多随机种子与严格阈值网格的敏感性分析，防泄漏声明清晰，证据链极其扎实。
- 不足: 未能复现论文中GRU在Microsoft数据集上的'唯一全正'特性（TCN与TSMixer亦全正），这可能源于Agent采用的网格搜索校准与论文100次贝叶斯搜索在寻优能力上的客观差异。