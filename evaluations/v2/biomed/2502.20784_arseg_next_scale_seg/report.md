# EVAL REPORT v2: 2502.20784_arseg_next_scale_seg

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 98.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1：LIDC基线Soft-Dice=0.9594（≥0.5），BraTS基线Hard-Dice=0.7814（即78.14%，≥75），均落入满分带，得20分。A2：LIDC AR-Seg Soft-Dice=0.9664（>基线0.9594），BraTS AR-Seg Hard-Dice=0.7898（>基线0.7814），满足AR-Seg≥同设置基线，落入满分带，得20分。A3：提供了nextscale_ablation和consensus_analysis等机制消融实验，详细分析了多尺度与共识聚合的作用，落入满分带，得20分。所有数值均有evidence_table.csv和metrics.json落盘支撑。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘扫描显示metrics.json与evidence_table.csv均存在，且包含丰富的训练history与ablation JSON文件。抽查LIDC基线Soft-Dice(0.9594)与BraTS WT Hard-Dice(0.7814)，在csv、json及report中严格一致（report中BraTS使用百分数78.14，csv中为0.7814，属合理量纲转换且已说明）。未发现抄袭论文锚值（0.658/86.97）行为，agent诚实报告了因冻结子集和伪掩码导致的绝对数值差异。证据真实且可核对，落入[30,40]高分档。 |

## A 核心结果达成度（60/60）

A1：LIDC基线Soft-Dice=0.9594（≥0.5），BraTS基线Hard-Dice=0.7814（即78.14%，≥75），均落入满分带，得20分。A2：LIDC AR-Seg Soft-Dice=0.9664（>基线0.9594），BraTS AR-Seg Hard-Dice=0.7898（>基线0.7814），满足AR-Seg≥同设置基线，落入满分带，得20分。A3：提供了nextscale_ablation和consensus_analysis等机制消融实验，详细分析了多尺度与共识聚合的作用，落入满分带，得20分。所有数值均有evidence_table.csv和metrics.json落盘支撑。

## B 证据真实性/实际复现（38.0/40）

磁盘扫描显示metrics.json与evidence_table.csv均存在，且包含丰富的训练history与ablation JSON文件。抽查LIDC基线Soft-Dice(0.9594)与BraTS WT Hard-Dice(0.7814)，在csv、json及report中严格一致（report中BraTS使用百分数78.14，csv中为0.7814，属合理量纲转换且已说明）。未发现抄袭论文锚值（0.658/86.97）行为，agent诚实报告了因冻结子集和伪掩码导致的绝对数值差异。证据真实且可核对，落入[30,40]高分档。

## 证据与重算说明

独立重算未执行。关键实测数：LIDC基线Soft-Dice=0.9594，AR-Seg=0.9664；BraTS WT基线Hard-Dice=0.7814，AR-Seg=0.7898；LIDC测试集5583 patches，BraTS测试集132 slices。所有指标均由代码生成并落盘于results/目录，证据链完整。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 对冻结数据的局限性（如LIDC无逐像素标注需构建伪掩码、BraTS mini仅单模态）进行了极其诚实且透明的说明；机制消融实验设计详实，有效支撑了相对提升的结论。
- 不足: BraTS WT Hard-Dice在report.md表格中显示为百分数（78.14），而在evidence_table.csv中为小数（0.7814），存在轻微的量纲表示不一致，虽不影响真实性但增加了核对成本。