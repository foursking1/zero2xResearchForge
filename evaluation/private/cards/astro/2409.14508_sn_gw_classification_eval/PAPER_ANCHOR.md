# PAPER_ANCHOR.md（私有：锚数值与出处）

论文：Abylkairov et al. 2025, arXiv:2409.14508v2 "Evaluating Machine Learning Models for Supernova Gravitational Wave Signal Classification"
锚抽取日期：2026-08-13。数值均来自论文 Table IV/正文，无臆造。

## 锚 A1（主锚）：GR 数据 8 模型分类准确率（mean±std %，Table IV GR 行）
- CNN 97.4±2.0；RNN 97.7±1.9；RF 96.8±2.4；**SVM 99.5±1.0（最高）**；NB 48.9±5.0；LR 95.8±2.1；k-NN 93.8±2.6；XGB 96.6±2.3
- 出处：Table IV 第 1 行；§III.A 正文 "SVM ... highest mean accuracy of 99.5±1.0%"，"except for Naïve Bayes, all models demonstrate strong performance"
- 定义口径：accuracy=正确预测/总预测（式 2）；64:16:20 切分，100 次随机重复取 mean±std
- 容差：冻结数据重算与论文值 |Δ| ≤ 3pp；主张成立判据 = 除 NB 外 7 模型均 >90% 且 SVM ≥ 其余模型均值（允许 SVM 与 RNN/CNN 在 1pp 内并列）

## 锚 A2：GREP→GR 跨域准确率（Table IV GREP→GR 行）
- CNN 37.9±6.5；RNN 30.5±5.5；RF 35.2±3.1；SVM 29.9±2.5；NB 38.8±4.2；LR 41.4±3.1；k-NN 33.1±3.5；XGB 34.5±3.1
- 出处：Table IV 第 3 行；§III.B "average accuracy of approximately 35%"；SVM "accuracy drops to 29.9±2.5%"
- 定义口径：GREP 训练、GR 测试
- 容差：重算与论文值 |Δ| ≤ 3pp；主张成立判据 = 全部模型 <50%（论文 29.9–41.4%）

## 锚 A3：时间归一化后 GREP*→GR*（Table IV 第 4 行）
- CNN 62.0±4.8；RNN 67.5±5.2；RF 43.6±4.5；SVM 68.0±4.3；NB 36.4±4.7；LR 57.1±4.8；k-NN 57.8±4.4；XGB 43.6±4.6
- 出处：Table IV 第 4 行；§III.B "even the best-performing model, SVM, reaches only 68.0±4.3% accuracy"；"accuracy improves to ~60%"
- 定义口径：按 f_peak 归一化时间后 GREP 训练、GR 测试
- 容差：重算与论文值 |Δ| ≤ 4pp；主张成立判据 = 最高准确率 ∈ (50%, 70%) 且明显高于 A2 同模型（>+10pp）

## 锚 A4（辅助）：数据集口径（§II.A）
- 452 GR（SFHo 116 / LS220 120 / HSDD2 108 / GShenFSU2.1 108）；412 GREP（105/105/103/99）；10 kHz；−2~6 ms 窗口（81 点）；振幅按 D·Δh 归一化
- 出处：§II.A；冻结 CSV 计数与此完全一致

## 锚 A5（背景）：方法规格
- CNN/RNN 架构（Table I/II）、经典模型超参搜索空间（Table III）、SVM poly degree 4 C=10（§III.A）、100 次随机切分（§II.B）、评估重复次数任务按 ≥10 次执行
- 说明：论文正文 PCA 提到 "reduce from 811 to 2" 与 CNN Input(81) 不一致，视为论文笔误；任务以 81 点窗口为准
