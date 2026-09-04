# 科研任务：验证 ExoMiner 对 TESS 候选行星的评分行为与低 MES 保守性论断（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2111.10009_exominer_tess_vetting`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Valizadegan H. et al., "ExoMiner: A Highly Accurate and Explainable Deep Learning Classifier that Validates 301 New Exoplanets", ApJ 926, 120 (2022)，arXiv:2111.10009
- 领域：astro / 系外行星 / 凌星候选验证（TESS）

## 问题（可证伪）

论文核心论断（Abstract/§9/§10/Table 16）：ExoMiner 在固定 **precision=99%** 时对 Kepler 测试集的 **recall=0.936**（最佳旧分类器仅 0.763）；迁移到 TESS 的 ExoMiner-Basic 在 **407 个 TOI** 上 **precision=0.88 / recall=0.73**；在 **低 MES（<10.5）区域更保守**——Kepler 未标记 KOI 中 MES<10.5 的 **943 个里仅 20 个（2.1%）** 获得 score>0.99，而 301 个新验证行星均满足 score>0.99 且 MES>10.5，半径 0.6–9.5 R⊕、周期 0.5–280 d。

请基于官方 ExoMiner 仓库发布的 TESS SPOC vetting 目录（11,289 个 TCE，含 ExoMiner Score）回答：

1. **分数分布**：报告 ExoMiner Score 的最小/中位/最大值；score≥0.5（PC 判定阈值）与 score>0.99（验证阈值）的 TCE 数量与占比；是否与「ExoMiner 高分高度集中在少数强信号 TCE」一致。
2. **低 MES 保守性**：MES<10.5 与 MES≥10.5 两组中 score>0.99 的占比；按 MES 分箱（0–5 / 5–10 / 10–15 / 15–20 / 20–30 / ≥30）报告 score>0.99 占比是否单调上升；对照论文「Kepler 943 个低 MES KOI 中仅 20 个（2.1%）>0.99」的保守性论断。
3. **高分候选人口**：score>0.99 且 MES>10.5 的候选数量；报告其行星半径与轨道周期分布（中位数、最小、最大）；对照论文 301 颗新验证行星的半径 0.6–9.5 R⊕ / 周期 0.5–280 d 范围，讨论 TESS 与 Kepler 样本窗口差异。
4. **分数与信号强度**：计算 ExoMiner Score 与 MES、Transit Model SNR 的秩相关（Spearman），判断「分数随信号强度增强」的单调性方向与强度。
5. **结论**：用四档标签判定「ExoMiner 评分对 TESS 候选具有高判别力、在低 MES 区域保守」的论断在冻结目录口径下为 `supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 冻结包物理位置：`$PAPER_BENCH_DATA_DIR`（来源 / 许可 / 逐文件 SHA-256 见 `data/SOURCE.md`、`data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 主数据（1 个真实文件，论文官方 GitHub 仓库发布的数据产品）：
  - `exominer_vetting_tess.csv`（2,811,413 B，11,289 行含表头，16 列）：NASA `nasa/ExoMiner` 官方仓库 `exominer_vetting_pc_catalog_dash-render-web-app/data/` 的 TESS SPOC 2-min 凌星候选 vetting 表（文件名 `exominer_vetting_tess-spoc-2-min-s1s67_dashtable_dvm-url_scoregt0.1.csv`）。覆盖 TESS Sectors 1–67 的 SPOC TCE，**ExoMiner Score > 0.1** 筛选（web 展示表口径）。关键列：
    - `TCE ID`（如 `390651552-1-S23`）、`TIC ID`、`Sector Run`（如 `1-65`、`14-60`）
    - `ExoMiner Score`（0–1 分类分数）、`ExoMiner Unc. Score`
    - `Orbital Period [day]`、`Transit Duration [hour]`、`Transit Depth [ppm]`、`Planet Radius [Earth Radii]`、`MES`（多事件统计量）、`Transit Model SNR`、`Number of transits observed`、`Gaia RUWE`
- 原始来源：https://github.com/nasa/ExoMiner （`exominer_vetting_pc_catalog_dash-render-web-app/data/`，raw URL 见 `data/SOURCE.md`）。
- 版本说明：论文（2021-11）的 TESS 实验基于 TOI 目录（Sectors 1–30，1,167 个 SPOC TOI）；本冻结目录为仓库后续发布的 S1–S67 TESS SPOC 2-min TCE 全量评分（score>0.1 子集），是论文方法与评分模型的官方延伸数据产品。论文的 precision/recall 需 TFOPWG 金标（本包不含），故任务聚焦**评分分布与人口行为**这些直接可检验的论断。
- 许可：NASA ExoMiner 项目公开仓库（GitHub），TESS 数据公开；无注册门槛。
- 规模：~2.8 MB，pandas 即可处理。

## 方向提示

1. **保守性口径**：论文 §9「943 个 MES<10.5 未标记 KOI 中 20 个 >0.99（2.1%）」是 Kepler 口径；本目录是 TESS 口径，两处占比应同数量级（<3%），方向必须一致，数值差异要归因（任务集/阈值/样本窗口差异）。
2. **验证阈值**：论文把 score>0.99 且 MES>10.5 作为新行星验证标准（§9）；本目录可直接数出该子集规模。
3. **窗口差异**：TESS 单/多扇区运行限制最长可测周期（本目录高分候选周期上限 ~125 d vs 论文 Kepler 280 d），这是讨论点不是错误。
4. **对照原则**：论文数值只能用于对照讨论，禁止作为「实测结果」。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）、关键数字、与论文 Abstract/§9/§10 论断的逐项对比及差异归因。
2. **`code/`**：完整可复现脚本（固定随机种子），从冻结数据读取并完成解析、统计、分箱、秩相关。
3. **`results/evidence_table.csv`**：至少含 MES 分箱表（列：`mes_bin, n_tce, n_score_gt099, frac_score_gt099`）与分数分布统计行。
4. **`results/metrics.json`**：总行数、分数分布、≥0.5 / >0.99 计数与占比、低 MES 保守性两口径、高分候选人口（计数+半径/周期分布）、Spearman 相关、论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（score>0.1 子集 / TESS vs Kepler 口径 / 无金标故不重算 precision-recall）。

## 数据铁律提醒

- 只使用本包冻结的真实数据；禁止模拟 / 合成数据。
- 禁止手工抄写论文数字作为「实测结果」；所有指标必须运行代码得到。
- 论文数值只能用于对照讨论。
- 提交的计数必须能从冻结数据 + 代码重算得到一致结果。
