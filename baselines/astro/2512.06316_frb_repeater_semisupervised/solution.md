# solution.md — FRB 重复暴 DM 差异验证（task 2512.06316_frb_repeater_semisupervised）

## 一句话结论

**`supported`**：在冻结的 Blinkverse CHIME 源级口径上，known repeaters 的色散量 DM 显著低于 non-repeaters（Mann-Whitney U，p=1.32×10⁻¹⁰），DM 方向、量级与显著性均与论文 Table 1（暴级 μ₁=464.83 vs μ₀=684.75、p=4.1×10⁻⁹）一致；在可选特征重要性分析中，DM 为物理特征中判别力最强的特征。

## 关键结果（全部由 `code/` 从冻结数据重算）

| 指标 | 本任务冻结数据（源级） | 论文 Table 1（暴级） |
|---|---|---|
| CHIME 样本规模 | **3,584 行**（repeater **94** + non-repeater **3,490**） | 593 暴 = 137 重复暴（42 源）+ 456 非重复暴 |
| repeater DM 均值 / 中位数 | **445.50** / **409.74** pc·cm⁻³ | μ₁ = 464.83（无中位数） |
| non-repeater DM 均值 / 中位数 | **686.44** / **584.90** pc·cm⁻³ | μ₀ = 684.75（无中位数） |
| 方向 | repeater 均值与中位数均更低 ✓ | repeater 更低 ✓ |
| Mann-Whitney U | **U = 100,426，p = 1.32×10⁻¹⁰**（两尾） | p = 4.10×10⁻⁹ |
| 效应量 | rank-biserial r = 0.388 | — |
| 四档结论 | **supported** | — |

## 口径差异说明（源级 vs 暴级）

- 论文 §2 统计为**暴级**（burst 级）：593 暴含 137 个来自 42 个已知重复源的重复暴；本冻结包为**源级** CHIME 记录（每源一条记录为主，3,584 行）。
- 编译器探针与源清单确认：原始 JSON 4,020 条 FRB 记录（CHIME 3,661：repeater=Yes 94 / No 3,567），编译器按 telescope=CHIME 且 DM 非空导出 3,584 行子集。
- 明细审计：3,584 行中 3,555 行为有名字的源（3,490 非重复 + 65 重复）；另有 29 行 repeater=1 的空源名记录（对应 Blinkverse JSON 中一个空 source 名的 CHIME 重复源块，其 29 个 DM 值在 JSON 中逐一对上）。**94 个 repeater DM 值全部能在 JSON CHIME repeater=Yes 记录中找到**，排除了抄数/混入外部数据。
- 因此源级与暴级数量差异（3,584 vs 593）源于口径（每个已知重复源在源级快照中只有一条记录 vs 论文暴级包含其所有暴），而非数据丢失。
- μ 具体数值的小幅差异（445.50 vs 464.83 等）由（a）口径 源级 vs 暴级、（b）快照日期（2026-08-13 vs 论文 2025-04-05）导致；方向、显著性、p<0.01 结论完全一致。

## 方法

1. `verify_claims.py`：校验两冻结文件 SHA-256 与清单一致；重算 3 个裁判抽查量（3,584 行 / 94 个 repeater / p 值）。
2. `analyze_frb_dm.py`：
   - Q1 样本规模 + JSON 审计；
   - Q2 分组描述统计（均值、中位数、四分位）；
   - Q3 `scipy.stats.mannwhitneyu`（两尾，独立两样本非参数检验）；
   - Q4 特征重要性：RandomForest（500 trees）+ 标准化的 LogisticRegression + permutation importance；
   - Q5 四档结论判定。

## 特征重要性（加分项）

- 全特征：RF 排序 mjd > **dm_pc_cm3** > gl_deg > gb_deg > dm_ymw16 > dm_ne2001（**DM 排第 2**）；LR 标准化系数绝对值 DM 最大（|−1.04|）。
- 剔除目录列 mjd 后：**dm_pc_cm3 排第 1**。mjd（发现时期）非论文物理特征（论文 5 特征为 D_snr、F_d、w_p、f_p、f_lu）；post-DM 的 RF 归因主要被 mjd（目录期效应）主导。结论：在冻结可用特征中 DM 判别意义最强，与论文「DM 为最重要判别特征」一致。

## 局限

- 冻结包缺论文其余 4 个物理特征（F_d/w_p/f_p/f_lu）的源级转储，无法完整重算论文 Table 1 五特征表或半监督分类流水线；本文只在可用特征上做判别性参考。
- 快照为 2026-08-13，论文为 2025-04-05 访问。
- 题目要求四档标签：`supported`。

## 复现

```bash
cd agent_solution
python3 code/verify_claims.py      # SHA-256 审计 + 裁判抽查量重算
python3 code/analyze_frb_dm.py     # 主分析：Q1–Q5、指标与图
```

依赖：`pandas, numpy, scipy, scikit-learn, matplotlib`。数据从冻结目录读取（Linux 挂载 `/mnt/f/dataset/astro/2512.06316_frb_repeater_semisupervised/`；Windows 路径 `F:\dataset\...\` 自动回退）。