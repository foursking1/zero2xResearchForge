# EVAL REPORT v5: 2207.04009_mg_mtp_defect_training

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 58.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 8.0 | 12 | |
| A2 科学结论保真 | 15.0 | 33 | |
| A3 方法严谨与可复现 | 10.0 | 15 | |
| **A 合计** | **33.0** | 60 | A1(8分)：产出了数据统计和势拟合结果CSV，但未完成DFT收敛参数核查，且缺失规范的metrics.json/evidence_table，核心交付物有明显缺口。A2(15分)：MTP最优RMSE 4.367 meV/atom，经典势845.95 meV/atom，成功复现了MTP比经典势低1-2个数量级的核心claim，效应匹配度高；但受限于agent自评结论为partially_supported，触发硬上限A2≤15。A3(10分)：方法基本sound，通过解析h5和cfg文件进行统计和拟合，但未核查DFT收敛参数，存在轻微方法论顾虑。 |
| B 证据真实性/实际复现 | 25.0 | 40 | 磁盘证据扫描显示缺失metrics.json和evidence_table.csv，但存在5个结果CSV文件和可运行代码，判定为证据等级1（部分证据），B必须在[11,29]区间。结合结论标签partially_supported的硬上限(B≤28)，给25分。 |

## A 核心结果达成度（33.0/60 = A1 8.0 + A2 15.0 + A3 10.0）

A1(8分)：产出了数据统计和势拟合结果CSV，但未完成DFT收敛参数核查，且缺失规范的metrics.json/evidence_table，核心交付物有明显缺口。A2(15分)：MTP最优RMSE 4.367 meV/atom，经典势845.95 meV/atom，成功复现了MTP比经典势低1-2个数量级的核心claim，效应匹配度高；但受限于agent自评结论为partially_supported，触发硬上限A2≤15。A3(10分)：方法基本sound，通过解析h5和cfg文件进行统计和拟合，但未核查DFT收敛参数，存在轻微方法论顾虑。

## B 证据真实性/实际复现（25.0/40）

磁盘证据扫描显示缺失metrics.json和evidence_table.csv，但存在5个结果CSV文件和可运行代码，判定为证据等级1（部分证据），B必须在[11,29]区间。结合结论标签partially_supported的硬上限(B≤28)，给25分。

## 证据与重算说明

独立重算未执行。关键实测数值：Everything数据集17210结构，EverythingNoShear 12833结构；MTP最优RMSE 4.367 meV/atom；经典对势RMSE 845.95 meV/atom。缺失规范化的metrics.json和evidence_table.csv。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 完整实现了MTP拟合和经典势对比，用实际数据验证了论文核心论断的数值优势；提供了详细的数据统计和可复现代码。
- 不足: 未核查DFT收敛参数，且未按照任务要求输出规范的metrics.json和evidence_table.csv，导致证据真实性评分受限。