# PAPER_ANCHOR.md（私有，仅裁判/编译者可见）— 2512.06316_frb_repeater_semisupervised

> 锚必须真实来自论文；冻结数据实测为编译器探针（2026-08-14）。容差用于判分（见 SCORE_RUBRIC）。

## 锚 A1 — 核心结果：repeaters 的 DM 显著更低（核心结果锚，判 A 维度）

| 项 | 值 |
|---|---|
| 指标名 | DM（D_snr）在 repeater / non-repeater 间的差异（Mann-Whitney U） |
| 论文数值 | **μ₀=684.75 vs μ₁=464.83 pc·cm⁻³，p=4.10×10⁻⁹**（Table 1）；Abstract：「Repeaters tend to show lower dispersion measures, higher peak frequencies, and higher fluences than non-repeaters」 |
| 出处 | §2 Data and Features / Table 1；Abstract |
| 冻结数据对应 | 源级实测（编译器）：repeater n=94 mean=445.50 / median=409.74；non-repeater n=3,490 mean=686.44 / median=584.90；Mann-Whitney U **p=1.32×10⁻¹⁰**——方向、量级、显著性均与论文一致 |
| 容差（判分用） | 满分带：方向（repeater 均值 < non-repeater）；p < 1×10⁻⁵；repeater 均值 ∈ [400, 500]、non-repeater ∈ [600, 800]（源级口径） |

## 锚 A2 — 核心结果：数据集规模与特征判别性（核心结果锚，判 A/C 维度）

| 项 | 值 |
|---|---|
| 指标名 | 数据集规模 / 判别特征 |
| 论文数值 | **593 暴** = **137 重复暴（42 个重复源）+ 456 非重复暴**（§2）；「All models achieve consistently high performance, identifying dispersion measure, peak frequency, and fluence as the most discriminative features」（Abstract）；Fig 5 SHAP：DM 为最重要特征 |
| 出处 | §2 Data and Features；Abstract；§3.5/Fig 5 |
| 冻结数据对应 | CHIME 源级子集 **3,584**（repeater 94 + non-repeater 3,490）；原始 JSON 4,020 条（CHIME 3,661）；（编译器实测；DM 为冻结数据中判别性最强的可用特征） |
| 容差（判分用） | 满分带：子集行数 3,584±3；repeater 94±2；agent 说明源级/暴级差异；可选特征重要性中 DM 排第一或前二 |

## 锚 A3 — 附带（B/C 维度用）

| 项 | 值 |
|---|---|
| 指标名 | 论文 Table 3 模型表现 / 候选重复源数量 |
| 论文数值 | Table 3：测试集 recall/precision/F1 全部 ≥0.8（RF 0.85/0.86/0.85；SVM 0.83/0.82/0.83；AdaBoost **0.90/0.90/0.90**；LR 0.82/0.90/0.86；GB 0.84/0.88/0.86）；§4：168 高置信候选（153 来自 unlabeled + 15 来自 non-repeater）、36 个额外候选 |
| 出处 | §4 Results / Table 3 / Table 4 |
| 冻结数据对应 | 本包为源级特征子集，不包含论文 5 特征全量（F_d/w_p/f_p/f_lu 在源级转储中缺失）；agent 若说明「无法在源级数据上完整复现半监督流水线」为正确做法 |
| 容差（判分用） | 不直接判分；用于 C2 边界说明 |

## 编译器探针（冻结数据，2026-08-14）

- blinkverse_all_sources.json：4,020 条 FRB_SOURCE（CHIME 3,661；repeater=Yes 94 / No 3,567）
- chime_dm_subset.csv：3,584 行（94 repeater + 3,490 non-repeater）
- DM：repeater mean 445.50 / median 409.74；non-repeater mean 686.44 / median 584.90
- Mann-Whitney U：p = 1.32×10⁻¹⁰（两尾）；方向：repeater 更低
- 论文对照：暴级 μ₁=464.83 vs μ₀=684.75（p=4.10×10⁻⁹）→ 源级与暴级方向、量级、显著性一致
- 结论：论文「repeaters DM 显著更低」声称在冻结源级数据上 supported

> 边界提示：论文 Table 1 为暴级（593 暴）统计；本包为源级（3,584 源）快照（2026-08-13 vs 论文 2025-04-05）。F_d/w_p/f_p/f_lu 在 Blinkverse 源级转储中缺失，无法在冻结包内重算 Table 1 其余特征；agent 正确说明该边界即可，不判负。
