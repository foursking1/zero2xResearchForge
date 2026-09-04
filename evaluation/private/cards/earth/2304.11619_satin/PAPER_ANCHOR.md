# PAPER_ANCHOR.md（私有）— 2304.11619 SATIN

> 来源：Roberts et al., "SATIN: A Multi-Task Metadataset for Classifying Satellite Imagery using Vision-Language Models", ICCV 2023 TNGCV Workshop（arXiv:2304.11619）。

## 锚 1（主锚，L1 核心结果）
| 项 | 值 |
|---|---|
| 指标 | SATIN 整体零样本分类准确率（27 数据集元基准的 overall score） |
| 论文数值 | **52.0%**（OpenCLIP ViT-G/14，LAION-2B 预训练） |
| 出处 | 摘要「the strongest method we evaluate achieves a classification accuracy of 52.0%」；Table 3「OpenCLIP ViT-G/14 2B ... 0.52（SATIN 列）」 |
| 定义口径 | 零样本 top-1 分类准确率；overall = 27 个数据集平均（§4.1） |
| 容差 | 相对差 d<=10% 满分；d<=30% 半满（见 SCORE_RUBRIC.md） |

## 锚 2（SAT-4 单列，任务数据对应的直接可比锚）
| 项 | 值 |
|---|---|
| 指标 | SAT-4 零样本分类准确率 |
| 论文数值 | **0.54**（OpenCLIP 列） |
| 出处 | 附录 Table 6「Per-Dataset Results ... OpenCLIP ... SAT-4 0.54」 |
| 定义口径 | OpenCLIP ViT-G/14 2B 在 SAT-4 上的零样本 top-1 准确率 |
| 容差 | 相对差 d<=10% 满分；d<=30% 半满 |

## 锚 3（Table 3 其它对比，用于方法对比报告）
| 方法 | SATIN overall | 出处 |
|---|---|---|
| CLIP ViT-L/14@336px | 0.51 | Table 3 |
| BLIP2 ViT-G/14 | 0.50 | Table 3 |
| BLIP ViT-B/16 | 0.45 | Table 3 |
| DeCLIP ViT-B/32 | 0.41 | Table 3 |
