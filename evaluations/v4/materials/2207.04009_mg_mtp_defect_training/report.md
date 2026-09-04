# EVAL REPORT v3: 2207.04009_mg_mtp_defect_training

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 50.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 30.0 | 60 | A1数据统计正确（Everything 17210，EverythingNoShear 12833）且有CSV落盘；A3主论断验证成功，MTP最优RMSE 4.367 meV/atom，经典势845.95 meV/atom，验证了1-2个数量级优势；但A2未核查DFT收敛参数。受证据等级1硬约束，A上限为35，综合给30分。 |
| B 证据真实性/实际复现 | 20.0 | 40 | 磁盘证据扫描显示metrics.json和evidence_table.csv缺失，判定为证据等级1（部分证据），B必须在[11,29]区间。Agent提供了5个详实的结果CSV文件和可运行代码，但缺乏规范化的证据表，给20分。 |

## A 核心结果达成度（30.0/60）

A1数据统计正确（Everything 17210，EverythingNoShear 12833）且有CSV落盘；A3主论断验证成功，MTP最优RMSE 4.367 meV/atom，经典势845.95 meV/atom，验证了1-2个数量级优势；但A2未核查DFT收敛参数。受证据等级1硬约束，A上限为35，综合给30分。

## B 证据真实性/实际复现（20.0/40）

磁盘证据扫描显示metrics.json和evidence_table.csv缺失，判定为证据等级1（部分证据），B必须在[11,29]区间。Agent提供了5个详实的结果CSV文件和可运行代码，但缺乏规范化的证据表，给20分。

## 证据与重算说明

独立重算未执行。关键实测数值：Everything数据集17210结构，EverythingNoShear 12833结构；MTP最优RMSE 4.367 meV/atom；经典对势RMSE 845.95 meV/atom。缺失metrics.json和evidence_table.csv，触发证据等级1约束。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 完整实现了MTP拟合和经典势对比，用实际数据验证了论文核心论断的数值优势；提供了详细的数据统计和可复现代码。
- 不足: 未核查DFT收敛参数，且未按照任务要求输出规范的metrics.json和evidence_table.csv，导致证据真实性评分受限。