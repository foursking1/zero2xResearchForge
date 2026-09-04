# TASK: ExoNet TESS 候选判别——KOI 判别力与 TESS 迁移计数能否复现？（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- 任务 ID：`2604.15560_exonet`
- 层级：L1（critical claim；卡标 L2 → 按新映射造 L1 题）
- 领域：astro（系外行星，TESS/Kepler 候选判别）
- 裁判：LLM judge（论文锚 + 证据抽查），见 `SCORE_RUBRIC.md`（私有）

## 1. Input（输入：冻结真实数据）

数据包位于 `data/`，全部为**真实公开数据**（NASA Exoplanet Archive 官方目录 2026-08 快照 + 论文作者发布的候选目录），详见 `data/SOURCE.md`（来源、许可、逐文件 SHA-256）。

### 1.1 `data/koi_cumulative.csv`（9,564 行，Kepler 目标兴趣体 KOI 目录）

NASA Exoplanet Archive `CUMULATIVE` 表子集（官方 TAP 查询冻结）。列：

| 列 | 含义 |
|---|---|
| `kepid` / `kepoi_name` | Kepler ID / KOI 信号名（**按 kepoi_name 去重，一信号一行**） |
| `koi_disposition` | `CONFIRMED` / `FALSE POSITIVE` / `CANDIDATE`（论文训练口径：CONFIRMED=1，FALSE POSITIVE=0，CANDIDATE 剔除） |
| `koi_period` / `koi_depth` / `koi_duration` / `koi_ror` / `koi_srad` | 轨道周期/凌星深度/时长/行星-恒星半径比/恒星半径 |
| `koi_teq` / `koi_steff` / `koi_slogg` / `koi_smet` / `koi_kepmag` | 平衡温度 / 恒星有效温度 / 表面重力 / 金属丰度 / 开普勒星等 |

### 1.2 `data/tess_toi_pc.csv`（4,927 行，TESS PC 候选目录）

NASA Exoplanet Archive `toi` 表子集（`tfopwg_disp='PC'`，即 SPOC 管线已通过的 Planet Candidate）。列：`tid,toi,tfopwg_disp,pl_orbper,pl_trandurh,pl_rade,st_teff,st_logg,st_tmag,ra,dec`。

### 1.3 `data/exonet_candidates.csv`（1,754 行，论文发布的高置信候选目录）

论文作者随论文发布的排名目录（CC-BY-4.0）。列：`toi,tic_id,planet_prob,period_days,radius_earth,eq_temp_K,host_teff_K,has_tess_fits,confidence,habitable_zone`。

> 注：本包**不含光变曲线**（论文用了 MAST 相位折叠光变；MAST 全量下载 GB 级、本任务不提供）。`data/` 只有目录级特征。

## 2. Output（输出要求）

在你的工作目录下产出以下提交物：

- `claim.md`：你检验的**可证伪科学声称**（一句话）+ 失败条件 + 结论标签（`supported`/`partially_supported`/`contradicted`/`inconclusive`）。
- `code/`：完整可运行的分析代码（Python/R 均可），**所有指标必须从 `data/` 冻结数据重算**，不得手工抄写任何数字。
- `results/evidence_table.csv`：逐行/逐模型证据表（至少含：数据集、n、正负类数、AUC、accuracy、阈值；或目录核验的逐项计数）。
- `results/metrics.json`：总体指标（含 KOI 判别器的 AUC/accuracy、混淆矩阵、TESS 迁移高置信计数及其与发布目录的差异、任何重采样区间）。
- `results/figure.svg`（或 png/pdf）：至少一张关键图（如 ROC 曲线，或 KOI→TESS 域概率分布对比，或校准图）。
- `report.md`：方法、结果、结论、边界（≤2 页）。

### 科学目标（Scientific goal）

端到端评估目标论文（不提供）的核心结果在冻结数据上的可复现性：

> **核心论断**：多模态模型 ExoNet 在 KOI 二分类上达到 test AUC=0.9549、accuracy=86.3%；迁移到 4,720 个未见 TESS PC 候选后，产出 1,754 个 ≥70% 高置信信号（其中 1,098 个 ≥85%；52 个处于 200–400K 宜居带；6 个半径 <1.6R⊕ 的岩石宜居带候选），并经温度缩放（T*=1.573）输出校准概率。

请基于冻结数据回答：

1. **判别力**：仅用 KOI **目录特征**（无光变）训练二分类器（CONFIRMED vs FALSE POSITIVE，剔除 CANDIDATE，按 `kepoi_name` 去重）的 AUC 与 accuracy 是多少？与论文的 0.9549 / 86.3% 差多少？多模态光变信息的缺失如何影响结论？
2. **跨域迁移**：将你的分类器应用于冻结的 TESS PC 候选（未见集），按 ≥70% / ≥85% 概率阈值各筛出多少候选？与论文发布目录（`exonet_candidates.csv` 即 ≥70% 集）的计数差异多大？域差距（Kepler→TESS）如何体现？
3. **口径核验**：论文发布目录的计数（1,754 个 ≥70%、1,098 个 ≥85%、52 个 HZ=200–400K、6 个 rocky<1.6R⊕）能否从该目录**独立重算一致**？与 `tess_toi_pc.csv` 中 `pl_rade`/`st_teff` 交叉核验（注意目录间值可能因快照/来源不同而有差异）？
4. **校准**：论文报告温度缩放 T*=1.573。从发布目录的概率分布与置信度档位（confidence 列），概率校准在何意义上可检验？给出你的校准代理分析（如概率直方图、阈值-命中率关系），并说明哪些校准声明在本数据上不可检验。
5. **结论**：给出四档结论标签与适用边界（特征口径、快照时间、未含光变/模型权重的内容）。

提示（不给方法步骤）：标签口径决定一切（CONFIRMED vs FP、CANDIDATE 剔除、按信号去重）；AUC 对类别不平衡稳健，accuracy 不稳健，两者都报；迁移评估要防"目录即答案"——你自己的分类器输出与论文发布概率不同源，计数对比是**差异分析**而非查表；HZ 与半径阈值严格按论文定义（200–400K、<1.6 R⊕）。

## 3. 数据铁律提醒

- **只用 `data/` 内冻结的真实数据**；禁止模拟/合成数据；禁止把论文/README 里报告的数值当作自己从数据算出的结果。
- 所有报告数字必须能从冻结数据 + 你的代码重算；裁判会抽查 1-2 个关键数并运行你的代码复核。
- 遵守 `data/SOURCE.md` 记录的许可（CC-BY-4.0 / NASA 数据条款）；数据文件 SHA-256 固定，不得改动。
- 目录快照时间（2026-08）与论文撰写期（2026-04）的差异是**数据事实**，须在报告中显式说明，不得隐藏或"修正"。