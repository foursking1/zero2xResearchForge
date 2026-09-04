# PAPER_ANCHOR（私有，仅裁判/编译者可见）：2401.10290 — 3h 提前 Kp 预测

> 用途：LLM judge 的判分基准。禁止向作答 agent 暴露本文件。所有论文数值均从 arXiv:2401.10290v1 正文/图抽出，禁止臆造。编译器探针数值基于本卡冻结数据（F:\dataset\astro\2401.10290_kp3h_geomagnetic_storm\），仅供判分校准。

## 锚 A1 — 核心结果：2021 测试期 3h 提前 Kp 预测准确率（核心结果锚，判 A 维度）

| 项 | 值 |
|---|---|
| 指标名 | test 期 accuracy（预测 Kp 在真实 Kp ±1 以内的事件占比） |
| 论文数值 | **82.55%** |
| 出处 | Abstract（"we are able to achieve an accuracy of 82.55% on data collected in 2021 when making early predictions three hours in advance"）；§3 Experiments 末段（"Additional downsampling with top 50 features was able to achieve an accuracy of 82.55%"）；§4 Conclusions（"The algorithm achieves a prediction accuracy at 82.55% by keeping only the most informative features (top 50 features), and downsampling data instances that occur more often (i.e., lower Kp indices) by half."）；Figure 7（Accuracy by different algorithms） |
| 定义口径 | 数据全部来自 2021；train=前 9 个月（Jan–Sep），test=后 3 个月（Oct–Dec）；RF 回归 100 棵树、mtry=p/3（§2.1/§3）；输入特征为 780 维滞后特征（OMNI 5-min 太阳风 7 变量×108 lag、Dst 3 lag、Kp 8 lag，§2）；top-50 特征选择 + 训练期下采样 L=2（丢弃一半低 Kp 样本，§3）；accuracy = %(test 事件中 \|pred−actual\| ≤ 1)，Kp 为 0–9 连续标度 |
| 容差（判分用） | 见 SCORE_RUBRIC.md A 维度数值带。**重要注记：论文 82.55% 在冻结数据下不可精确复现**（论文未公开特征构造/预处理全部细节）。编译器探针（冻结 5-min OMNI + GFZ Kp + 京都 Dst，3h 网格，中位数插补，RF 100 树）：全特征 acc≈0.7456、top-100≈0.7333、top-50≈0.7374、top-50+下采样≈0.7075、持久性基线≈0.7252、均值基线≈0.5850。因此 A 满分带按 [0.65, 0.82] 校准（SuryaBench 同款"冻结数据固有难度"处理）；>0.82 不直接加分，需解释来源。 |

## 锚 A2 — 数据规模与特征结构（口径锚）

| 项 | 值 |
|---|---|
| 指标名 | 特征维度 / 数据点 / 时间事件 |
| 论文数值 | **780 features；2.1 million data points；2679 time events** |
| 出处 | §2 The method（"Together the data translates to 2.1 million data points, 2679 time events and 780 features (variables)…"） |
| 定义口径 | 特征包括 Kp、FMA（磁场总强度）、Bx/By/Bz、太阳风速度、密度、温度，按各自采样间隔滞后：OMNI 5-min（9h lookback→108 lag/变量）、Dst hourly（3 lag）、Kp 3h（24h lookback→8 lag）；response = 预测时刻 3 小时后的 Kp |
| 冻结数据对应 | 冻结包可实现 767 特征（7×108 + 3 + 8）；2021 全年 3h 网格事件 ≈2,916（warm-up 后 2,911 完整行；train 2,181 / test 735，中位数插补口径）。与论文"780/2679"的差异来自事件网格与缺测处理，判分不以此为准 |

## 锚 A3 — 特征重要性随滞后衰减（可证伪的子论断）

| 项 | 值 |
|---|---|
| 指标名 | 变量重要性随时间滞后的衰减 |
| 论文数值 | 定性+图示：重要性随"到预测时刻的时间"快速下降（Figure 5）；6 小时前的测量 barely informative（§3/§4： "The importance of variables from solar measurements decreases very quickly as the amount of advance in prediction time increases. Measurements taken 6 hours in advance becomes barely informative"） |
| 出处 | §3 Experiments，Figure 5（Variable importance，x 轴 Time till prediction 0–500 分钟，Kp/FMA/dst 各自滞后点）；§4 Conclusions |
| 编译器探针 | 冻结数据 RF 特征重要性：近端（≤15 min 滞后）均值 ≈0.00302 vs 远端（495–505 min 滞后）均值 ≈0.00071，比值 ≈4.3×。判分阈值：agent 报告近端/远端重要性比值 ≥ 2 即视为复现该子论断 |

## 辅助数据事实（裁判 B 维度抽查基准；均从冻结数据算出）

| 字段 | 冻结值 | 来源 |
|---|---|---|
| test 期（Oct–Dec 2021，3h 网格）事件数 | 735（完整特征行） | `omni_5min_2021.csv`+`kp_gfz_2021.csv`+`dst_kyoto_2021.csv` 构造 |
| 2021 年最强地磁暴 | 2021-11-04；GFZ Kp 峰值 7.667（09:00–12:00 区间）、京都 Dst 最低 −105 nT（11-04 13:00） | `kp_gfz_2021.csv`（2021/11/4, HR_START=9.0, Kp=7.667）；`dst_kyoto_2021.csv`（2021,11,4,13,Dst=−105） |
| 数据行数 | OMNI 5-min 105,120；GFZ Kp 2,920；京都 Dst 8,760；aux hourly 8,760 | 三个 CSV + aux CSV |
| Kp/Dst 交叉验证 | aux hourly `kp_index/10` 与 GFZ Kp 完全一致（如 11-04 09:00 均 7.7）；`dst_index_nt` 与京都 Dst 逐时一致（11-04 13:00 均 −105） | `aux_omni_hourly_2021.csv` vs GFZ/京都 CSV |
| 下采样口径 | L=2 = 训练时对 Kp<3 的样本丢弃一半（论文 §3） | — |

## 判分对照速查（judge 用）

- test 期 ±1 accuracy ∈ [0.65, 0.82] 且报持久性/均值基线且做重要性衰减分析（近/远比值≥2）且讨论 82.55% 差距 → A=60。
- accuracy ∈ [0.58, 0.65)∪(0.82, 0.90]，或落入满分带但缺基线/衰减分析 → A=30。
- accuracy < 0.58（≈均值基线）或 > 0.90（疑似泄漏）或未做严格时间切分 → A=0。
- B 抽查两数：test 期事件数 735（3h 网格口径）；11-04 Kp 峰值 7.667 / Dst 最低 −105（交叉验证 7.7 / −105）。
