# EVAL REPORT v3: 2604.13897_molcryst_mlips

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 65.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 30.0 | 60 | 逐项核对：A1数据统计与A2体系对照完整达成；但A3主论断验证中，论文锚值为能量MAE 0.141 kJ/mol/atom、力MAE 0.648 kJ/mol/Å，Agent实测代理模型RMSE为1.11 kJ/mol/atom和11.17 kJ/mol/Å，偏差超600%，属于明显不达标。因缺乏基础模型权重仅能from-scratch训练，核心数值子项未命中，整体落入“仅部分核心子项达成”区间，A=30。 |
| B 证据真实性/实际复现 | 35.0 | 40 | 磁盘证据扫描显示metrics.json缺失，但evidence_table.csv、h5_structure_report.json及训练日志等实测证据详实且内部严格自洽（如acridine_train 18544构型、2318批次均吻合），证据等级为2，落入“有evidence但部分缺失”分档，B=35。 |

## A 核心结果达成度（30.0/60）

逐项核对：A1数据统计与A2体系对照完整达成；但A3主论断验证中，论文锚值为能量MAE 0.141 kJ/mol/atom、力MAE 0.648 kJ/mol/Å，Agent实测代理模型RMSE为1.11 kJ/mol/atom和11.17 kJ/mol/Å，偏差超600%，属于明显不达标。因缺乏基础模型权重仅能from-scratch训练，核心数值子项未命中，整体落入“仅部分核心子项达成”区间，A=30。

## B 证据真实性/实际复现（35.0/40）

磁盘证据扫描显示metrics.json缺失，但evidence_table.csv、h5_structure_report.json及训练日志等实测证据详实且内部严格自洽（如acridine_train 18544构型、2318批次均吻合），证据等级为2，落入“有evidence但部分缺失”分档，B=35。

## 证据与重算说明

独立重算未执行。关键实测数：acridine_train构型数18544，批次数2318；resora代理模型验证集RMSE_E_per_atom=11.53 meV（约1.11 kJ/mol/atom），RMSE_F=115.79 meV/A（约11.17 kJ/mol/Å），均有对应日志和CSV支撑。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 数据层解析极其详尽，20个h5文件的批次结构和统计完整且内部高度一致；代理模型训练脚本规范，对局限性分析客观。
- 不足: 受限于缺少MACE-MH-1基础模型权重，未能复现论文核心的微调后高精度量级；缺失metrics.json文件。