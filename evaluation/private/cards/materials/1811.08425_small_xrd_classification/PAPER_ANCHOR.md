# PAPER_ANCHOR: 1811.08425_small_xrd_classification（私有）

论文：Oviedo et al., npj Computational Materials 5, 60 (2019)；arXiv:1811.08425。
锚全部摘自论文正文/表格/图，禁止臆造。

## 锚 1（主锚，A 维度）
- 指标名：空间群分类 5 折交叉验证平均子集精度（Case 3）
- 论文数值：**89%**（正文表述 "more than 93% and 89%"；摘要 "93% and 89%"）
- 出处：摘要（p3）；Sec III "Classification results and All Convolutional Neural Network"（p17）；Table 1（Case 3 行）
- 定义口径：Case 3 = 全部模拟谱（164 条）增强 2000 + 80% 实验谱（88 条）训练，20% 实验谱测试，5 折 CV（shuffle + 固定种子）；a-CNN = 3 层 1D 卷积（32 filters，kernel/stride 8/5/3）+ ReLU + GAP + softmax；BCE；Adam；batch 128；早停；Keras 2.2.1/TF。
- 容差：报告均值 ≥0.86 → 满分；0.80–0.86 → 45/60；0.75–0.80 → 30/60；0.60–0.75 → 15/60；<0.60 → 0（详见 SCORE_RUBRIC.md）。

## 锚 2（增强效果，佐证）
- 指标名：物理信息数据增强对分类精度的影响
- 论文数值：无增强 **<60%** → 增强后 **93%**（维度）/ **89%**（空间群）；Table S6：物理信息增强 vs 传统噪声增强平均提升 **>12% 绝对**
- 出处：Sec IV Conclusions（p22-23："A few thousand augmented spectra are found to increase our classification accuracy from <60% to 93% for dimensionality and 89% for space-group."）；Sec II（p16，Table S6 引用）
- 定义口径：增强 = 峰缩放/峰消除/图案平移（Eqs.1-3），模拟与实验各 2000 条
- 容差：有增强 ≥0.80 且无增强 <0.70 → 佐证成立；仅报告有增强结果不扣分

## 锚 3（数据粗化，加分）
- 指标名：2θ 步长粗化后的分类精度
- 论文数值：基线步长 **0.04°**；最高精度区间 **0.04–0.08°**；步长 **≤0.16°** 时精度 **≥85%**（维度与空间群均满足）；采集时间缩短 75%，<5.5 分钟
- 出处：Sec III "Impact of data coarsening"（p19-20）；Fig 4
- 容差：0.16° 步长下 SG 精度 ≥0.80 视为符合趋势

## 辅助事实（裁判核查用）
- 实验谱 88 条 / 7 空间群（类别数 4/17/1/13/4/2/47）；维度分类 75 条 / 3 类（93% 锚，本任务不评估，因维度数据未随仓库发布）
- 模拟谱 164 条（ICSD 结构，Panalytical Highscore v4.7 模拟，随机晶向）
- F1 macro > 0.85（Sec IV，p23）
- 数据源：作者仓库 PV-Lab/AUTO-XRD（Apache-2.0）
