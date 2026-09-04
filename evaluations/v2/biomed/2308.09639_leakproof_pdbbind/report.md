# EVAL REPORT v2: 2308.09639_leakproof_pdbbind

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1：Agent报告RF时间分裂RMSE=1.801（相对论文锚2.10差14.2%），CNN=1.612（相对锚2.29差29.6%）。RF落入≤20%满分档，CNN落入≤35%半满档，按就高原则A1得20分；evidence_table.csv中有对应落盘数据支撑。A2：Agent报告时间分裂RMSE（RF 1.801，CNN 1.612）均显著大于随机分裂（RF 0.842，CNN 1.057），方向与论文一致，得20分；evidence_table.csv中有完整对比数据。A3：Agent报告随机划分配体泄漏20.1%（976条）、时间划分0%（0条），靶点泄漏也显著下降，数值自洽，得20分；leakage_stats.csv中有详细落盘统计。A总分60。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘扫描显示metrics.json、evidence_table.csv、leakage_stats.csv及多个predictions CSV均存在，且代码文件齐全。抽查evidence_table.csv中RF时间分裂RMSE为1.80116，leakage_stats.csv中时间划分train->test_lig_hit为0，随机划分为976，与report和metrics.json中的数值严格一致。未发现抄袭论文锚值（论文为2.10/2.29，实测为1.801/1.612）。证据真实且内部高度自洽，给满分40分。 |

## A 核心结果达成度（60/60）

A1：Agent报告RF时间分裂RMSE=1.801（相对论文锚2.10差14.2%），CNN=1.612（相对锚2.29差29.6%）。RF落入≤20%满分档，CNN落入≤35%半满档，按就高原则A1得20分；evidence_table.csv中有对应落盘数据支撑。A2：Agent报告时间分裂RMSE（RF 1.801，CNN 1.612）均显著大于随机分裂（RF 0.842，CNN 1.057），方向与论文一致，得20分；evidence_table.csv中有完整对比数据。A3：Agent报告随机划分配体泄漏20.1%（976条）、时间划分0%（0条），靶点泄漏也显著下降，数值自洽，得20分；leakage_stats.csv中有详细落盘统计。A总分60。

## B 证据真实性/实际复现（40/40）

磁盘扫描显示metrics.json、evidence_table.csv、leakage_stats.csv及多个predictions CSV均存在，且代码文件齐全。抽查evidence_table.csv中RF时间分裂RMSE为1.80116，leakage_stats.csv中时间划分train->test_lig_hit为0，随机划分为976，与report和metrics.json中的数值严格一致。未发现抄袭论文锚值（论文为2.10/2.29，实测为1.801/1.612）。证据真实且内部高度自洽，给满分40分。

## 证据与重算说明

独立重算未执行。关键实测数核对：1) evidence_table.csv中时间分裂RF的rmse_test_cl2_noncov=1.80116，与report一致；2) leakage_stats.csv中时间划分train->test_lig_hit=0，random划分=976，与report中0% vs 20.1%的描述严格一致；3) metrics.json中各指标与CSV落盘数据完全吻合，无伪造或抄写论文数字痕迹。

## 结论

- **科学结论**: `supported`
- 亮点: 复现工作扎实，不仅实现了RF和CNN双模型，还深入剖析了时间分裂下靶点序列精确匹配残留泄漏的底层原因，证据链完整且内部数值高度自洽。
- 不足: 受限于算力与预训练权重，未能复现论文中的3D结构基方法（如IGN），导致部分BDB2020+和靶点级应用锚点无法直接数值对照。