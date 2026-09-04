# EVAL REPORT v5: 2505.01415_everglades_water_level

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 69.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **41.0** | 60 | A1: 核心交付物完整，包含代码、evidence_table、详细报告及多维度的metrics CSV，得12分。A2: 成功复现了claim(a)深度模型优于线性模型和claim(b)线性模型长horizon显著退化的核心效应；但claim(c) Chronos最优未能复现且方向相反（contradicted），且NBEATS等具体模型绝对数值偏离锚值。整体定性趋势部分匹配，受限于partially_supported硬上限，A2给14分。A3: 防泄漏设计严密（标准化仅用训练段、测试段隔离），提供verify_data脚本与固定种子，方法sound且可复现，得15分。 |
| B 证据真实性/实际复现 | 28.0 | 40 | 磁盘扫描显示证据等级为2，包含evidence_table.csv、data_facts.json及大量按模型和站点分解的metrics CSV，内部数值与报告严格自洽。但受限于partially_supported结论的硬上限（B≤28），给28分。 |

## A 核心结果达成度（41.0/60 = A1 12.0 + A2 14.0 + A3 15.0）

A1: 核心交付物完整，包含代码、evidence_table、详细报告及多维度的metrics CSV，得12分。A2: 成功复现了claim(a)深度模型优于线性模型和claim(b)线性模型长horizon显著退化的核心效应；但claim(c) Chronos最优未能复现且方向相反（contradicted），且NBEATS等具体模型绝对数值偏离锚值。整体定性趋势部分匹配，受限于partially_supported硬上限，A2给14分。A3: 防泄漏设计严密（标准化仅用训练段、测试段隔离），提供verify_data脚本与固定种子，方法sound且可复现，得15分。

## B 证据真实性/实际复现（28.0/40）

磁盘扫描显示证据等级为2，包含evidence_table.csv、data_facts.json及大量按模型和站点分解的metrics CSV，内部数值与报告严格自洽。但受限于partially_supported结论的硬上限（B≤28），给28分。

## 证据与重算说明

独立重算未执行。关键实测数：MLPResidual_mc0.1 28d MAE=0.298，NLinear=0.397，DLinear=0.451，Chronos_c512=0.348。数据行数1411，日期范围正确，均有落盘CSV与JSON支撑。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 防泄漏设计严谨，证据文件极其详实且多维分解，对未能复现的绝对数值和Chronos劣势进行了客观的局限性分析。
- 不足: NBEATS等经典模型未能复现论文优势，且线性模型间的相对退化幅度排序与论文锚值相反，Chronos受限于本地小权重未能验证claim c。