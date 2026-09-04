# 论文锚：1703.00564_moleculenet_benchmark

> 用途：LLM judge 判分基准（私有）。数值来自 arXiv:1703.00564v3（Chem. Sci. 2018），禁止臆造。

## 锚清单

| # | 指标 | 论文数值 | 出处 | 定义口径 | 容差 |
|---|---|---|---|---|---|
| 1 | HIV（scaffold 划分）ROC-AUC | GraphConv 0.763±0.016、KernelSVM 0.792、XGBoost 0.756、Logreg 0.702、IRV 0.737、Multitask 0.698、Bypass 0.693、Weave 0.703 | Table 5 | 8 模型，scaffold 划分，AUC-ROC | 参照锚（方向 + ±0.05 内可判一致） |
| 2 | BACE（scaffold 划分）ROC-AUC | Logreg 0.781±0.010、KernelSVM 0.862、XGBoost 0.840 | Table 5 | AUC-ROC | 参照锚 |
| 3 | 主论断 | 「可学习表示总体最优，但数据稀缺/高度不平衡时吃力；物理感知特征对 QM/生物物理数据可能比算法更重要」 | Abstract / §Results | 方向性 | 方向 |
| 4 | 数据集规模 | HIV 41,127 / BACE 1,513 / BBBP 2,039 / ClinTox 1,477 / ESOL 1,128 / FreeSolv 642 / Lipophilicity 4,200 | Table 1 | 分子数 | 精确（冻结数据核验） |
| 5 | 评价指标选择 | 正例率 <2% 用 PRC-AUC，否则 ROC-AUC；分类默认 ROC-AUC，回归 RMSE | §Metrics | 协议锚 | 方向 |

## 备注
- 主论断：可学习表示（图模型）总体占优但有条件；本卡冻结数据 = 论文 7 个公共数据集（DeepChem 官方 CSV + OGB 划分），同源。
- 判分提示：以「图模型 ≥ 指纹基线（多数数据集）+ 数据稀缺/不平衡时优势减弱」的方向为主判据；绝对数值受实现/划分影响，不强求。
