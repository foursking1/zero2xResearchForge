# EVAL REPORT v7: 2502.20784_arseg_next_scale_seg

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 64.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 15.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **42.0** | 60 | A1(12)：核心交付物完整，包含metrics.json、evidence_table.csv等机器可读结果文件。A2(15)：成功复现了AR-Seg风格模型优于同设置基线的相对效应，方向与论文一致，但绝对数值与论文真值差异较大，属定性匹配；受partially_supported结论硬上限约束，给15分。A3(15)：方法严谨，防泄漏措施到位，诚实说明伪掩码和子集限制，代码逻辑sound且可复现。 |
| B 真值一致性/可验证性 | 22.0 | 40 | truth_check=diverged | agent数 LIDC Soft-Dice 0.9664 vs 锚点 0.658 → 偏离（因使用Otsu伪掩码导致指标虚高）；agent数 BraTS WT Hard-Dice 78.98 vs 锚点 86.97 → 偏离（因仅使用10例单模态子集及2D简化导致指标偏低）。关键指标均超出容差带，判定为diverged。但agent在报告中诚实说明了协议差异导致的不可对标性，未抄袭论文数字，故在diverged档位内给予中等偏上分数。 |

## A 核心结果达成度（42.0/60 = A1 12.0 + A2 15.0 + A3 15.0）

A1(12)：核心交付物完整，包含metrics.json、evidence_table.csv等机器可读结果文件。A2(15)：成功复现了AR-Seg风格模型优于同设置基线的相对效应，方向与论文一致，但绝对数值与论文真值差异较大，属定性匹配；受partially_supported结论硬上限约束，给15分。A3(15)：方法严谨，防泄漏措施到位，诚实说明伪掩码和子集限制，代码逻辑sound且可复现。

## B 真值一致性/可验证性（22.0/40）[truth_check=diverged]

agent数 LIDC Soft-Dice 0.9664 vs 锚点 0.658 → 偏离（因使用Otsu伪掩码导致指标虚高）；agent数 BraTS WT Hard-Dice 78.98 vs 锚点 86.97 → 偏离（因仅使用10例单模态子集及2D简化导致指标偏低）。关键指标均超出容差带，判定为diverged。但agent在报告中诚实说明了协议差异导致的不可对标性，未抄袭论文数字，故在diverged档位内给予中等偏上分数。

## 证据与重算说明

独立重算未执行。关键实测数：LIDC基线Soft-Dice=0.9594，AR-Seg=0.9664；BraTS WT基线Hard-Dice=78.14，AR-Seg=78.98；LIDC测试集5583 patches，BraTS测试集132 slices。所有指标均由代码生成并落盘，证据链完整。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 对冻结数据的局限性进行了极其诚实且透明的说明，机制消融实验设计详实，有效支撑了相对提升的定性结论。
- 不足: 受限于算力和数据协议简化，绝对数值与论文真值偏差较大，无法在定量层面验证论文的核心性能声明。