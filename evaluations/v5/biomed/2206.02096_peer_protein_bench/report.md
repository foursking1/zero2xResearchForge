# EVAL REPORT v5: 2206.02096_peer_protein_bench

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 70.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 15.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **42.0** | 60 | A1(12分)：核心交付物（claim.md、代码、evidence_table.csv、metrics.json、report.md）完整产出，完全符合TASK.md要求。A2(15分)：实测DDE 59.98、CNN 70.20、LSTM 64.63，成功复现了“从零训练编码器显著优于特征工程”的核心科学效应与排序，效应匹配度极高；但受限于“partially_supported”结论级硬上限（A2≤15），故给15分。A3(15分)：方法严谨，严格区分训练/验证/测试集，特征统计量仅由训练集拟合，无数据泄漏；提供固定种子与确定性自检脚本，结果可由提交物复算。 |
| B 证据真实性/实际复现 | 28.0 | 40 | 磁盘证据扫描显示证据等级为2（齐全自洽），包含完整的metrics.json、evidence_table.csv及校验脚本，内部数值高度自洽，无抄写论文数字痕迹。但受限于“partially_supported”结论级硬上限（B≤28），故给28分。 |

## A 核心结果达成度（42.0/60 = A1 12.0 + A2 15.0 + A3 15.0）

A1(12分)：核心交付物（claim.md、代码、evidence_table.csv、metrics.json、report.md）完整产出，完全符合TASK.md要求。A2(15分)：实测DDE 59.98、CNN 70.20、LSTM 64.63，成功复现了“从零训练编码器显著优于特征工程”的核心科学效应与排序，效应匹配度极高；但受限于“partially_supported”结论级硬上限（A2≤15），故给15分。A3(15分)：方法严谨，严格区分训练/验证/测试集，特征统计量仅由训练集拟合，无数据泄漏；提供固定种子与确定性自检脚本，结果可由提交物复算。

## B 证据真实性/实际复现（28.0/40）

磁盘证据扫描显示证据等级为2（齐全自洽），包含完整的metrics.json、evidence_table.csv及校验脚本，内部数值高度自洽，无抄写论文数字痕迹。但受限于“partially_supported”结论级硬上限（B≤28），故给28分。

## 证据与重算说明

独立重算未执行。基于磁盘证据扫描与提交物核查，关键实测数：test样本数1999，DDE accuracy 59.98，CNN accuracy 70.20，LSTM accuracy 64.63，均在evidence_table.csv和metrics.json中落盘且相互严格一致，verify脚本逻辑完备。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 代码工程化程度极高，防泄漏设计严密，并提供了完善的确定性与数据完整性自检脚本，证据链极其完整且自洽。
- 不足: 受限于离线环境未能实现预训练PLM的实测对比，导致核心论断的“PLM全面最优”部分只能依赖论文数据进行间接讨论，结论定为partially_supported从而触发硬上限限制。