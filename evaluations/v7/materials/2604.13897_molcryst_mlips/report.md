# EVAL REPORT v7: 2604.13897_molcryst_mlips

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 46.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 6.0 | 12 | |
| A2 科学结论保真 | 10.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **31.0** | 60 | A1(6分)：产出了详尽的数据统计CSV和代码，但缺失任务明确要求的 claim.md、report.md 和 metrics.json，属于有明显缺口的交付。A2(10分)：论文核心claim为微调达到能量MAE 0.141、力MAE 0.648；Agent因无基础模型权重仅做from-scratch训练，实测误差偏离近10倍，未能复现核心精度效应，属于部分不支持，受partially_supported硬上限约束给10分。A3(15分)：数据解析与代理训练方法sound，固定种子，无数据泄漏，单位换算正确，代码可由提交物复算。 |
| B 真值一致性/可验证性 | 15.0 | 40 | truth_check=diverged | 逐条比对：1. 体系数：agent识别10个体系文件（含acridine等） vs 锚点10体系（含acridine扩展） → 吻合；2. acridine_train批次数：agent报2318 vs 锚点>1000 → 吻合；3. 能量误差：agent报1.11 kJ/mol/atom (11.53 meV) vs 锚点0.141 kJ/mol/atom → 严重偏离（约8倍）；4. 力误差：agent报11.17 kJ/mol/Å (115.79 meV/Å) vs 锚点0.648 kJ/mol/Å → 严重偏离（约17倍）。核心模型指标量级错误，判定为diverged。 |

## A 核心结果达成度（31.0/60 = A1 6.0 + A2 10.0 + A3 15.0）

A1(6分)：产出了详尽的数据统计CSV和代码，但缺失任务明确要求的 claim.md、report.md 和 metrics.json，属于有明显缺口的交付。A2(10分)：论文核心claim为微调达到能量MAE 0.141、力MAE 0.648；Agent因无基础模型权重仅做from-scratch训练，实测误差偏离近10倍，未能复现核心精度效应，属于部分不支持，受partially_supported硬上限约束给10分。A3(15分)：数据解析与代理训练方法sound，固定种子，无数据泄漏，单位换算正确，代码可由提交物复算。

## B 真值一致性/可验证性（15.0/40）[truth_check=diverged]

逐条比对：1. 体系数：agent识别10个体系文件（含acridine等） vs 锚点10体系（含acridine扩展） → 吻合；2. acridine_train批次数：agent报2318 vs 锚点>1000 → 吻合；3. 能量误差：agent报1.11 kJ/mol/atom (11.53 meV) vs 锚点0.141 kJ/mol/atom → 严重偏离（约8倍）；4. 力误差：agent报11.17 kJ/mol/Å (115.79 meV/Å) vs 锚点0.648 kJ/mol/Å → 严重偏离（约17倍）。核心模型指标量级错误，判定为diverged。

## 证据与重算说明

独立重算未执行。关键实测数：acridine_train构型数18544，批次数2318；resora代理模型验证集RMSE_E_per_atom=11.53 meV（约1.11 kJ/mol/atom），RMSE_F=115.79 meV/A（约11.17 kJ/mol/Å），均有对应日志和CSV支撑。但缺失claim.md、metrics.json和report.md等关键结论文件。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 数据层解析极其详尽，20个h5文件的批次结构和统计完整且内部高度一致；代理模型训练脚本规范，对无法复现微调精度的局限性分析客观合理。
- 不足: 缺失任务要求的claim.md、report.md和metrics.json标准文件；受限于缺少基础模型权重，未能复现论文核心的微调后高精度量级，实测误差与真值偏离达10倍以上。