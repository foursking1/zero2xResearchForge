# EVAL REPORT v7: 2207.04009_mg_mtp_defect_training

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 59.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 6.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 13.0 | 15 | |
| **A 合计** | **33.0** | 60 | A1(6分)：Agent产出了数据统计和势拟合/解析的CSV结果文件，但缺失了TASK.md明确要求的claim.md、metrics.json和evidence_table.csv，属于有机器可读结果但存在明显必需输出缺口。A2(14分)：Agent通过解析h5归档和自行拟合经典势，成功验证了MTP精度优于经典势1-2个数量级的核心claim，与论文真值高度一致；但受限于Agent自评结论为partially_supported，触发A2≤15的硬上限，故给14分。A3(13分)：方法严谨，提供了完整可运行的Python代码，解析了cfg和h5文件，并自行实现了经典对势和代理势的拟合对照，可复现性强。 |
| B 真值一致性/可验证性 | 26.0 | 40 | truth_check=matched | agent数 4.367 meV/atom (MTP最优RMSE) vs 锚点 ~10 meV/atom 量级 → 吻合；agent数 845.95 meV/atom (经典势RMSE) 与 MTP 相差约200倍 vs 锚点 低1-2个数量级 → 吻合；agent数 Everything 17210 / EverythingNoShear 12833 vs 锚点 Everything与Everything±Shear两套训练集 → 吻合。核心指标均与论文真值匹配，但受partially_supported结论硬上限(B≤28)限制，给26分。 |

## A 核心结果达成度（33.0/60 = A1 6.0 + A2 14.0 + A3 13.0）

A1(6分)：Agent产出了数据统计和势拟合/解析的CSV结果文件，但缺失了TASK.md明确要求的claim.md、metrics.json和evidence_table.csv，属于有机器可读结果但存在明显必需输出缺口。A2(14分)：Agent通过解析h5归档和自行拟合经典势，成功验证了MTP精度优于经典势1-2个数量级的核心claim，与论文真值高度一致；但受限于Agent自评结论为partially_supported，触发A2≤15的硬上限，故给14分。A3(13分)：方法严谨，提供了完整可运行的Python代码，解析了cfg和h5文件，并自行实现了经典对势和代理势的拟合对照，可复现性强。

## B 真值一致性/可验证性（26.0/40）[truth_check=matched]

agent数 4.367 meV/atom (MTP最优RMSE) vs 锚点 ~10 meV/atom 量级 → 吻合；agent数 845.95 meV/atom (经典势RMSE) 与 MTP 相差约200倍 vs 锚点 低1-2个数量级 → 吻合；agent数 Everything 17210 / EverythingNoShear 12833 vs 锚点 Everything与Everything±Shear两套训练集 → 吻合。核心指标均与论文真值匹配，但受partially_supported结论硬上限(B≤28)限制，给26分。

## 证据与重算说明

独立重算未执行。关键实测数：MTP最优RMSE 4.367 meV/atom (level=24, cutoff=8.2)，经典势RMSE 845.95 meV/atom，Everything数据集构型数17210。磁盘扫描显示缺失规范的metrics.json、claim.md和evidence_table.csv，证据等级判定为1（部分证据）。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `matched`
- 亮点: 成功从冻结数据中解析出MTP预测结果并自行拟合了经典势作为对照，用扎实的数据完美验证了MTP精度优于经典势1-2个数量级的核心论断。
- 不足: 未按照任务要求输出claim.md、metrics.json等规范化证据文件，且未核查DFT收敛参数，导致结论保守评为partially_supported并触发硬上限扣分。