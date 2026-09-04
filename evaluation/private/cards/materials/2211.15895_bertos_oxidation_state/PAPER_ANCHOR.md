# PAPER_ANCHOR: 2211.15895_bertos_oxidation_state（私有）

目标论文（隐藏）：Fu et al., arXiv:2211.15895 / Adv. Sci. 2023。锚全部摘自论文原文（Abstract/正文），禁臆造。冻结数据复现值附于每条（编译期完整性核对，非自测实验）。

## 锚 1（全元素精度，主锚）
- 指标：原子位点级氧化态预测精度 PS（token-level accuracy）
- 论文数值：**96.82%**（cleaned ICSD 全元素）；**97.61%**（氧化物材料）
- 出处：Abstract（"achieves 96.82% accuracy for all-element oxidation states prediction benchmarked on the cleaned ICSD dataset and achieves 97.61% accuracy for oxide materials"）；Table 1
- 口径：正确原子位点 / 全部原子位点（190,468 sites 口径，OS-ICSD-CN）
- 冻结数据复算（官方 checkpoint，本环境 CPU 推理）：ICSD 模型×ICSD 测试 = **96.25%**（295,515 sites）；ICSD_oxide 模型×ICSD_oxide 测试 = **97.04%**（236,003 sites）
- 容差：±1.5 pp（论文值 96.82/97.61；冻结模型复现差 ≤0.6 pp）

## 锚 2（OS-ICSD-CN 与交叉矩阵）
- 指标：PS 于 OS-ICSD-CN 测试集；Table 1 4×4 精度矩阵
- 论文数值：**96.27%**（OS-ICSD-CN 测试，190,468 原子位点；Table 1 同格 96.28%）；Table 1 矩阵（Train\Test）：OS-ICSD 96.82/96.28/97.51/97.11；OS-ICSD-CN 95.92/96.27/96.60/96.95；OS-ICSD-oxide 95.78/94.96/97.61/97.14；OS-ICSD-CN-oxide 94.95/94.85/96.70/96.97
- 出处：Sec 3 Overall performance（"we evaluate its performance over the OS-ICSD-CN test dataset with 3,724 unique compositions … Out of 190,468 atomic sites, our algorithm achieves 96.27% accuracy"）；Table 1
- 冻结数据复算：ICSD_CN×ICSD_CN = **95.75%**（200,020 sites）；ICSD×ICSD_CN = 95.85%（论文 96.28）；ICSD×ICSD_oxide = 96.94%（论文 97.51）；ICSD_CN_oxide×ICSD_CN_oxide = 96.55%（论文 96.97）
- 容差：对角线 ±1.5 pp；交叉项 ±2 pp

## 锚 3（化合物级与元素分组）
- 指标：PC（化合物全对比例）、PCASA（化合物级平均位点精度）、金属/非金属位点精度、Pymatgen 对比
- 论文数值：**PC = 87.76%**；**PCASA = 97.16%**；Pymatgen oxid state guess 仅 **4.49%** 样本可确定氧化态；金属位点 **97.12%**、非金属位点 **96.05%**
- 出处：Sec 3（"PC accuracy reaches 87.76%. In contrast, when we use the Pymatgen's oxid state guess function, only 4.49% of the test samples can be assigned definite oxidation states. We further calculate the compound-level average site accuracy PCASA, which reaches 97.16%"；"The overall accuracy of the metal atomic site OS reaches 97.12%, and the nonmetal ones reaching 96.05%"）
- 冻结数据复算：ICSD_CN×ICSD_CN PC = **84.80%**（3,724 化合物）；金属 95.49%（41,732 sites）/ 非金属 95.81%（158,288 sites，按标准金属元素表分组）
- 容差：PC ±3 pp；金属/非金属 ±2.5 pp（分组元素表口径差异允许）；Pymatgen 4.49% 为佐证锚（需 pymatgen，可选复现）

## 锚 4（数据集规模，供 B 证据核查对照）
- 论文数值：OS-ICSD-CN 训练集 **31,827 个唯一组成**、测试集 **3,724 个唯一组成**；OS-ICSD-CN 测试原子位点 190,468
- 出处：Sec 3（"31,827 samples with unique compositions … OS-ICSD-CN test dataset with 3,724 unique compositions"）
- 冻结数据核对：ICSD_CN.zip train 块 31,827 ✓、test 块 3,724 ✓（位点计数口径差异见 SOURCE.md，202,410 vs 190,468，与论文计数方法有关）
- 容差：块数必须精确一致（31,827 / 3,724）