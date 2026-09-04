# EVAL REPORT v2: 2604.13897_molcryst_mlips

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 87.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 52.0 | 60 | A1(20分)：完整解析20个h5文件，结构协议说明充分，单位换算正确，得20分。A2(20分)：正确识别10个体系文件，明确映射论文9体系+acridine扩展及ehowih，规模统计详尽，得20分。A3(12分)：agent报告resora代理模型RMSE_E=11.53 meV(约1.11 kJ/mol/atom)，RMSE_F=115.79 meV/A(约11.17 kJ/mol/A)；与论文锚值(0.141/0.648)量级相差约10倍，但因缺乏基础模型权重仅做from-scratch代理训练，方向一致且讨论充分，落入“部分成立”区间(10-14)，给12分。 |
| B 证据真实性/实际复现 | 35.0 | 40 | 磁盘证据扫描显示metrics.json缺失，但evidence_table.csv等实测证据文件存在。evidence_table中能量/力统计与h5_structure_report及代码逻辑内部严格一致（如acridine_train构型数18544，批次数2318），无伪造或抄数痕迹，符合“有证据文件且数值与报告严格一致、可核对”条件，落入[30,40]区间，给35分。 |

## A 核心结果达成度（52.0/60）

A1(20分)：完整解析20个h5文件，结构协议说明充分，单位换算正确，得20分。A2(20分)：正确识别10个体系文件，明确映射论文9体系+acridine扩展及ehowih，规模统计详尽，得20分。A3(12分)：agent报告resora代理模型RMSE_E=11.53 meV(约1.11 kJ/mol/atom)，RMSE_F=115.79 meV/A(约11.17 kJ/mol/A)；与论文锚值(0.141/0.648)量级相差约10倍，但因缺乏基础模型权重仅做from-scratch代理训练，方向一致且讨论充分，落入“部分成立”区间(10-14)，给12分。

## B 证据真实性/实际复现（35.0/40）

磁盘证据扫描显示metrics.json缺失，但evidence_table.csv等实测证据文件存在。evidence_table中能量/力统计与h5_structure_report及代码逻辑内部严格一致（如acridine_train构型数18544，批次数2318），无伪造或抄数痕迹，符合“有证据文件且数值与报告严格一致、可核对”条件，落入[30,40]区间，给35分。

## 证据与重算说明

独立重算未执行。关键实测数值：acridine_train构型数18544，批次数2318，能量范围-2063.02至-629.76 eV；resora代理模型Epoch 1验证集RMSE_E_per_atom=11.53 meV，RMSE_F=115.79 meV/A。证据文件evidence_table.csv与报告数值严格一致。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 数据层解析极其详尽，20个h5文件的批次结构、原子数、能量/力范围统计完整且内部高度一致；代理模型训练脚本规范，对无法复现微调精度的局限性分析客观合理。
- 不足: 受限于缺少MACE-MH-1基础模型权重，未能真正复现论文核心的微调后高精度量级，仅能证明数据本身可用于训练MLIP；缺失metrics.json文件。