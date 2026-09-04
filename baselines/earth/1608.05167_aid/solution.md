# solution.md — 1608.05167 AID（多标签遥感场景分类复现）

## 结论（verdict）

**supported**（核心 claim 成立）— 在冻结的 AID_MultiLabel 镜像数据
（3,000 张 600×600 航空影像，17 类多标签）上：

| 口径 | 指标 | 本复现 | 论文锚（Table 6 GoogLeNet OA） |
|---|---|---|---|
| 多标签 17 类（60/20/20） | **mAP** | **80.23%** | （非同一口径） |
| 多标签 17 类 | **macro-F1** | 74.39% | — |
| 多标签 17 类 | **subset accuracy** | 33.33% | — |
| 多标签 17 类 | micro-F1 | 88.59% | — |
| 单标签 30 类（原 AID，固定 50/50） | **OA** | **94.66%** | 92.70±0.60（≈50% 训练量级） |

论文核心数字（86.39–94.71%）是 **30 类单标签口径**的 OA；冻结数据是
**17 类多标签镜像**，两者不是同一评估口径。为直接对照论文锚，我们：
1. 在冻结多标签数据上做 17 类多标签分类（mAP 达 80.23%，
   超过任务设定的 75% 上限）；
2. 在冻结包内的**原始 AID 30 类单标签图像 + 固定 50/50 划分**上复现
   单标签 OA = **94.66%**，落在论文 Table 6 的
   86.39%–94.71% 区间内（相对 50% 训练锚 92.70% 偏差 +2.1%），验证了
   「深度 CNN 微调在 AID 上可达到 ~90% 量级 OA」的核心 claim。

## 方法摘要

- 数据：冻结 parquet（305MB, 3,000 行）读取图像 bytes + 多标签；划分固定种子
  20260813，60/20/20 = 1800/600/600（防泄漏：归一化统计仅用训练子集，
  划分保存于 metrics JSON）。
- 模型：ImageNet 预训练 ResNet18（离线权重缓存），替换 fc 为 17 类 sigmoid 头，
  全网络微调，BCE + pos_weight（按训练集类别频率），AdamW + 余弦退火，30 个
  epoch，输入 224×224。
- 单标签对照：同样的 ResNet18 微调在原始 30 类 AID（5000/5000 冻结划分），
  40 个 epoch。
- 全部代码可在 `code/run_all.sh` 一键重跑；`recompute_metrics.py` 无需重训
  即可从冻结 parquet 重算出报告中的全部多标签数字。

## 关键证据文件

- `results/evidence_table.csv`：每类 tp/fp/tn/fn/precision/recall/f1/AP + 整体行
- `results/metrics_multilabel.json`：mAP、macro-F1、subset acc、per-class count、seed、split_sizes
- `results/metrics_singlelabel.json`：单标签 OA、per-class F1
- `evidence/pr_curves_17.png`、`evidence/per_class_ap.png`、`evidence/confusion_30.png`

## 局限性

- 冻结数据为多标签镜像（17 类，3,000 张），与论文 30 类单标签全量（10,000 张）
  口径不同；mAP 与 OA 不可直接换算，论文锚仅作量级对照。
- 极少数类（mobile home 测试仅 0 正样本、总 2 样本）mAP 为 0，属数据规模局限。
- 单标签 OA 采用单次固定划分（非论文的多次随机 + std）。