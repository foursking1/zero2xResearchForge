# EVAL REPORT v2: 2207.04009_mg_mtp_defect_training

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 62.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 50.0 | 60 | A1(20分): 实测数值：Everything 17210构型，EverythingNoShear 12833构型。落入「数据统计正确」满分带，有structures_summary.csv落盘支撑，给20分。A2(10分): 实测数值：无。未核查DFT收敛参数(0.6/6.4 meV/atom)，但在报告中如实承认无法复算，落入10-20分带，因无落盘抽查证据给下限10分。A3(20分): 实测数值：MTP最优RMSE 4.367 meV/atom，经典对势845.95 meV/atom。相差近200倍，落入「方向一致且有佐证」满分带，有mtp_fit_results.csv和classical_pair_rmse.csv落盘，给20分。 |
| B 证据真实性/实际复现 | 12.0 | 40 | 根据【磁盘证据扫描】明确结论，metrics.json与evidence_table.csv等指定实测证据文件缺失，触发「B必须∈[0,15]」硬规则。虽然agent提供了其他结果CSV文件，但缺乏规范化的证据表，且独立重算未执行，故给12分。 |

## A 核心结果达成度（50.0/60）

A1(20分): 实测数值：Everything 17210构型，EverythingNoShear 12833构型。落入「数据统计正确」满分带，有structures_summary.csv落盘支撑，给20分。A2(10分): 实测数值：无。未核查DFT收敛参数(0.6/6.4 meV/atom)，但在报告中如实承认无法复算，落入10-20分带，因无落盘抽查证据给下限10分。A3(20分): 实测数值：MTP最优RMSE 4.367 meV/atom，经典对势845.95 meV/atom。相差近200倍，落入「方向一致且有佐证」满分带，有mtp_fit_results.csv和classical_pair_rmse.csv落盘，给20分。

## B 证据真实性/实际复现（12.0/40）

根据【磁盘证据扫描】明确结论，metrics.json与evidence_table.csv等指定实测证据文件缺失，触发「B必须∈[0,15]」硬规则。虽然agent提供了其他结果CSV文件，但缺乏规范化的证据表，且独立重算未执行，故给12分。

## 证据与重算说明

独立重算未执行。关键实测数值：Everything数据集17210结构，EverythingNoShear 12833结构；MTP最优RMSE 4.367 meV/atom (level=24, cutoff=8.2)；经典对势RMSE 845.95 meV/atom。因缺失metrics.json和evidence_table.csv，证据链完整性受损。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 完整实现了MTP拟合和经典势对比，用实际数据验证了论文核心论断的数值优势；提供了详细的数据统计和可复现代码。
- 不足: 未核查DFT收敛参数，且未按照任务要求输出规范的metrics.json和evidence_table.csv，导致证据真实性评分受限。