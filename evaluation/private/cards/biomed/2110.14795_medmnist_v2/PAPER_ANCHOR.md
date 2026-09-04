# 论文锚：2110.14795_medmnist_v2

> 用途：LLM judge 判分基准（私有）。数值来自 arXiv:2110.14795v3（Scientific Data 2023），禁止臆造。

## 锚清单

| # | 指标 | 论文数值（ResNet-18 @28） | 出处 | 定义口径 | 容差 |
|---|---|---|---|---|---|
| 1 | BloodMNIST AUC/ACC | 0.998 / 0.958（8 类，train 11,959） | Table 3 | 28×28，官方划分 | ±0.02 |
| 2 | BreastMNIST AUC/ACC | 0.901 / 0.863（2 类） | Table 3 | 28×28 | ±0.05 |
| 3 | DermaMNIST AUC/ACC | 0.917 / 0.735（7 类） | Table 3 | 28×28 | ±0.05 |
| 4 | PneumoniaMNIST AUC/ACC | 0.944 / 0.854（2 类） | Table 3 | 28×28 | ±0.05 |
| 5 | RetinaMNIST AUC/ACC | 0.717 / 0.524（5 类） | Table 3 | 28×28 | ±0.08 |
| 6 | 主论断 | 轻量基准上标准 CNN 性能高；数据集间难度差异大（Blood≈0.998 vs Retina≈0.72）；AutoML 与 ResNet 接近 | Abstract / Table 3/5 | 方向性 | 方向 |

## 备注
- 主论断：28×28 医学图像用标准 CNN 可达论文报告量级；难度排序 Blood>Pneumonia>Derma≈Breast>Retina。
- 判分提示：以「各数据集 AUC 落论文 ±0.05-0.08 区间 + 难度排序一致」为主判据；实现/超参差异可解释偏差。
