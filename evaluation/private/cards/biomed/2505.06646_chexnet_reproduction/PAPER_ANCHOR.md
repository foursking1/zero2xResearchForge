# 论文锚：2505.06646_chexnet_reproduction

## 锚清单（全部来自论文，禁止臆造；判分私有）

| # | 指标 | 论文数值 | 出处 | 定义口径 | 容差 |
|---|---|---|---|---|---|
| 1 | CheXNet 复现模型平均测试 AUC | 0.79 | §Results（"The CheXNet replica model had a test average AUC of 0.79..."） | DenseNet-121 预训练 + BCE，patient-wise 划分，NIH ChestX-ray14 14 类平均测试 AUC | 相对差 ≤10% 满分；≤25% 半满 |
| 2 | DACNet 平均测试 AUC | 0.85 | §Results / Abstract（"reaching an average AUC of 0.85"） | DACNet（Focal Loss + AdamW + ColorJitter + 逐类阈值）14 类平均测试 AUC | 相对差 ≤10% 满分；≤25% 半满 |
| 3 | CheXNet 复现模型平均测试 F1 | 0.08 | §Results（"test average F1 score of just 0.08"） | 同上模型 14 类平均 F1 | 绝对差 ±0.15 内满分 |
| 4 | DACNet 平均测试 F1 | 0.39 | §Results / Abstract（"an average F1 score of 0.39"） | DACNet 14 类平均 F1（逐类阈值优化） | 绝对差 ±0.15 内满分 |
| 5 | ViT 对照平均测试 AUC | 0.794；F1 0.111 | §Results（ViT 段） | ImageNet 预训练 ViT 微调，14 类平均 | 参照锚（不要求复现） |

## 备注
- 主论断：DenseNet-121 复现可达到高 AUC（0.79）但 F1 极低（0.08，类别不平衡+标注噪声）；加入现代训练技巧（Focal Loss 等）后 AUC 0.85 / F1 0.39。
- 论文出处：arXiv:2505.06646，§Results / Abstract；数值以论文 PDF 为准。冻结数据为 NIH ChestX-ray14 公开小镜像子集，锚为全量数据口径 → 判分时对冻结子集规模导致的偏移给予容差。