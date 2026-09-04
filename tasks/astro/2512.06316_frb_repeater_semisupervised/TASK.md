# 科研任务：验证 FRB 重复暴与色散量 DM 的显著差异及判别性声称（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2512.06316_frb_repeater_semisupervised`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Mankatwit N., Thongkonsing P., Loekkesee S., Chainakun P., Luangtip W., Sanpa-arsa S., "Revealing Hidden Repeaters in the CHIME/FRB Catalog: Semi-Supervised Insights into the Fast Radio Burst Population", 2025, arXiv:2512.06316（MNRAS 545, 2178, 2026）
- 领域：astro / 高能天体物理 / 快速射电暴（FRB）人口统计

## 问题（可证伪）

论文核心论断（Abstract/§2/Table 1）：**基于 Blinkverse 数据库的 CHIME 样本（593 个暴：137 个来自已知重复源的暴 + 456 个非重复暴），repeaters 与 non-repeaters 在色散量 DM（D_snr）上存在统计显著差异——repeaters 的 DM 更低（Table 1：μ₀=684.75 vs μ₁=464.83 pc cm⁻³，Mann-Whitney U p=4.10×10⁻⁹）；且 DM 是半监督分类中最重要的判别特征（Abstract/Fig 5）**。

请基于冻结的 Blinkverse CHIME 样本（源级，含 repeater 标签与 DM）回答：

1. **样本规模**：报告 `chime_dm_subset.csv` 的总行数、已知 repeater（`repeater=1`）与 non-repeater（`repeater=0`）的数量；对照论文 §2 的「593 暴（137 重复暴来自 42 源 + 456 非重复暴）」并说明源级与暴级的口径差异。
2. **DM 方向声称**：分别计算两类源的 DM 均值与中位数；验证「repeaters 的 DM 更低」是否成立（均值与中位数均比较）。
3. **显著性声称**：用 Mann-Whitney U 检验（`scipy.stats.mannwhitneyu`）比较两类 DM，报告 p 值；对照论文阈值 p<0.01（Table 1 五特征中 4 个显著）与论文 p=4.10×10⁻⁹；冻结源级数据 p 值应同样极小（<1e-5 量级）。
4. **特征重要性（可选加分）**：用冻结数据中的可用特征（`dm_pc_cm3`、`dm_ne2001`、`dm_ymw16`、`mjd`、`gl_deg`、`gb_deg`）训练一个简单分类器（如随机森林/逻辑回归），报告特征重要性排序，验证 DM 是否为最重要判别特征（论文 Abstract/Fig 5）。
5. **结论**：用四档标签判定「repeaters 与 non-repeaters 的 DM 存在显著差异且重复暴 DM 更低（DM 为关键判别特征）」论断在冻结数据口径下为 `supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 冻结包物理位置：`$PAPER_BENCH_DATA_DIR`（来源 / 许可 / 逐文件 SHA-256 见 `data/SOURCE.md`、`data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 主数据（2 个真实文件，Blinkverse 公开数据库 + 编译器派生子集）：
  - `blinkverse_all_sources.json`（2,559,111 B）：**Blinkverse 数据库原始 API 转储**（2026-08-13 抓取，4,020 条 `FRB_SOURCE` 记录）。每条记录 `content` 含：`source`（FRB 名）、`telescope`（CHIME/ASKAP/…）、`ra`/`dec`（hms/dms 与 `ra_degree`/`dec_degree`）、`dm`（色散量 pc·cm⁻³）、`dm_ne2001`/`dm_ymw16`、`mjd`、`gl`/`gb`、`repeater`（`Yes`/`No`，已知重复源标签）、`reference` 等。**这是论文 §2 的原始数据源（论文访问日期 2025-04-05，本包为 2026-08-13 快照）。**
  - `chime_dm_subset.csv`（300,968 B，3,584 行）：编译器按论文 §2 口径（telescope=CHIME 且 DM 非空）导出的源级子集。列：`source`、`ra_deg`、`dec_deg`、`dm_pc_cm3`、`dm_ne2001`、`dm_ymw16`、`mjd`、`gl_deg`、`gb_deg`、`repeater`（0/1）。**任务统计请以此表为准；如需原始 JSON 做审计请用 `blinkverse_all_sources.json`。**
- 原始来源：Blinkverse 数据库（https://blinkverse.zero2x.org/），公开 FRB 观测参数数据库，聚合 CHIME/FRB、ASKAP、FAST、GBT、Arecibo 等望远镜观测。
- 版本说明：论文 Table 1 是**暴级**（593 暴）统计；本包冻结的是**源级**（3,584 个 CHIME 源）快照——均值/中位数的具体数值会有小幅差异，但方向与显著性应一致；agent 须如实讨论该口径差异，不得把论文 μ 值抄作源级实测。
- 许可：Blinkverse 为开放科研数据库（无注册门槛）；CHIME/FRB 目录经 CANFAR 永久归档（CISTI.CANFAR/21.0007、23.0004、25.0066）公开。
- 规模：~2.9 MB，纯 Python + scipy 秒级。

## 方向提示

1. 用 `pandas.read_csv` 读 `chime_dm_subset.csv`；`repeater` 列 0/1。
2. Mann-Whitney U：`scipy.stats.mannwhitneyu(rep_dm, nonrep_dm, alternative="two-sided")`；报告 U 与 p。
3. 均值/中位数都要报告；论文 Table 1 用均值（μ₀/μ₁），源级数据同样给出均值与中位数。
4. 注意：论文的 593 暴 = 137 重复暴（来自 42 个重复源）+ 456 非重复暴；本包为 3,584 个 CHIME 源（94 个已知重复源 + 3,490 非重复）。两口径的差异（每源单条 vs 每暴一条）是讨论重点。
5. 可选特征重要性：随机森林 `feature_importances_` 或逻辑回归系数；`dm_pc_cm3` 应排第一或前二。
6. 所有统计必须由提交代码从冻结数据重算；论文数值只能用于对照。

## 输出要求

- `results/evidence_table.csv`：关键证据表（如按类汇总：`class, n, dm_mean, dm_median, dm_q1, dm_q3` + 样本级行）。
- `results/metrics.json`：上述 1–5 问的数值结论（样本规模、两类 DM 均值/中位数、Mann-Whitney p、特征重要性（若做）、四档结论）。
- `code/`：可运行的解析/统计代码（Python），读取 `$PAPER_BENCH_DATA_DIR` 下的冻结数据。
- `REPORT.md`：方法（口径定义、检验选择）、结果表、与论文 Table 1 / §2 的对照与差异归因、四档结论与局限。

## 数据铁律提醒

- 禁止使用模拟/合成数据；禁止把论文数值直接抄作「实测」。
- 提交的统计必须能从冻结数据 + 代码重算得到一致结果。
