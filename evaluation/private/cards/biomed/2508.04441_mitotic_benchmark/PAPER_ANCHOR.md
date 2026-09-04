# 论文锚：2508.04441_mitotic_benchmark

## 锚清单（全部来自论文，禁止臆造）

| # | 指标 | 论文数值 | 出处 | 定义口径 | 容差 |
|---|---|---|---|---|---|
| 1 | MIDOG 2022 全量 Virchow2-LoRA Weighted F1 | 0.81±0.014 | Table 4（100% dataset size of MIDOG） | LoRA 适配 Virchow2 在 MIDOG 2022 全量训练数据上的有丝分裂分类加权 F1 | 提交 F1 落 0.6-0.9 满分档（子集口径放宽） |
| 2 | 同上 AUROC | 0.89±0.011 | Table 4 | 同上口径 AUROC | 参照 |
| 3 | 同上 Balanced Accuracy | 0.80±0.022 | Table 4 | 同上口径 Balanced ACC | 参照 |
| 4 | 10% 数据 Virchow2（LinProb）Weighted F1 | 0.72±0.00 | Table 12（10% dataset size of MIDOG） | 10% 训练数据下线性探测 F1 | 数据效率趋势锚：与全量差 ≤0.15 |
| 5 | 端到端 ResNet50（100%）Weighted F1 | 0.78±0.010 | Table 4 | 端到端训练的 CNN 基线 | 参照 |
| 6 | 数据集规模 | 9,501 MF / 11,051 难例（405 例） | §3.1.2 / 数据集描述 | MIDOG 2022 训练集标注 | 冻结子集按实际统计 |

## 备注
- 主论断：LoRA 适配基础模型优于线性探测，且以 10% 数据接近全量性能；端到端 CNN 仍具竞争力。
- 论文出处：arXiv:2508.04441（MELBA 2026，DOI 10.59275/j.melba.2026-a3eb），Table 4 / Table 12 / §3.1.2；数值以论文 PDF 为准。冻结数据为 MIDOG 2022 官方训练集 4 张图子集。