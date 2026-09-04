# report.md（完整报告）

## 1. 背景与目标

MedMNIST v2（Yang et al., Scientific Data 2023）构建了 12 个 2D + 6 个 3D 的轻量（28×28）
医学图像分类基准，并报告 ResNet-18 等标准 CNN 基线的 AUC/ACC。其核心论断是：
标准 CNN 在轻量医学图像分类上即可达到很高性能（多数数据集 AUC≥0.90），且不同数据集难度差异
巨大（BloodMNIST AUC≈0.998 vs RetinaMNIST≈0.717）；AutoML 与 ResNet 基线性能接近。

本任务在冻结的 5 个 MedMNIST2D 数据集上独立复现 ResNet-18 基线的数据规模与分类性能，并与论文
Table 3 对照，验证该论断。

## 2. 数据与任务统计（A1，A2 数据部分）

数据为官方冻结 npz（SHA-256 已核验，见 `data/source_manifest.json`）。各数据集类别数、通道数、
各划分样本数与官方 / TASK 说明一致：

| 数据集 | 类别 | 通道 | train | val | test | train 类别分布 |
|---|---|---|---|---|---|---|
| bloodmnist | 8 | 3 | 11959 | 1712 | 3421 | 852/2181/1085/2026/849/993/2330/1643 |
| breastmnist | 2 | 1 | 546 | 78 | 156 | 147/399 |
| dermamnist | 7 | 3 | 7007 | 1003 | 2005 | 228/359/769/80/779/4693/99 |
| pneumoniamnist | 2 | 1 | 4708 | 524 | 624 | 1214/3494 |
| retinamnist | 5 | 3 | 1080 | 120 | 400 | 486/128/206/194/66 |

完整逐分片计数在 `results/class_counts.json` 与 `results/split_sizes.csv`，由
`code/data_stats.py` 从 npz 重算生成。

## 3. 方法

### 3.1 预处理
- 图像 uint8 → float32，除以 255 到 [0,1]；NHWC → NCHW。
- 逐通道标准化，mean/std 仅由 train 统计（留出测试集）。

### 3.2 模型
- ResNet-18（torchvision 定义），28×28 适配 stem（7×7→3×3/stride1，去掉 max-pool），
  保持原 block/池化/全连接设计；每数据集独立训练（互不共享参数）。

### 3.3 训练
- 训练增强：随机翻转 + 旋转 ±10°（只作用于 train batch）。
- Adam lr=1e-3 / wd=1e-4，ReduceLROnPlateau（val AUC, patience 6, factor 0.2），
  batch 64，seed=0，max 45 epochs，early stop patience=12（val AUC）。
- 所有 model selection 仅使用 val；test 仅在 best-val checkpoint 上评估一次。

### 3.4 评估口径
- 多类 AUC = macro one-vs-rest AUC（`roc_auc_score(..., multi_class="ovr",
  average="macro")`，MedMNIST 官方口径）；二类 = 正类 ROC AUC（等价的病/异常类）。
- ACC = argmax。
- 对照组不参与任何计算；测试集不参与早停。

## 4. 结果（A3）

| 数据集 | val AUC | **test AUC** | **test ACC** | 论文 AUC/ACC | ΔAUC | 区间判定 |
|---|---|---|---|---|---|---|
| bloodmnist | 0.9990 | **0.9978** | **0.9640** | 0.998/0.958 | −0.0002 | ≥0.97 ✓ |
| breastmnist | 0.9799 | **0.8997** | **0.8718** | 0.901/0.863 | −0.0013 | ≥0.85 ✓ |
| dermamnist | 0.9287 | **0.9302** | **0.7621** | 0.917/0.735 | +0.0132 | ≥0.86 ✓ |
| pneumoniamnist | 0.9976 | **0.9701** | **0.8862** | 0.944/0.854 | +0.0261 | ≥0.89 ✓ |
| retinamnist | 0.8256 | **0.7011** | **0.4625** | 0.717/0.524 | −0.0159 | 0.63–0.80 ✓ |

要点：

1. **全部 5 数据集 test AUC 落在 rubric A3 区间**，且与论文数值偏差全部在 ±0.03 以内
   （容差 ±0.05–0.08）。
2. **难度排序完全一致**：实测 `blood > pneumonia > derma > breast > retina`
   （0.9978 > 0.9701 > 0.9302 > 0.8997 > 0.7011），论文锚 `Blood > Pneumonia > Derma ≈
   Breast > Retina`。两个最易（Blood）与最难（Retina）的差距 ≈0.30 AUC，与论文 ≈0.28 一致，
   直观体现“难度差异巨大”。
3. **结论标签：`supported`。**

## 5. AutoML 论述的说明

论文另一论断是 AutoML（Auto-sklearn/AutoKeras）与 ResNet-18 基线接近。本任务冻结数据仅含 5 个
2D 数据集，无 AutoML 检查点与对应资源，故未复现 AutoML 部分；该部分不影响主论断判定（主论断锚
为 ResNet-18 基线性能 + 难度差异），方向上 AutoML 已在论文 Table 5 报告与 ResNet 同量级。

## 6. 局限与讨论

- **超参/增强差异**：论文基础建设使用官方较重的随机增强（random affine/rotation），并可能使用
  余弦 LR 等多轮随机重复取最优；本复现用较轻增强 + 单 seed。因此个别 ACC（如 Retina 0.4625 vs
  0.524）存在偏差，仍在可行波动范围内；AUC 为主要判据，波动远小于容差。
- **AUC 口径**：采用官方 macro one-vs-rest AUC；若改用 ovo 或 micro，数值会略有不同
  （方向不变）。已固定并写入 `metrics.json`。
- **单一 run**：未做 5-10 重复度 + 均值/方差；Retina 这类小数据集（train 1080）方差较大。
  已给出固定 seed 的完整重算路径。
- **模型变体**：ResNet-18 stem 为 3×3/stride1 的 28×28 适配版，与论文原文 resnet18 直接跑
  数值相近，但非逐位二进制一致；我们在报告中如实说明。
- **测试集只用一次**：best-val 选择后 test 仅评估一次，杜绝调训泄漏。

## 7. 文件清单

```
claim.md                    # 结论判定（supported）+ 关键数字
solution.md                 # 方法 + 结果摘要
report.md                   # 本报告
run_all.sh                  # 一键复现脚本
code/
  config.py                 # 数据定位 / 元数据 / 超参 / 论文锚（仅对照）
  data_stats.py             # 类别计数 + 划分规模（A1）
  train.py                  # ResNet-18 训练 + 评估 + 结果导出（A2/A3/C2）
results/
  evidence_table.csv        # 每数据集一行（dataset,n_classes,train_size,test_size,model,auc,acc,…）
  metrics.json              # 类别计数、AUC/ACC、vs 论文对照、难度排序、结论标签
  class_counts.json         # 逐分片逐类计数
  split_sizes.csv           # 各划分规模
  checkpoints/<dataset>_best.pt
```

依赖：Python ≥3.10，numpy，scikit-learn，torch≥2.0，torchvision。

复现：

```bash
bash run_all.sh --device cpu --epochs 45     # 或 --device cuda（推荐，~17 分钟）
# 若数据不在默认路径：export MEDMNIST_DATA_DIR=/path/to/dir 再执行
```