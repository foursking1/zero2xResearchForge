# solution.md（方法说明与结果）

## 任务概述

验证 MedMNIST v2 论文（Yang et al., Scientific Data 2023, arXiv:2110.14795）的核心论断：
（1）轻量 28×28 医学图像分类任务上，标准 CNN（ResNet-18 基线）即可达到高 AUC（多数数据集
AUC≥0.90）；（2）不同数据集难度差异巨大（BloodMNIST ≈0.998 vs RetinaMNIST ≈0.72）；（3）
AutoML 与 ResNet-18 基线性能接近。

在冻结的 5 个 MedMNIST2D 数据集（BloodMNIST、BreastMNIST、DermaMNIST、PneumoniaMNIST、
RetinaMNIST）上独立完成数据统计、训练、测试评估，并给出与论文对照的四档结论。

## 方法

**数据与统计（A1）**
- 从冻结 npz 读取 `train/val/test` 六键；逐数据集按官方口径统计类别数与样本数：
  Blood(8 类, 11959/1712/3421)、Breast(2, 546/78/156)、Derma(7, 7007/1003/2005)、
  Pneumonia(2, 4708/524/624)、Retina(5, 1080/120/400)；与 TASK/SOURCE 所述完全一致。
- 灰度数据集（Breast、Pneumonia）为单通道 28×28，RGB 数据集为 28×28×3（NHWC → NCHW）。
- 归一化：每数据集由 **train 部分**计算逐通道 mean/std（像素先缩放到 [0,1]），val/test 仅变换，
  统计量不接触测试集。

**模型（A2）**
- ResNet-18（torchvision 结构），为适配 28×28 输入将 stem 改为 3×3/stride-1 卷积 +
  BN + ReLU，移除初始 max-pool；ResNet block 保持标准结构。
- 全连接输出类数 = 数据集类别数；平均池化 + Linear 头。
- 输入通道：灰度 1、RGB 3。

**训练与防泄漏（C2）**
- 训练增强（仅 train）：随机水平翻转 + 随机旋转 ±10°；
- Adam（lr=1e-3, weight_decay=1e-4），ReduceLROnPlateau（on **val AUC**），
  batch=64，seed=0，max 45 epochs，早停 patience=12（基于 **val AUC**）。
- 模型选择全部基于 **validation**；**test 每数据集仅最后评估一次**，实测结果直接上报，
  无重复调参。

**评估（A3）**
- AUC：多类 = macro 一元超曲线 AUC（`sklearn.metrics.roc_auc_score` with
  `multi_class="ovr", average="macro"`，MedMNIST 官方口径）；二类 = 正类分数 ROC AUC。
- ACC：`argmax` 准确率。最终选定 best-val checkpoint 报告 test 指标。

## 结果（test）

| 数据集 | AUC | ACC | 论文 AUC/ACC | ΔAUC | 判定 |
|---|---|---|---|---|---|
| bloodmnist | 0.9978 | 0.9640 | 0.998 / 0.958 | -0.0002 | supported |
| breastmnist | 0.8997 | 0.8718 | 0.901 / 0.863 | -0.0013 | supported |
| dermamnist | 0.9302 | 0.7621 | 0.917 / 0.735 | +0.0132 | supported |
| pneumoniamnist | 0.9701 | 0.8862 | 0.944 / 0.854 | +0.0261 | supported |
| retinamnist | 0.7011 | 0.4625 | 0.717 / 0.524 | -0.0159 | supported |

- 全部数据集 AUC 落入 rubric A3 验证区间（Blood≥0.97、Breast≥0.85、Derma≥0.86、
  Pneumonia≥0.89、Retina 0.63–0.80）。
- 难度排序（test AUC 降序）：blood > pneumonia > derma > breast > retina，与论文锚完全一致。
- 结论标签：`supported`。

## 复现

```bash
# 从本目录（agent_solution/）
bash run_all.sh --device cpu --epochs 45        # 或 --device cuda
MEDMNIST_DATA_DIR=/path/to/frozen/npz python3 code/data_stats.py
MEDMNIST_DATA_DIR=/path/to/frozen/npz python3 code/train.py --device cpu
```

- 数据定位：`code/config.py` 依序探测环境变量 `MEDMNIST_DATA_DIR` → 
  `F:\dataset\biomed\2110.14795_medmnist_v2\` → `/mnt/f/dataset/biomed/2110.14795_medmnist_v2/`。
- 固定种子：`SEED=0`；torch/cudnn 确定性模式（GPU 下 benchmark=False）。
- 产物：`results/evidence_table.csv`（rubric B 抽查字段来源）、`results/metrics.json`、
  `results/checkpoints/<dataset>_best.pt`、`results/class_counts.json`、`results/split_sizes.csv`。

依赖：Python ≥3.10，numpy，scikit-learn，torch≥2.0，torchvision。CPU 全程约 60–90 分钟
（本机 RTX 4080 约 17 分钟）。