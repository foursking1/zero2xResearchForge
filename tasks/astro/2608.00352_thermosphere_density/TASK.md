# TASK: AETHER-P3 热层密度预测——三档地磁活动的 Min Dst 锚与 Gannon 风暴主相（critical claim 验证）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- 任务 ID：`2608.00352_thermosphere_density`
- 层级：L1（critical claim）
- 领域：astro（空间天气 / 热层密度 / 轨道力学）
- 裁判：LLM judge（论文锚 + 证据抽查），判分标准见 `SCORE_RUBRIC.md`（私有）

---

## 1. 科学声称（可证伪）

目标论文（arXiv:2608.00352，AETHER-P3 全球热层密度预测模型，Space Weather 在投）报告了 8 个**独立卫星测试案例**的评测框架（论文 Table 3），用于评估模型在地磁活动三档（安静 / 中等 / 极端）下的预测技能与不确定性可靠性。该框架声称：

> **C1**：安静档测试（2024-05-24 ~ 2024-05-31，SWARM-A/C）窗口内最小 Dst = **−27 nT**；
> **C2**：中等档测试（2015-02-01 ~ 2015-02-28，SWARM-A/C）窗口内最小 Dst = **−69 nT**；
> **C3**：极端档测试（2024-05-10 ~ 2024-05-13，GRACE-FO / SWARM-A / SWARM-B / SWARM-C，May 2024 Gannon 风暴）窗口内最小 Dst = **−406 nT**；
> **C4**：极端案例主相定义为 **2024-05-10 15:00 → 2024-05-13 00:00**（论文 Table 5），且窗口内最小 Dst 时刻落在主相内。

**失败条件**：任一窗口的逐小时最小 Dst 与上述锚显著不符（超出地磁指数版本/舍入可解释的范围），或极端窗口最小 Dst 时刻不在主相定义内。

## 2. 方向提示

- 数据为**逐小时 Dst 地磁指数（nT）**，来自论文随附发布；测试窗口以 UTC 日期为准（含首尾日）。
- 逐小时最小 Dst = 窗口内全部小时值的最小值。建议同时报告每窗口小时数（应为 24×天数）以核对窗口完整性。
- 注意：表 3 的 Min Dst 是"窗口内最小 Dst"。若与逐小时最小值有 1–2 nT 的差异，属指数版本/舍入的常见现象，应**如实报告并归因**，而不是强行改数或直接抄论文数字。
- 建议额外做三件事：(a) 数据完整性核查（时间跨度、每小时一个点、无缺口）；(b) 三档分类自洽性（安静档窗口最小 Dst > −50、中等档 ≈ −50~−100、极端档 < −300 的幅值分层是否与标签一致）；(c) 极端窗口最小 Dst 出现时刻与主相（C4）的包含关系判定。

## 3. Input（冻结真实数据）

`data/` 内为论文随附发布的**真实地磁指数数据**（Zenodo 10.5281/zenodo.20412490 软件发布的 `Datafiles/DST.mat`；底层为 WDC Kyoto 逐小时 Dst 指数）。详见 `data/SOURCE.md`（来源、许可、逐文件 SHA-256、派生说明）。

### 3.1 文件清单

| 文件 | 内容 |
|---|---|
| `data/DST.mat` | 原始 MATLAB 文件（论文原样发布），219,168 行 × 8 列 |
| `data/dst_hourly.csv` | 由 `DST.mat` 确定性派生（见 `derive_dst_csv.py`）：逐小时 `datetime_utc` + `dst_nt` |
| `data/derive_dst_csv.py` | 派生脚本（冻结随包，用于审计与复算） |

### 3.2 Schema（`dst_hourly.csv`）

| 列 | 含义 |
|---|---|
| `datetime_utc` | UTC 时刻，格式 `YYYY-MM-DD HH:MM:SS`，逐小时 |
| `dst_nt` | 逐小时 Dst 指数（nT），整数 |

`DST.mat` 列为 `[year, month, day, hour, minute, second, day_of_year, dst]`（已验证，如 2000-02-01 00:00 行 day_of_year=32）。

---

## 4. Output（输出要求）

在作答工作目录产出可复现分析包：

- `claim.md`：被检验的声称（C1–C4）+ **结论标签**（四档之一：`supported` / `partially_supported` / `contradicted` / `inconclusive`）+ 一句话结论。
- `code/`：完整可运行代码（Python/R），**所有数字必须从 `data/` 冻结数据重算**，不得手工抄写。
- `results/evidence_table.csv`：逐窗口证据表，至少含列：`window, condition, period_start, period_end, n_hours, min_dst, min_dst_time, paper_table3, abs_diff, main_phase_ok, category_ok`（每窗口一行）。
- `results/metrics.json`：总体指标（每窗口 `min_dst`/`n_hours`/`min_dst_time`；数据完整性核查结果；结论标签；分类自洽结论）。
- `results/figure.svg`（或 png/pdf）：至少一张关键图（如 Dst 时序图标注三个测试窗口与最小 Dst 时刻，或窗口内 Dst 分布对比）。
- `report.md`：方法、结果、结论、边界（≤2 页）。

### 需回答的问题

1. **数据完整性**：数据时间跨度？是否每小时一个点、无缺口（总行数 = 24 × 天数）？
2. **三个窗口的最小 Dst**：W1（2024-05-24~31）、W2（2015-02-01~28）、W3（2024-05-10~13）的逐小时最小 Dst 与出现时刻各是多少？与声称的 −27 / −69 / −406 相差多少？
3. **主相验证**：W3 最小 Dst 时刻是否落在 2024-05-10 15:00 → 2024-05-13 00:00（C4）内？
4. **分类自洽**：窗口内 Dst 幅值是否支持"安静 / 中等 / 极端"三档标签？
5. **结论**：C1–C4 整体结论标签是什么？差异如何归因？

## 5. 数据铁律提醒

- **只用 `data/` 内冻结的真实数据**；禁止模拟/合成数据；禁止把文献/README 里的数值当作自己从数据算出的结果（一切数字必须由你的代码从冻结数据产出）。
- 所有报告数字必须能从冻结数据 + 你的代码重算；裁判会抽查 1–2 个关键数并运行你的代码复核（防抄数）。
- 遵守 `data/SOURCE.md` 记录的许可（MIT / WDC Kyoto 引用要求）；数据文件 SHA-256 固定（见 `data/SOURCE.md`），不得改动。
- 本任务只验证论文的**测试框架（Dst 锚）声称**；卫星密度数据与模型预测不在本卡数据面内，不要在报告中声称验证了模型预测技能。