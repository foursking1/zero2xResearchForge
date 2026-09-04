# Claim Assessment — arXiv:2307.11958 (L1 critical claim)

## Q1. 数据与协议
- 冻结子集：MSD 全量（Spleen 41 例 / Liver 131 例）中各冻结 10 例（512² 轴向 CT，
  NIfTI），Spleen 标签类=1，Liver 标签类=1+2（合并为前景二值）。
- **冻结缺陷**：9/10 Liver *image* 流 gzip 被截断（SHA-256 与 `data/README.md`
  一致），label 流全部完好；我们实现了只读重建 loader（`common.py`），把每个
  卷可恢复的真实前缀解码出来（无任何合成）。`results/data_check.json` 记录逐例恢复。
- 解剖后果：`liver_10…17` 的 label 前景起始 z≈270–450，落在可恢复前缀
  （z≈68–197）之外 → 仅 `liver_0`（75 片，前景 z45–73）与 `liver_1`（99 可恢复
  片，29 前景片）可用于 Liver 源模型池预训练（论文为 5 个全量源任务，冻结后实际
  ≈2 个可用源病例）。
- 协议：源池 = Liver 预训练 U-Net（5 个成员：容量/种子/预算不同 + 1 个随机
  初始化），目标 = Spleen 微调，固定划分与种子；TE 评估只用目标 *train* 扫描，
  CC-FV 不使用任何目标标注（pseudo-label 来自源模型自身输出）。

## Q2. TE 排序 vs 真实微调 Dice 的相关性

主读数为 probe（冻编码器、只训 decoder/head）微调 Dice：

| TE 方法 | Pearson | 加权 Kendall τ | top-1 命中 |
|---|---|---|---|
| **CC-FV (ours, source-free)** | **0.3827** | **0.4000** | ✗ |
| LogME | 0.2728 | 0.8000 | ✓ |
| LEEP | 0.2042 | 0.4000 | ✗ |
| GBC | 0.1707 | 0.0000 | ✗ |

对照（论文 Table 1 五任务均值）：CC-FV 0.7003 / 0.4986；GBC 0.3317 / 0.4111；
LogME 0.2082 / 0.0218。

敏感性（全体微调、其余相同）：CC-FV 0.2174/0.2000，LogME 0.5281/0.6000，
LEEP 0.3992/0.2000，GBC −0.8732/−0.6000。

## Q3. “按 TE 选出最优源模型”是否等于微调最优
否（top-1 **未命中**）：CC-FV 选出 `l08_s1`，实际最优为 `l16_short`
（两种读法下均为 `l16_short`）。CC-FV 正地把随机初始化 `scratch` 排在最后。

## 结论标签
**`partially_supported`**

- 支持面：在 probe 读法下 CC-FV 的加权 τ=0.40（≥0.3 满分档）、Pearson=0.38，
  且其 Pearson 在本子集优于全部三个基线；方向判断成立。
- 不支持面：未复现论文量级（0.70/0.50）；full-finetune 读法下回落到
  0.22/0.20；top-1 选择不中；主因是冻结数据使源池近乎退化（仅 2 个可用
  Liver 源病例 + 随机成员）与 2D/128px 简化。

## 关键数字
- 全部数字由 `code/` 计算得出（固定种子、CPU）；`results/metrics.json` +
  `results/evidence_table.csv` 可重算。
- CC-FV 成员分数（decoder 特征）：`l08_s1`0.573, `l16_short`0.566,
  `l16_s1`0.524, `l16_s2`0.505, `scratch`0.420（最后一名）。
- probe Dice（test）：`l16_short`0.8586 > `l16_s1`0.8274 > `l08_s1`0.7769 >
  `scratch`0.7514 > `l16_s2`0.6166。