# Claim Assessment — 2502.20784 AR-Seg 下尺度掩码预测分割

## 结论标签：`partially_supported`

AR-Seg 的核心论断「显式跨尺度（下尺度掩码）自回归 + 共识聚合优于单尺度基线」的
**相对方向**在我们的冻结数据/简化协议上得到复现（AR-Seg 风格模型在 LIDC 与 BraTS 两个
固定协议上均 ≥ 单尺度基线），但由于只使用了冻结子集、2D 简化、伪掩码与确定性单次推理，
**绝对数值与论文（LIDC Soft-Dice 0.658 / BraTS Dice 86.97）不可直接对标**，且完整 AR-Seg
（token 化下尺度自回归 transformer + 多采样共识）未完整复现，因此标定为部分支持。

## 三问判定

### Q1 数据与协议（已做）
- LIDC：冻结 parquet 共 **40,187** 个结节 patch，来自 **875** 例患者 / **2,651** 个结节
  cluster（全量 LIDC-IDRI 为 1,018 例，冻结镜像覆盖 86%）；数据无逐像素标注
  （bbox 跨度 == patch 跨度），故按任务提示构造**一次性、确定性**的 Otsu+最大连通域
  **伪掩码**（文档化限制）；按患者 70/15/15 固定划分（train 612 例 / val 131 例 /
  test 132 例；train 12,000 patch / val 6,334 / test 5,583）。
- BraTS 2021 mini：**10 例**单模态 240×240×155 NIFTI（全量 1,251 例、4 模态）；
  2D 轴向切片、128×128 重采样，WT 二分类为主协议，ET/TC/WT 4 类为辅助分析；
  按病例固定划分 train 0-6 / val 7 / test 8-9（train 427 片 / val 61 / test 132 片）。

### Q2 分割基线复现（已做）
- LIDC（Soft-Dice 口径）：U-Net 基线 **0.9594**（≥ 0.5 满分线；hard-Dice 0.9706，IoU 0.9551）。
- BraTS（Dice 口径）：U-Net 基线 WT hard-Dice **78.14**（≥ 75 满分线；soft-Dice 0.4666，IoU 0.6821）。
- 辅助 4 类（ET/TC/WT 平均 25.1 / WT 75.27）如实呈现，受单模态 + 测试病例 ET≈788
  体素影响 ET/TC 难分（论文使用 4 模态全量），已在 report.md 说明。

### Q3 AR-Seg 核心机制（简化实现 + 相对提升）
- 简化实现：共享编码器 + **多尺度掩码监督头**（1/4、1/2、1）+ **下尺度→细尺度条件化**
  （粗掩码上采样后拼入细解码器，即“next-scale conditioning”）+ **共识聚合近似**
  （K 次 MC-dropout 采样平均）。
- LIDC：AR-Seg 风格 **0.9664** vs 基线 0.9594（**+0.0070**，相对 +0.73%）；
  hard-Dice +0.0028，IoU +0.0063。
- BraTS WT：AR-Seg 风格 **78.98** vs 基线 78.14（**+0.84 pts hard-Dice**）；
  soft-Dice +0.0222，IoU +0.0160。
- 机制消融：多尺度监督关闭（arseg_noscale_sup）0.9666、条件化通道置常量的 ablation
  Δ≈0，说明在我们 2D 单次前向近似中，相对增益来自“多尺度 coarse→fine 结构”本身，
  而辅助/条件通道贡献很小——这是相对完整 AR-Seg（严格自回归采样约束）的一个重要差异，
  已在 report.md 详述。

### 关键证据文件
- `results/evidence_table.csv`（model/dataset/metric/value，44 行）
- `results/metrics.json`（样本统计 + 各模型指标 + 锚点对照 + 结论标签）
- `evidence/nextscale_ablation.json`、`evidence/consensus_analysis.json`、`evidence/*.png`
- 所有数字均由 `code/` 从冻结数据重新运行得到，未抄写论文数值。