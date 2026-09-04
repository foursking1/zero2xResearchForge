# PAPER_ANCHOR: 2608.06662_mlip_cross_geometry（私有）

目标论文（隐藏）：arXiv:2608.06662v1。锚全部摘自论文原文（摘要/正文章节/图注），禁臆造。括号内为编译期数据核验结果（非自测实验）。

## 锚 1（零样本最佳模型：ORB-V3 全局误差）
- 指标：参考能量对齐后全局（全几何）能量 RMSE（meV/atom）与力 RMSE（meV/Å）
- 论文数值：**energy RMSE = 6 meV atom⁻¹；force RMSE = 197.3 meV Å⁻¹**（26 个预训练 MLIP 零样本基准中最佳，ORB-V3，MP-NC 组）
- 出处：Abstract（"the best zero-shot model (ORB-V3) reaches energy and force root-mean-square errors of 6 meV atom−1 and 197.3 meV ˚A−1, respectively, with the largest force errors in neck and wire configurations"）；Sec III.B（"ORB-V3 is the best-performing MP-NC model, with an energy RMSE of 6 meV atom−1 and a force RMSE of 197.3 meV ˚A−1"）；Figure 2A
- 口径：26 模型零样本、仅参考能量对齐（训练划分上拟合元素级偏移 {Δµ_Zr, Δµ_O}，Sec II.B）、全局聚合
- 编译期核验：冻结数据 14,434 帧（35 文件）可作为对齐参考集；论文内部训练/测试划分标签未随数据发布，精确复现 6/197.3 依赖对齐参考集选择
- 容差：能量 ±4 meV/atom；力 ±60 meV/Å（要求报告对齐口径；数值超容差但方向/排序正确且口径合理 → 半档）

## 锚 2（均值与 MP-C/MP-NC 分组）
- 指标：全体模型平均 aligned 能量/力 RMSE；MP-NC 与 MP-C 分组误差关系；MP-C 组最佳模型
- 论文数值：**全体均值 ≈ 20 meV atom⁻¹ 与 400 meV Å⁻¹**；**MP-NC 组整体误差低于 MP-C 组**；**MP-C 组最佳 ORB-V2-MPtrj：energy 107.67 meV atom⁻¹、force 309.1 meV Å⁻¹**
- 出处：Sec III.B（"the mean aligned energy and force RMSEs are around 20 meV atom−1 and 400 meV ˚A−1, respectively"；"Within the MP-C group, ORB-V2-MPtrj reaches 107.67 meV atom−1 and 309.1 meV ˚A−1"；"Models categorized as MP-NC achieve lower errors as a group in this benchmark"）
- 口径：对 26 模型平均；MP-C/MP-NC 按 Matbench Discovery 惯例分组（代码/权重可用性 + 训练数据许可）
- 容差：均值能量 ±5 meV/atom、力 ±100 meV/Å；ORB-V2-MPtrj 能量 ±10、力 ±40（需实际运行该模型才判数值；仅报告分组方向不给数值分）

## 锚 3（几何依赖方向性）
- 指标：逐几何类力 RMSE 相对排序；能量 RMSE 相对排序
- 论文数值：**最大力误差出现在 neck 与 wire 配置**（摘要原文）；**neck 与 wire 是大多数训练条件下最困难的评测域**（Sec III.E： "Neck and wire configurations remain the most difficult evaluation domains across most training conditions"）；体相/表面误差最低（Figure 2A 零样本散点分布）
- 出处：Abstract；Sec III.B（Figure 2A）；Sec III.E
- 口径：逐几何类聚合力/能量 RMSE；方向性判据不依赖对齐参考集（力无偏移、能量对齐仅平移）
- 容差：无容差（必须 neck/wire 力 RMSE > bulk/slab；能量低配位类 > 体相/表面类；若采样需一致协议）

## 锚 4（Figure 2B 训练对齐示例——参考锚，非核心）
- 指标：训练/微调对齐模型在 Slab/Particle/Wire 上的能量 RMSE/MAE（meV/atom）
- 论文数值：**Slab RMSE 15.39 / MAE 11.62；Particle RMSE 74.47 / MAE 39.35；Wire RMSE 60.35 / MAE 39.43**
- 出处：Figure 2B 图内标注（training-aligned 对比图；论文 Sec III.C 训练对比 引用）
- 口径：微调/训练后模型在保留测试划分上的对齐能量误差；重算需训练模型，本卡仅作参考锚，不进入 A 判分
- 容差：不判分（若 agent 主动复现并落在 ±5 meV/atom 内可在 C3 加分）

## 锚 5（B 组定性方向，加分项）
- 指标：微调 vs from-scratch；几何特化微调负迁移；属性级行为与平均误差排名解耦
- 论文数值：**微调模型能量与力误差低于 from-scratch（同 50 epoch、墙钟时间相当）**（Sec III.C）；**wire-only 微调提高其他几何能量误差 = 负迁移**（Sec III.E）；**基于平均能量/力误差的排名不能普遍预测弹性/振动/表面能/颈动力学等属性级行为**（Abstract；Sec III.F）
- 出处：Abstract；Sec III.C（"fine-tuned models achieve lower energy and force errors than their from-scratch counterparts"；"Fine-tuning and from-scratch training require similar wall-clock times"）；Sec III.E（"wire-only fine-tuning increases energy errors on several other geometries"）；Sec III.F（"Average energy and force errors do not necessarily determine the accuracy of derived physical quantities"）
- 口径：定性方向判据；本卡不要求重跑微调（加分项，方向正确 +5 上限，进入 A3 或 C 加分）
- 容差：方向性无容差