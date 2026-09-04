# EVAL REPORT v3: 2502.20784_arseg_next_scale_seg

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | 逐项核对Rubric band：A1基线LIDC Soft-Dice=0.9594(≥0.5)且BraTS WT Hard-Dice=78.14(≥75)，命中满分带得20分；A2 AR-Seg LIDC 0.9664>基线0.9594，BraTS 78.98>基线78.14，命中满分带得20分；A3提供了nextscale_ablation等详细机制分析，命中满分带得20分。虽然绝对数值与论文锚值偏差较大，但符合Task及CALIBRATION中降低精确数值依赖、侧重相对提升与机制验证的设计，严格命中Rubric定义的band，A=60。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘扫描确认metrics.json与evidence_table.csv均存在，证据等级为2（齐全自洽）。包含丰富的训练history、ablation JSON及完整可运行代码。抽查关键数值在csv、json及报告中严格一致，未发现抄袭论文锚值行为，诚实报告了协议差异。符合“有metrics.json且内部自洽、并有校验证据”的最高档，B=40。 |

## A 核心结果达成度（60/60）

逐项核对Rubric band：A1基线LIDC Soft-Dice=0.9594(≥0.5)且BraTS WT Hard-Dice=78.14(≥75)，命中满分带得20分；A2 AR-Seg LIDC 0.9664>基线0.9594，BraTS 78.98>基线78.14，命中满分带得20分；A3提供了nextscale_ablation等详细机制分析，命中满分带得20分。虽然绝对数值与论文锚值偏差较大，但符合Task及CALIBRATION中降低精确数值依赖、侧重相对提升与机制验证的设计，严格命中Rubric定义的band，A=60。

## B 证据真实性/实际复现（40/40）

磁盘扫描确认metrics.json与evidence_table.csv均存在，证据等级为2（齐全自洽）。包含丰富的训练history、ablation JSON及完整可运行代码。抽查关键数值在csv、json及报告中严格一致，未发现抄袭论文锚值行为，诚实报告了协议差异。符合“有metrics.json且内部自洽、并有校验证据”的最高档，B=40。

## 证据与重算说明

独立重算未执行。关键实测数：LIDC基线Soft-Dice=0.9594，AR-Seg=0.9664；BraTS WT基线Hard-Dice=78.14，AR-Seg=78.98；LIDC测试集5583 patches，BraTS测试集132 slices。所有指标均由代码生成并落盘于results/目录，证据链完整。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 对冻结数据的局限性（如伪掩码、单模态子集）进行了极其诚实且透明的说明，机制消融实验设计详实，有效支撑了相对提升的结论。
- 不足: BraTS WT Hard-Dice在report表格中显示为百分数（78.14）而在csv中为小数（0.7814），存在轻微的量纲表示不一致，略微增加了核对成本。