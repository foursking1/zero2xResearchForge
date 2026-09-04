# 论文锚：2607.16250_multiomics_breast_cancer_er

## 锚清单（全部来自论文，禁止臆造）

| # | 指标 | 论文数值 | 出处 | 定义口径 | 容差 |
|---|---|---|---|---|---|
| 1 | RNA-only RF 分类准确率 | 92.35±1.07% | Table II（RNA-Only 结果） | 五折 CV 下 RNA 表达预测 ER 状态的分类准确率 | 相对差 ≤10% 满分档（Acc 80-95%） |
| 2 | RNA-only RF 宏 F1 | 89.28±1.57% | Table II | 同上口径 Macro F1 | 参照 |
| 3 | RNA-only XGBoost Balanced Accuracy | 88.69±2.18% | Table II | 同上口径 Balanced Accuracy | 参照 |
| 4 | RNA-only XGBoost ROC-AUC | 95.61±1.50% | Table II | 同上口径 ROC-AUC | 参照 |
| 5 | 多组学集成 RF Balanced Accuracy / ROC-AUC | 90.3% / 97.1% | Abstract（"Random Forest achieved the best overall performance in the integrated multi-omic setting, obtaining a balanced accuracy of 90.3% and an ROC-AUC of 97.1%"） | 集成（RNA+CNV+RPPA）最优模型 | Balanced Acc ≥85% + AUC≥单组学 |
| 6 | 队列规模与类别不平衡 | 549 例；ER+ 75.4% / ER- 24.6% | §III Dataset Description | 清洗后 TCGA-BRCA 队列 | 相对差 ≤15% |
| 7 | 特征数 | RNA 604 / CNV 860 / RPPA 223（合计 1,687） | §III | 特征选择后特征数 | 参照（以实际实现为准） |

## 备注
- 主论断：RNA 最强；多组学集成小幅一致提升；折内特征选择防泄漏。
- 论文出处：arXiv:2607.16250，Abstract、Table II/III、§III；数值以论文 PDF 为准。冻结数据为 cBioPortal datahub 同源 TCGA-BRCA 数据（论文用 UCSC Xena）。