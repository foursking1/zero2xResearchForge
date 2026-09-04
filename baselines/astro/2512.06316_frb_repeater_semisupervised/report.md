# REPORT — 验证 FRB 重复暴与色散量 DM 的显著差异及判别性声称

- **task_id**：`2512.06316_frb_repeater_semisupervised`（L1 critical claim）
- **论文**：Mankatwit N., Thongkonsing P., Loekkesee S., Chainakun P., Luangtip W., Sanpa-arsa S., *Revealing Hidden Repeaters in the CHIME/FRB Catalog: Semi-Supervised Insights into the Fast Radio Burst Population*, arXiv:2512.06316（MNRAS 545, 2178, 2026）
- **被验证声称**：Blinkverse CHIME 样本中 repeaters 的 DM 显著低于 non-repeaters（Table 1：μ₁=464.83 vs μ₀=684.75，Mann-Whitney U p=4.10×10⁻⁹）；DM 为最重要判别特征（Abstract / Fig 5）。

---

## 1. 数据与口径

### 1.1 冻结数据

| 文件 | 说明 | SHA-256 |
|---|---|---|
| `chime_dm_subset.csv` | 编译器按论文 §2 口径（CHIME 且 DM 非空）导出的源级子集，3,584 行 × 10 列 | `be77ddda…f4a7`（与清单一致，`verify_claims.py` 复检） |
| `blinkverse_all_sources.json` | Blinkverse API 原始转储，4,020 条 FRB_SOURCE 记录 | `3302a12f…124e`（与清单一致） |

表列：`source, ra_deg, dec_deg, dm_pc_cm3, dm_ne2001, dm_ymw16, mjd, gl_deg, gb_deg, repeater`。`repeater` 为 0/1 已知重复源标签（来自 Blinkverse `repeater` 字段）。

### 1.2 口径定义

- **源级**：每 FRB 源一条记录（本冻结包口径）。已知重复源仍为一行，取其代表 DM。
- **暴级**：每暴一条（论文 Table 1 口径——已知重复源含多暴）。

两口径的换算不改变 DM 差异的物理结论，但样本量完全不同（3584 源 vs 593 暴），**μ 数值不可直接混用**（见 §3 对照）。

## 2. 方法与实现

| 步骤 | 实现 |
|---|---|
| 完整性审计 | `code/verify_claims.py`——SHA-256 对照 `source_manifest.json` + 3 个裁判抽查量重算 |
| 样本规模 | `pandas` 计数 + 与原始 JSON 交叉审计（4,020 / CHIME 3,661 / repeater=Yes 94） |
| 描述统计 | 分组 `mean / median / std / q1/q3 / min / max / IQR` |
| 显著性检验 | `scipy.stats.mannwhitneyu`（两尾、独立两样本、非参数）；另算 rank-biserial 效应量 |
| 特征重要性（加分） | RandomForest(500 trees)、标准化 LogisticRegression、permutation importance（RF，10 次重排）；5 折 CV-AUC |

检验选择：DM 分布典型地高度右偏（见 `figures/dm_hist_by_class.png`）、双样本方差不齐，故不用 t 检验，采用 Mann-Whitney U——与论文一致；显著性阈值 p<0.01（论文 Table 1 口径）。

## 3. 结果

### 3.1 样本规模（问题 1）

- `chime_dm_subset.csv` **总行数 3,584**
- **repeater = 94**；**non-repeater = 3,490**
- 原始 JSON：4,020 条总数；CHIME 3,661（repeater=Yes 94，No 3,567）
- 论文对照：593 暴 = 137 重复暴（42 个已知重复源）+ 456 非重复暴

**源级 vs 暴级差异**：论文 137 重复暴由 42 个重复源产生，即暴级去重后仅 42 源；本快照含 94 行 CHIME repeater=1 记录 = **65 个具名重复源 + 1 个无源名重复源块（29 条记录）**。具名重复源数（65）远大于论文的 42，主因是快照日期（2026-08-13 比论文 2025-04-05 新）与 Blinkverse 聚合程度；数量差异来自口径与快照日期，不是伪造。审计确认 29 行空源名记录对应 JSON 中该无源名 CHIME 重复源的 29 条记录，且 **94 个 repeater DM 值全部能在 JSON 的 CHIME repeater=Yes 记录中按 DM 精确匹配**。

### 3.2 DM 方向（问题 2）

| 统计量 | repeater (n=94) | non-repeater (n=3,490) |
|---|---|---|
| mean | **445.50** | **686.44** |
| median | **409.74** | **584.90** |
| q1 | 293.66 | 384.02 |
| q3 | 552.61 | 866.47 |
| std | 252.28 | 420.49 |
| min / max | 87.82 / 1703.48 | 102.65 / 3966.73 |

**均值与中位数均显示 repeater 更低** → 方向声称成立。

### 3.3 显著性（问题 3）

- Mann-Whitney U（两尾）**U = 100,426**，**p = 1.32×10⁻¹⁰**
- 效应量：rank-biserial r ≈ 0.388（中效应）
- **p << 1e-5**，更 < 0.01（论文阈值）；与论文暴级 p=4.10×10⁻⁹ 同量级、同方向。

### 3.4 特征重要性（问题 4，加分项）

- 全特征 RF 排序：`mjd > dm_pc_cm3 > gl_deg > gb_deg > dm_ymw16 > dm_ne2001` → **DM 排第 2**。
- 标准化 LR：绝对值系数最大者为 `dm_pc_cm3`（−1.04，负号 = 重复暴 DM 更低）→ **DM 排第 1**。
- 置换重要性：`mjd > dm_pc_cm3 > …`（DM 排第 2）。
- 剔除非物理目录列 `mjd` 后：**`dm_pc_cm3` 排第 1**（RF 与置换重要性）。
- 5 折 CV AUC：RF 0.754、LR 0.820。

结论：冻结可用特征中 DM 的判别意义最强（RF 中仅次于目录期列 mjd；LR 与剔除 mjd 后均第一）。满足论文「DM 为最重要判别特征」的方向性表述；`mjd` 非论文物理特征，仅作完整性报告。（论文其余特征 w_p / f_p / f_lu 未冻结入源级转储，无法完整重算其 Fig 5 SHAP。）

### 3.5 结论（问题 5）

**四档标签：`supported`**

支撑点：
1. 方向成立（均值与中位数均 repeater 更低）；
2. 显著性成立（p=1.32×10⁻¹⁰ << 1e-5 << 0.01）；
3. 与论文数值逐项对照一致（μ₁ 445.50 vs 464.83；μ₀ 686.44 vs 684.75；p-量级 1e-10 vs 1e-9）；
4. 源级/暴级口径差异如实说明。

## 4. 与论文对照与差异归因

| 项 | 论文（暴级 593） | 本工作（源级 3,584） | 差异归因 |
|---|---|---|---|
| repeater 均值 DM | 464.83 | 445.50 | 暴级 vs 源级平均（参数重复暴的 DM 分布不同）；快照日期 |
| non-repeater 均值 DM | 684.75 | 686.44 | 同上（几乎一致） |
| Mann-Whitney p | 4.10×10⁻⁹ | 1.32×10⁻¹⁰ | 样本量/口径，均「显著，p<0.01」 |
| 方向 | repeater 更低 | repeater 更低 | **一致** |
| 样本数 | 593 暴（137+456） | 3,584 源（94+3,490） | 暴级含重复暴多次计数；快照日期 |

未混用：论文 μ 数值仅用于对照表，实测值全部由代码重算出。

## 5. 局限与边界

- **无法在冻结包内完整复现论文半监督流水线**：论文 5 特征（D_snr、F_d、w_p、f_p、f_lu）中仅 DM（D_snr 对应的源级色散量）与部分辅助列在源级转储中可用；w_p/f_p/f_lu 缺失 → 不做超论文范围的实验，特征重要性仅作参考性加分。
- **158/168 候选重复源等 Table 4 内容**（A3 锚）不在本包可验证范围。
- 快照日期 2026-08-13（论文访问 2025-04-05），CHIME 目录后续更新会小幅改变源计数与 μ。
- 29 行空源名重复记录已在审计中交代，不进入源列表去重。
- 目录期列 `mjd` RF 高重要性不代表物理可解释判别力，已在 §3.4 说明。

## 6. 复现与文件清单

**运行**（从冻结数据重算全部数值）：
```bash
cd agent_solution
python3 code/verify_claims.py   # SHA-256 审计 + 裁判抽查量（3584/94/p）
python3 code/analyze_frb_dm.py  # 主分析 Q1–Q5：统计、特征重要性、图形
```

依赖：pandas / numpy / scipy / scikit-learn / matplotlib（纯 CPU，秒级）。

| 产物 | 路径 |
|---|---|
| 主分析代码 | `code/analyze_frb_dm.py` |
| 审计/重算代码 | `code/verify_claims.py` |
| 关键证据表（类别汇总 + 样本行） | `results/evidence_table.csv` |
| 数值结论 JSON | `results/metrics.json` |
| 裁判抽查验证 JSON | `results/verification.json` |
| 全量源级明细 | `evidence/all_sources_dm.csv` |
| 类别汇总 | `evidence/class_summary.csv` |
| 图形 | `figures/dm_box_by_class.png`、`figures/dm_hist_by_class.png` |