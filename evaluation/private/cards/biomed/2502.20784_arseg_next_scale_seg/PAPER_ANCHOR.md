# 论文锚：2502.20784_arseg_next_scale_seg

## 锚清单（全部来自论文，禁止臆造）

| # | 指标 | 论文数值 | 出处 | 定义口径 | 容差 |
|---|---|---|---|---|---|
| 1 | LIDC-IDRI AR-Seg GED | 0.232（↓） | Table 1 | Generalized Energy Distance（16 采样） | 参照锚（相对提升） |
| 2 | LIDC-IDRI AR-Seg HM-IoU | 0.616（↑） | Table 1 | Matched Intersection over Union（16 采样） | 参照锚 |
| 3 | LIDC-IDRI AR-Seg Soft-Dice | 0.658（↑） | Table 1 | Soft-Dice（16 采样）；BerDiff 0.644、CAR 0.633 | 提交 ≥0.5 满分档 |
| 4 | BraTS 2021 AR-Seg Dice | 86.97 | Table 2（Results on BRATS 2021） | 多类脑肿瘤分割 Dice；对比 nnU-Net 84.57、BerDiff 85.42、HiDiff 85.80 | 提交 ≥75 满分档 |
| 5 | 数据集规模 | LIDC-IDRI 1,018 例；BraTS 2021 多模态 | §Dataset and preprocessing | 论文实验数据集 | 冻结子集按实际 |

## 备注
- 主论断：AR-Seg（下尺度掩码自回归 + 共识聚合）在 LIDC-IDRI 与 BraTS 2021 上均优于 SOTA。
- 论文出处：arXiv:2502.20784，Table 1/2、§Dataset and preprocessing；数值以论文 PDF 为准。冻结数据为 LIDC-IDRI patch 镜像 + BraTS 2021 mini 子集。