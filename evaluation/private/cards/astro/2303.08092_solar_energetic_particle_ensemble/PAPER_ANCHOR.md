# PAPER_ANCHOR.md（私有：锚数值与出处）

论文：O'Keefe et al. 2024, Adv. Space Res. "The Random Hivemind: An Ensemble Deep Learner Application to Solar Energetic Particle Prediction Problem"（arXiv:2303.08092v2）
锚抽取日期：2026-08-13。数值均来自论文表格/正文，无臆造。

## 锚 A1（主锚）：TSS（中位数±MAD，Table 2）
- CoNN 0.906±0.042；Committee 0.926±0.023；RH v1 0.915±0.010；RH v2 0.944±0.005
- 出处：Table 2 第 4 行；§4 正文 "TSS=0.906±0.042 for the CoNN ... increased to TSS=0.926±0.023, TSS=0.915±0.010, and TSS=0.944±0.005 (RH v2)"
- 定义口径：TSS = Recall − FP/(FP+TN)（论文 Eq. 定义，50 次实验的中位数与 MAD）
- 容差：冻结数据上主张成立判据 = RH v2 中位 TSS ≥ CoNN 中位 TSS（相对锚）；绝对值允许偏差 ±0.05（数据版本差异）

## 锚 A2：TSS（均值±std，Table 1）
- CoNN 0.906±0.043；Committee 0.926±0.035；RH v1 0.915±0.029；RH v2 0.944±0.023
- 出处：Table 1
- 容差：同 A1（相对对比为主）

## 锚 A3：HSS（中位数±MAD，Table 2）
- CoNN 0.163±0.026；Committee 0.168±0.005；RH v1 0.163±0.010；RH v2 0.168±0.008
- 出处：Table 2 第 5 行；§5 Conclusion 复述
- 容差：RH v2 HSS ≥ CoNN HSS（无系统性下降）；绝对值 ±0.02

## 锚 A4：ROC AUC（均值±std，Table 1）
- CoNN 0.9903±0.0005；Committee 0.9907±0.0001；RH v1 0.9901±0.0005；RH v2 0.9906±0.0003
- 出处：Table 1 末行
- 说明：辅助锚；无需硬判，报告即可

## 锚 A5：混淆矩阵（中位数±MAD，Table 2）
- TP 22.8±1.5 / 23.2±0.5 / 22.9±0.0 / 23.6±0.0；FN 1.2±1.5 / 0.8±0.5 / 1.1±0.0 / 0.4±0.0；FP 237±46.5 / 219±10 / 225.7±20 / 224.8±15.5；TN ≈5233–5251
- 出处：Table 2；§4 "capturing almost every single SEP flare in the test data set (which is 24 events on average)"
- 说明：测试集每切分约 5,494 样本（18,311×0.3）；冻结数据测试集规模会不同，锚用于方向性检查（FN 很小、FP/TN≈1/23、TP/FP≈1/10）

## 锚 A6：数据集口径（§2）
- 18,311 耀斑（2002–2017）；64 SEP vs 18,247 非 SEP（1/285 不平衡）；8 C 级 / 36 M 级 / 20 X 级 SEP 关联耀斑；12 特征（§2.2 映射）；70/30 随机切分（§2 说 10 次，§4/表注说 50 次——论文内部不一致，任务按 ≥10 次执行并注明）
- 出处：§2 正文与 Figure 1/2
- 容差：冻结数据 24,797 行 / 76 SEP（门户当前版本），应用排除准则后 24,570 / 74；差异须报告
