# PAPER_ANCHOR.md（私有：锚数值与出处）

论文：Muthukrishna et al. 2019, arXiv:1903.02557, MNRAS "DASH: Deep Learning for the Automated Spectral Classification of Supernovae and their Hosts"
锚抽取日期：2026-08-13。以下数值均来自论文正文/表格，无臆造。

## 锚 A1（主锚）：OzDES 总体匹配率
- 数值：**197/212 = 92.9%（论文写 93%）**
- 出处：§5.2 正文 "It matched the ATel classification for 93% of the spectra, correctly classifying 197 out of the 212 supernovae."；汇总表 Table 1（§5.2 下方）
- 定义口径：DASH top-1 分类与 ATel 分类一致（表 1 汇总 212 条；? 标签单独计数）
- 容差/判定：裁判以冻结子集重算提交值（一致性 ±2pp）；主张成立判据为冻结子集总体匹配率 ≥ 0.80（冻结子集 69 条为全集 212 条的真实子集，样本构成略偏，见 CALIBRATION）

## 锚 A2：分型匹配率（Table 1）
- 数值：Ia 127/129=98.4%；Ia? 34/43=79.1%；II 25/28=89.3%；II? 7/9=77.8%；Ibc 1/1=100%；Ibc? 2/2=100%
- 出处：Table 1（第 2、3 列）
- 定义口径：DASH 与 ATel 同大类即匹配（Ia、II、Ibc；? 归入大类）
- 容差：冻结子集分型匹配率与论文对应类绝对差 ≤ 15pp（子集样本量小，允许波动）；Ia 类要求 ≥ 0.90（论文 98.4%，冻结子集 Ia 47 条）

## 锚 A3：速度
- 数值：**212 条全部在 20 秒内自主分类完成**（"we were able to autonomously classify all 212 spectra in under 20 seconds"）
- 出处：§5.2 正文
- 定义口径：单批次自动分类（无人干预）墙钟时间；§5.3 补充：单条光谱 DASH 数秒 vs Superfit 数十分钟
- 容差：冻结 69 条在提交机器上报告实际耗时即可（主张的可扩展性定性支持）；若 >10 分钟需说明原因并影响 A3 评分

## 锚 A4：逐对象 DASH 分类记录（Table 2，用于 B 部分抽查重算）
- 数值示例（论文 Table 2 / Appendix C 记录，格式：对象 z ATel类型 DASH类型(龄窗) p Reliable）：
  - DES16C3bq（Run24，z=0.241，ATel SNIa max）→ **Ia-norm (-2 to 2)，p=1.0，Reliable**
  - DES16C3bq（Run25，z=0.237，ATel Ia post-max）→ **Ia-norm (2 to 6)，p=0.868，Reliable**
  - DES16E2aoh（Run25，z=0.403，ATel Ia post-max）→ **Ia-91T (-6 to -2)，p=0.864，Reliable**
  - DES16E1ciy（Run26，z=0.174，ATel SNIa near-max）→ **Ia-norm (2 to 6)，p=0.992，Reliable**
- 出处：Appendix C Table 2（第 4–6 列：DASH 分类、softmax 概率、Reliable 标志）
- 定义口径：同对象、同历元（z 匹配）下 DASH top-1 类型
- 容差：抽查对象预测与 Table 2 同子类型（如 Ia-norm）；若模型 v06 与论文模型有差，放宽为同大类（Ia/II/Ibc）并注明

## 锚 A5（背景锚，非必检）：验证集混淆矩阵
- 数值（Fig 6，80/20 训练/验证切分，Model 1）：Ia-norm 0.99、Ia-91T 0.78、Ia-91bg 0.92、IIb 0.90、Ic-norm 0.77、Ic-broad 0.92、Ibn/IIP/IIL/Ic-pec 1.00 等
- 出处：§5.1 + Figure 6
- 说明：复现需按论文切分重训，本任务不要求（冻结数据以官方模型推理为主）；仅作背景参照
