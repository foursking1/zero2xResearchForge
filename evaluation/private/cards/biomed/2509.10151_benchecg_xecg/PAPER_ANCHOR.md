# 论文锚：2509.10151_benchecg_xecg

## 锚清单（全部来自论文，禁止臆造）

| # | 指标 | 论文数值 | 出处 | 定义口径 | 容差 |
|---|---|---|---|---|---|
| 1 | xECG PTB-XL AUROC | 0.853±0.022 | Table 2（PTB-XL 任务） | xECG 在 PTB-XL 分类任务（macro AUROC）5 次训练均值±std | 提交 AUROC ≥0.80 满分档 |
| 2 | ST-MEM PTB-XL AUROC | 0.702±0.020 | Table 2 | 次优公开基础模型 ST-MEM 同口径 | 参照 |
| 3 | xECG PTB-XL F1 | 0.674±0.013 | Table 2 | 同任务 F1 | 提交 F1 ≥0.5 满分档 |
| 4 | ST-MEM PTB-XL F1 | 0.436±0.036 | Table 2 | 同口径 | 参照 |
| 5 | 显著性 | p=0.000004（AUROC）/ p=0.000032（F1） | Table 2 注记 | xECG vs ST-MEM 配对检验 | 方向性锚 |
| 6 | BenchECG 规模 | 8 数据集、10 任务；xECG mean rank 1.2 | Abstract/§1 | 基准覆盖与综合排名 | 参照锚 |

## 备注
- 主论断：xECG 在 BenchECG 上全面最优且显著优于 ST-MEM；是唯一在所有任务上都强的公开模型。
- 论文出处：arXiv:2509.10151，Table 2 与 Abstract；数值以论文 PDF 为准。冻结数据为 PTB-XL-small 镜像（train/validation）。