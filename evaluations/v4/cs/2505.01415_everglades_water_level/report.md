# EVAL REPORT v3: 2505.01415_everglades_water_level

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 74.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 39.0 | 60 | A1: 最佳MLP(0.298)与线性(0.451)排序正确，数值偏离锚值，落入22分带。A2: 线性退化增幅均≥50%，但DLinear增幅(69%)<NLinear(83%)，未满足附加排序条件，得13分。A3: 运行Chronos(0.348)但劣于最佳任务特定(0.298)，方向不符得4分。A4站点难度方向一致不扣分。总计39分。 |
| B 证据真实性/实际复现 | 35.0 | 40 | 磁盘扫描显示证据等级为2，虽无metrics.json，但包含evidence_table.csv及大量按模型、站点、lead分解的metrics CSV，且与data_facts.json及报告数值严格自洽，给35分。 |

## A 核心结果达成度（39.0/60）

A1: 最佳MLP(0.298)与线性(0.451)排序正确，数值偏离锚值，落入22分带。A2: 线性退化增幅均≥50%，但DLinear增幅(69%)<NLinear(83%)，未满足附加排序条件，得13分。A3: 运行Chronos(0.348)但劣于最佳任务特定(0.298)，方向不符得4分。A4站点难度方向一致不扣分。总计39分。

## B 证据真实性/实际复现（35.0/40）

磁盘扫描显示证据等级为2，虽无metrics.json，但包含evidence_table.csv及大量按模型、站点、lead分解的metrics CSV，且与data_facts.json及报告数值严格自洽，给35分。

## 证据与重算说明

独立重算未执行。关键实测数：MLPResidual_mc0.1 28d MAE=0.298，DLinear=0.451，NLinear=0.397，Chronos_c512=0.348。数据行数1411，日期范围正确，均有落盘CSV支撑。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 防泄漏设计严谨，证据文件极其详实且多维分解，对未能复现的绝对数值和Chronos劣势进行了客观的局限性分析。
- 不足: NBEATS等经典模型未能复现论文优势，且线性模型间的相对退化幅度排序与论文锚值相反，Chronos受限于本地小权重未能验证claim c。