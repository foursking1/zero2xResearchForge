# EVAL REPORT v5: 2604.13897_molcryst_mlips

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 58.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 8.0 | 12 | |
| A2 科学结论保真 | 10.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **33.0** | 60 | A1：产出了详尽的数据统计、结构解析和代理模型训练代码及结果，但缺失任务明确要求的 claim.md、report.md 和 metrics.json，属于实质性产出但有明显缺口，给 8 分。A2：论文核心 claim 为微调达到能量 MAE 0.141、力 MAE 0.648；Agent 因无基础模型权重仅做 from-scratch 训练，实测 RMSE 为 1.11 和 11.17，偏差近 10 倍，未能复现核心精度效应，属于部分不支持/弱相关，且受 partially_supported 硬上限约束，给 10 分。A3：数据解析与代理训练方法 sound，固定种子，无数据泄漏，单位换算正确，可由提交物复算，给 15 分。 |
| B 证据真实性/实际复现 | 25.0 | 40 | 磁盘证据扫描显示 evidence_table.csv、统计 JSON 及训练日志详实且内部严格自洽，但缺失关键的 metrics.json 文件，属于“部分证据”分档 [11,29]。结合 partially_supported 结论的硬上限（≤28），给 25 分。 |

## A 核心结果达成度（33.0/60 = A1 8.0 + A2 10.0 + A3 15.0）

A1：产出了详尽的数据统计、结构解析和代理模型训练代码及结果，但缺失任务明确要求的 claim.md、report.md 和 metrics.json，属于实质性产出但有明显缺口，给 8 分。A2：论文核心 claim 为微调达到能量 MAE 0.141、力 MAE 0.648；Agent 因无基础模型权重仅做 from-scratch 训练，实测 RMSE 为 1.11 和 11.17，偏差近 10 倍，未能复现核心精度效应，属于部分不支持/弱相关，且受 partially_supported 硬上限约束，给 10 分。A3：数据解析与代理训练方法 sound，固定种子，无数据泄漏，单位换算正确，可由提交物复算，给 15 分。

## B 证据真实性/实际复现（25.0/40）

磁盘证据扫描显示 evidence_table.csv、统计 JSON 及训练日志详实且内部严格自洽，但缺失关键的 metrics.json 文件，属于“部分证据”分档 [11,29]。结合 partially_supported 结论的硬上限（≤28），给 25 分。

## 证据与重算说明

独立重算未执行。关键实测数：acridine_train 构型数 18544，批次数 2318；resora 代理模型验证集 RMSE_E_per_atom=11.53 meV（约 1.11 kJ/mol/atom），RMSE_F=115.79 meV/A（约 11.17 kJ/mol/Å），均有对应日志和 CSV 支撑。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 数据层解析极其详尽，20个 h5 文件的批次结构和统计完整且内部高度一致；代理模型训练脚本规范，对无法复现微调精度的局限性分析客观合理。
- 不足: 缺失任务要求的 claim.md、report.md 和 metrics.json 标准文件；受限于缺少基础模型权重，未能复现论文核心的微调后高精度量级。