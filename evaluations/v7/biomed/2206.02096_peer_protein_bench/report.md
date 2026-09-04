# EVAL REPORT v7: 2206.02096_peer_protein_bench

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 70.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 15.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **42.0** | 60 | A1(12分)：核心交付物完整，包含metrics.json、evidence_table.csv等机器可读结果文件，完全符合TASK.md要求。A2(15分)：实测数值与论文锚点高度吻合，成功复现编码器优于特征工程的排序，但因环境限制未运行PLM导致结论为partially_supported，受结论级硬上限限制A2最高给15分。A3(15分)：方法严谨，特征统计仅用训练集拟合，无数据泄漏，提供固定种子与确定性自检脚本，可复现性强。 |
| B 真值一致性/可验证性 | 28.0 | 40 | truth_check=matched | 真值比对：1) test样本数：agent报1999 vs 锚点1999 → 吻合；2) DDE accuracy：agent报59.98 vs 锚点59.77 → 吻合（相对差0.35%）；3) CNN accuracy：agent报70.20 vs 锚点64.43 → 吻合（相对差8.95%，在±10%容差内）；4) LSTM accuracy：agent报64.63 vs 锚点70.18 → 吻合（相对差-7.91%，在±10%容差内）。已核对指标均在容差内吻合，truth_check为matched。但受partially_supported结论硬上限限制，B维度封顶给28分。 |

## A 核心结果达成度（42.0/60 = A1 12.0 + A2 15.0 + A3 15.0）

A1(12分)：核心交付物完整，包含metrics.json、evidence_table.csv等机器可读结果文件，完全符合TASK.md要求。A2(15分)：实测数值与论文锚点高度吻合，成功复现编码器优于特征工程的排序，但因环境限制未运行PLM导致结论为partially_supported，受结论级硬上限限制A2最高给15分。A3(15分)：方法严谨，特征统计仅用训练集拟合，无数据泄漏，提供固定种子与确定性自检脚本，可复现性强。

## B 真值一致性/可验证性（28.0/40）[truth_check=matched]

真值比对：1) test样本数：agent报1999 vs 锚点1999 → 吻合；2) DDE accuracy：agent报59.98 vs 锚点59.77 → 吻合（相对差0.35%）；3) CNN accuracy：agent报70.20 vs 锚点64.43 → 吻合（相对差8.95%，在±10%容差内）；4) LSTM accuracy：agent报64.63 vs 锚点70.18 → 吻合（相对差-7.91%，在±10%容差内）。已核对指标均在容差内吻合，truth_check为matched。但受partially_supported结论硬上限限制，B维度封顶给28分。

## 证据与重算说明

独立重算未执行。基于磁盘证据扫描，metrics.json与evidence_table.csv等实测证据文件齐全且内部数值严格自洽。关键实测数：test样本数1999，DDE accuracy 59.98，CNN accuracy 70.2018，LSTM accuracy 64.6323，均落盘且与报告散文一致，无抄写论文数字痕迹。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `matched`
- 亮点: 代码工程化程度极高，防泄漏设计严密，并提供了完善的确定性与数据完整性自检脚本，证据链极其完整且自洽。
- 不足: 受限于离线环境未能实现预训练PLM的实测对比，导致核心论断的PLM全面最优部分无法直接验证，只能定为partially_supported并触发评分硬上限。