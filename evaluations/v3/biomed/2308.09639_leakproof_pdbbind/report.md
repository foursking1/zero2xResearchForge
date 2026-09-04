# EVAL REPORT v3: 2308.09639_leakproof_pdbbind

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v3（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1：Agent报告RF时间分裂RMSE=1.801（相对论文锚2.10差14.2%），落入≤20%满分档，得20分；CNN相对差29.6%落入半满档，按就高原则A1得20分。A2：时间分裂RMSE（RF 1.801，CNN 1.612）均显著大于随机分裂（RF 0.842，CNN 1.057），方向与论文一致，得20分。A3：随机划分配体泄漏20.1%（976条），时间划分0%（0条），靶点泄漏也显著下降，数值自洽，得20分。A总分60。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示证据等级为2（齐全自洽）。metrics.json、evidence_table.csv、leakage_stats.csv及代码文件均存在。抽查evidence_table.csv中RF时间分裂RMSE为1.80116，leakage_stats.csv中时间划分train->test_lig_hit为0、随机为976，与报告严格一致。未发现抄袭论文锚值，给满分40。 |

## A 核心结果达成度（60/60）

A1：Agent报告RF时间分裂RMSE=1.801（相对论文锚2.10差14.2%），落入≤20%满分档，得20分；CNN相对差29.6%落入半满档，按就高原则A1得20分。A2：时间分裂RMSE（RF 1.801，CNN 1.612）均显著大于随机分裂（RF 0.842，CNN 1.057），方向与论文一致，得20分。A3：随机划分配体泄漏20.1%（976条），时间划分0%（0条），靶点泄漏也显著下降，数值自洽，得20分。A总分60。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示证据等级为2（齐全自洽）。metrics.json、evidence_table.csv、leakage_stats.csv及代码文件均存在。抽查evidence_table.csv中RF时间分裂RMSE为1.80116，leakage_stats.csv中时间划分train->test_lig_hit为0、随机为976，与报告严格一致。未发现抄袭论文锚值，给满分40。

## 证据与重算说明

独立重算未执行。关键实测数核对：1) evidence_table.csv中时间分裂RF的rmse_test_cl2_noncov=1.80116，与report一致；2) leakage_stats.csv中时间划分train->test_lig_hit=0，random划分=976，与报告中0% vs 20.1%的描述严格一致；内部数值高度自洽。

## 结论

- **科学结论**: `supported`
- 亮点: 复现工作极其扎实，不仅完成了RF和CNN双模型训练验证了方向性结论，还深入剖析了时间分裂下靶点序列精确匹配残留泄漏的底层原因，证据链完整且内部数值高度自洽。
- 不足: 受限于算力与预训练权重，未能复现论文中的3D结构基方法（如IGN），导致BDB2020+和靶点级应用的部分锚点无法进行直接数值对照。