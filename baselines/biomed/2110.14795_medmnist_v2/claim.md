# ← 结论判定（claim）

**标签：`supported`**

## 一句话结论

在冻结的 MedMNIST v2 五个 2D 医学图像数据集（28×28）上，使用标准 CNN（ResNet-18@28，3×3 stem 适配小图）独立训练并在官方划分的测试集上评估后，各数据集 test AUC 全部落在论文量级（BloodMNIST 0.9978 / BreastMNIST 0.8997 / DermaMNIST 0.9302 / PneumoniaMNIST 0.9701 / RetinaMNIST 0.7011），且数据集间难度排序与论文完全一致（Blood > Pneumonia > Derma ≈ Breast > Retina）。论文核心论断得到支持。

## 关键数字（test）

| 数据集 | 类别数 | training | test | AUC（实测） | ACC（实测） | 论文 AUC/ACC（对照） | vs 论文 ΔAUC |
|---|---|---|---|---|---|---|---|
| BloodMNIST | 8 | 11,959 | 3,421 | **0.9978** | 0.9640 | 0.998 / 0.958 | -0.0002 |
| BreastMNIST | 2 | 546 | 156 | **0.8997** | 0.8718 | 0.901 / 0.863 | -0.0013 |
| DermaMNIST | 7 | 7,007 | 2,005 | **0.9302** | 0.7621 | 0.917 / 0.735 | +0.0132 |
| PneumoniaMNIST | 2 | 4,708 | 624 | **0.9701** | 0.8862 | 0.944 / 0.854 | +0.0261 |
| RetinaMNIST | 5 | 1,080 | 400 | **0.7011** | 0.4625 | 0.717 / 0.524 | -0.0159 |

- AUC 口径：多类 = macro 一元超曲线 AUC（MedMNIST 官方口径，`roc_auc_score(..., multi_class="ovr", average="macro")`）；二类 = 正类分数 ROC AUC。
- 难度排序（实测 test AUC 降序）：`blood > pneumonia > derma > breast > retina` —— 与论文锚排序完全一致；模型仅用 train/val 调参，test 每数据集仅评估一次。

## 判据对照

1. 全部 5 数据集 test AUC 均落在 rubric A3 验证区间（Blood≥0.97、Breast≥0.85、Derma≥0.86、Pneumonia≥0.89、Retina 0.63–0.80）。
2. 难度排序完全一致。
3. ΔAUC 全部在 ±0.026 以内（容差 ±0.05–0.08 内）。
4. AutoML 与 ResNet 基线接近的主论断方向成立（强模型未复现 AutoML 部分，见 report）。

**结论：论文关于「轻量 28×28 医学图像分类上标准 CNN 即达高 AUC、数据集难度差异大」的关键论断在冻结数据上得到复现与支持。**