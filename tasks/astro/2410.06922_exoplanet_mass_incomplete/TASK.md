# TASK: 不完备系外行星数据的 ML 质量插补——L1 critical claim

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- 任务 ID：`2410.06922_exoplanet_mass_incomplete`
- 层级：L1（critical claim；卡标 L2 → 按新映射造 L1 题）
- 领域：astro（系外行星统计 / 缺失数据插补）
- 裁判：LLM judge（论文锚 + 证据抽查），见 `SCORE_RUBRIC.md`（私有）

## 1. Input（输入：冻结真实数据）

数据包位于 `data/`，为**真实公开数据**（NASA Exoplanet Archive PSCompPars 官方 TAP 快照），详见 `data/SOURCE.md`（来源、许可、SHA-256）。

### 1.1 `data/pscomppars_2026-08-13.csv`（6,336 颗行星，2026-08-13 快照）

| 列 | 含义（论文属性） |
|---|---|
| `pl_rade` / `pl_masse` | 行星半径（R⊕）/ 质量（M⊕） |
| `pl_orbper` / `pl_orbeccen` | 轨道周期（天）/ 离心率 |
| `pl_eqt` / `st_mass` / `st_met` | 平衡温度（K）/ 恒星质量（M☉）/ 恒星金属丰度（dex） |
| `sy_pnum` | 系统内已知行星数 |
| `discoverymethod` / `disc_year` / `ra` / `dec` | 发现方法 / 年份 / 坐标（辅助列） |

> 论文用 2023-02-02 快照（5,251 颗）；本包为 2026-08-13 快照（6,336 颗），质量缺失率 61.7% vs 论文 72.8%——**快照差异是数据事实，必须在报告中显式说明**。

## 2. Output（输出要求）

在你的工作目录下产出以下提交物：

- `claim.md`：你检验的**可证伪科学声称**（一句话）+ 失败条件 + 结论标签（`supported`/`partially_supported`/`contradicted`/`inconclusive`）。
- `code/`：完整可运行的分析代码（Python/R 均可），**所有指标必须从 `data/` 冻结数据重算**，不得手工抄写任何数字。
- `results/evidence_table.csv`：逐算法逐数据集证据表（至少含：数据集、算法、测试行星数、ϵ=RMS(ln(m_obs/m_imp))、150 测试子集 ϵ）。
- `results/metrics.json`：总体指标（各算法排名、完整 vs 全档案 vs 扩展对比、GAIN 差距等）。
- `results/figure.svg`（或 png/pdf）：至少一张关键图（如观测 vs 插补质量散点图，或算法误差对比条图）。
- `report.md`：方法、结果、结论、边界（≤2 页）。

### 科学目标（Scientific goal）

端到端评估目标论文（不提供全文）的核心结果在冻结数据上的可复现性：

> **核心论断**：五种能利用多维不完备数据集的 ML 算法（kNN-Imputer、MissForest、GAIN、MICE、kNN×KDE）中：利用全部行星发现（含缺失值）的插补优于仅用完整子集（550 颗、六属性）；加入更多属性（8 属性）带来小幅提升；kNN×KDE 综合最优（还能输出概率分布），GAIN 一贯最差。

论文关键数值（完整数据集六属性、凌星测试 150 颗，Fig 3）：误差 ϵ=RMS(ln(m_obs/m_imp))：mBM(TLG2020)=0.980、kNN-Imputer=0.876、MissForest=0.885、GAIN=1.253、MICE=0.968、kNN×KDE=0.886（5 个新算法中 4 个优于 mBM；最优 ~0.88 ≈ 2.4×）。全档案六属性（1,426 颗测试，Fig 7）：kNN×KDE=1.510（150 子集 0.846）、kNN-Imputer=1.628（1.258）、MissForest=1.701（0.835）、GAIN=2.552（1.942）、MICE=1.728（0.918）、PS-CP=2.566（3.094）；加入全档案后 150 测试子集误差对 kNN×KDE/MissForest/MICE 改善、对 kNN-Imputer/GAIN 变差。扩展八属性（Fig 11）：ϵ=1.502（150 子集 0.840），vs 六属性 1.510/0.846——小幅提升。

请基于冻结数据回答：

1. **算法对比（完整属性子集）**：从冻结快照构造"六属性完整子集"（半径、质量、周期、平衡温度、恒星质量、行星数都齐全的行星），按论文协议（150 颗测试、隐藏质量、五算法 + 必要基线）计算各算法 ϵ。排名模式（GAIN 最差、kNN×KDE/MissForest/kNN-Imputer 最优、4/5 优于 mBM）是否保持？
2. **不完备数据收益**：用全部 6,336 颗（含缺失）重做插补。对可与完整子集测试对齐的行星，加入全档案是否改善误差？各算法的收益/损害方向是否与论文一致（kNN×KDE/MissForest/MICE 改善，kNN-Imputer/GAIN 变差）？
3. **属性增加**：加入恒星金属丰度与轨道离心率（8 属性），kNN×KDE 的整体 ϵ 是否 ≤ 六属性结果（论文 1.502 vs 1.510）？
4. **概率分布价值**：kNN×KDE 对若干行星（如热木星 vs 罕见/低观测数行星）输出的质量分布形状（单峰/双峰、宽度）能否指示置信度？给出 2–3 个定性示例。
5. **结论**：给出四档结论标签与适用边界（快照差异、缺失机制、与测量偏差的混淆）。

提示（不给方法步骤）：论文代码开源（`https://github.com/DeltaFloflo/exoplanet_imputation`），可作参考实现或直接运行（须从冻结数据重算指标，不得抄论文数字）；ϵ 定义 = RMS(ln(m_obs/m_imp))；注意质量最小质量（RV）与真实质量的差别（论文按 TLG2020 协议处理）；缺失率随快照变化是数据事实。

## 3. 数据铁律提醒

- **只用 `data/` 内冻结的真实数据**；禁止模拟/合成数据；禁止把论文/README 里报告的数值当作自己从数据算出的结果。
- 所有报告数字必须能从冻结数据 + 你的代码重算；裁判会抽查 1-2 个关键数并运行你的代码复核。
- 遵守 `data/SOURCE.md` 记录的许可（NASA Exoplanet Archive 公开条款）；数据文件 SHA-256 固定，不得改动。
- 快照差异（2026-08-13 vs 论文 2023-02-02）是**数据事实**，须在报告中显式说明，不得隐藏或"修正"。