# EVAL REPORT v5: 2502.20784_arseg_next_scale_seg

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 70.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 15.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **42.0** | 60 | A1(12)：核心交付物完整，包含代码、数据协议解析、基线与AR-Seg风格模型的训练评估结果及机制消融，完全符合TASK.md要求。A2(15)：成功复现了AR-Seg风格模型在LIDC和BraTS上均优于同设置单尺度基线的相对效应，方向与论文一致；但受限于伪掩码、2D简化及子集规模，绝对数值与论文锚值差异较大，且简化机制的条件化通道消融显示贡献为0。结论为partially_supported，受硬上限约束给15分。A3(15)：方法严谨，LIDC采用患者级划分防泄漏，BraTS固定病例划分，伪掩码确定性生成，代码固定种子且逻辑sound，具备可复现性。 |
| B 证据真实性/实际复现 | 28.0 | 40 | 磁盘证据扫描确认metrics.json与evidence_table.csv均存在且内部自洽，包含丰富的训练history与ablation JSON，证据等级为2。未发现抄袭论文锚值行为，诚实报告了协议差异。受partially_supported结论硬上限约束，B最高给28分。 |

## A 核心结果达成度（42.0/60 = A1 12.0 + A2 15.0 + A3 15.0）

A1(12)：核心交付物完整，包含代码、数据协议解析、基线与AR-Seg风格模型的训练评估结果及机制消融，完全符合TASK.md要求。A2(15)：成功复现了AR-Seg风格模型在LIDC和BraTS上均优于同设置单尺度基线的相对效应，方向与论文一致；但受限于伪掩码、2D简化及子集规模，绝对数值与论文锚值差异较大，且简化机制的条件化通道消融显示贡献为0。结论为partially_supported，受硬上限约束给15分。A3(15)：方法严谨，LIDC采用患者级划分防泄漏，BraTS固定病例划分，伪掩码确定性生成，代码固定种子且逻辑sound，具备可复现性。

## B 证据真实性/实际复现（28.0/40）

磁盘证据扫描确认metrics.json与evidence_table.csv均存在且内部自洽，包含丰富的训练history与ablation JSON，证据等级为2。未发现抄袭论文锚值行为，诚实报告了协议差异。受partially_supported结论硬上限约束，B最高给28分。

## 证据与重算说明

独立重算未执行。关键实测数：LIDC基线Soft-Dice=0.9594，AR-Seg=0.9664；BraTS WT基线Hard-Dice=0.7814，AR-Seg=0.7898；LIDC测试集5583 patches，BraTS测试集132 slices。所有指标均由代码生成并落盘，证据链完整。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 对冻结数据的局限性进行了极其诚实且透明的说明，机制消融实验设计详实，有效支撑了相对提升的定性结论。
- 不足: 受限于算力和数据，未能复现完整的tokenized AR-Seg自回归机制，且BraTS WT Hard-Dice在报告与CSV中存在轻微量纲表示不一致。