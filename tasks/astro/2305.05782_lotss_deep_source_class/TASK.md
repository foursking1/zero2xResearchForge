# 科研任务：验证 LoTSS Deep DR1 射电源分类人口统计（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2305.05782_lotss_deep_source_class`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Best P.N. et al., "The LOFAR Two-metre Sky Survey: Deep Fields Data Release 1. V. Survey description, source classifications and host galaxy properties", MNRAS (2021/2023)，arXiv:2305.05782
- 领域：astro / 河外射电天文学 / 射电源分类（LOFAR 深场）

## 问题（可证伪）

论文核心论断（Abstract/§7/Table 2）：LoTSS-Deep DR1 对约 **80,000 个射电源**（三个深场 ELAIS-N1、Lockman Hole、Boötes 共 **81,951** 个）进行多波段 SED 拟合与 AGN/恒星形成分类，划分为**星暴/恒星形成星系（SFG）、射电宁静 AGN（RQAGN）、射电高声激 AGN（HERG）、射电低声激 AGN（LERG）与未分类**五类；**94.7% 的源可可靠分类**（未分类 5.3%）；**SFG 占 67.9%**（ELAIS-N1 中超过 70%）、**RQAGN 占 9.1%**、LERG+HERG 合计约 17.7%；在低流量端 SFG 占主导（ELAIS-N1 极限流量处 >90%，S_150MHz≈1–1.5 mJy 处 SFG 与射电 AGN 主导地位切换）。

请基于官方发布的分类目录（LOFAR Surveys 网站 DR1 数据发布）回答：

1. **目录规模**：解析三个场的 `*_classifications_dr1.fits`（ELAIS-N1 / Lockman / Boötes），报告各场行数与总源数；对照 Table 2 的 31,610 / 31,162 / 19,179 / 81,951。
2. **逐类计数**：用 `Overall_class` 列统计每场五类（SFG/RQAGN/LERG/HERG/Unc）计数，逐场对照论文 Table 2，并给出总计与百分比。
3. **可靠分类率**：验证「94.7% 可靠分类（5.3% 未分类）」；验证「SFG 67.9%、RQAGN 9.1%、LERG 15.6%、HERG 2.1%」。
4. **低流量主导**：在 ELAIS-N1 用 `S_150MHz`（Jy）分箱，报告 SFG 占比随流量密度的单调变化；定位 SFG 占比降至 50% 的「开关点」流量（应 ~1–1.5 mJy）；讨论与论文「极限流量处 SFG 主导」的一致性（注意完整性修正等口径差异）。
5. **结论**：用四档标签判定「LoTSS-Deep DR1 射电源以 SFG 为主（~2/3）、94.7% 可分类、低流量端 SFG 主导」论断在冻结数据口径下为 `supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 冻结包物理位置：`$PAPER_BENCH_DATA_DIR`（来源 / 许可 / 逐文件 SHA-256 见 `data/SOURCE.md`、`data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 主数据（9 个真实文件，论文官方数据发布；FITS 二进制表）：
  - 每场主表（列见 README）：`en1_classifications_dr1.fits`（31,610 行）、`lockman_classifications_dr1.fits`（31,162 行）、`bootes_classifications_dr1.fits`（19,179 行）
    - 关键列：`Source_name`、`S_150MHz`（Jy）、`z_best`、`AGN_final`（0/1/−1）、`Mass_cons`、`SFR_cons`、`Radio_excess`（dex）、`RadioAGN_final`（0/1/−1）、`Overall_class`（SFG/RQAGN/LERG/HERG/Unc）
  - 每场扩展表 `*_classifications_extended_dr1.fits`（含更多中间分类输出，可交叉验证）
  - 每场 README `*_classifications_README.txt`（列定义与分类规则）
- 原始来源：LOFAR Surveys 官网 `https://lofar-surveys.org/deepfields.html`（DR1 数据发布，`public/deepfields/data_release/{en1,lockman,bootes}/`）。
- 分类规则（README）：`AGN_final=0 & RadioAGN_final=0` → SFG；`1 & 0` → RQAGN；`0 & 1` → LERG；`1 & 1` → HERG；任一为 −1 → Unc。
- 许可：LoTSS Deep Fields DR1 公开数据发布（LOFAR Surveys，CC 学术使用，无注册）。
- 规模：~24 MB（F 盘），fitsio/pandas 即可处理。

## 方向提示

1. **解析方式**：FITS 二进制表（可用 `fitsio` 或 `astropy.io.fits`）；`Overall_class` 是最终分类列。
2. **口径**：论文 Table 2 的每场总数 31,610/31,162/19,179 与目录行数**完全一致**（编译器 2026-08-13 实测逐类一致）；百分比 67.9/9.1/15.6/2.1/5.3 由总计 81,951 计算。
3. **低流量端**：`S_150MHz` 单位 Jy；ELAIS-N1 中 S<100 μJy 的 SFG 占比约 84%（编译器实测；论文「>90% 极限流量处」含完整性修正，口径差异需讨论）；SFG 占比随流量单调下降，50% 交叉点 ~1 mJy。
4. **对照原则**：论文数值只能用于对照讨论，禁止作为「实测结果」；Table 2 是精确可复现锚，其余为方向性论断。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）、关键数字、与论文 Table 2 的逐场逐类对比及差异归因。
2. **`code/`**：完整可复现脚本（固定随机种子），从冻结数据读取并完成解析、统计、分箱。
3. **`results/evidence_table.csv`**：至少含逐类计数表（列：`field, class, n` + 汇总行）与流量分箱表（列：`field, flux_bin_uJy, n, n_sfg, frac_sfg`）。
4. **`results/metrics.json`**：三场行数、逐类计数与百分比、可靠分类率、ELAIS-N1 流量分箱与开关点、论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（FITS 解析 / 完整性修正口径 / 流量单位）。

## 数据铁律提醒

- 只使用本包冻结的真实数据；禁止模拟 / 合成数据。
- 禁止手工抄写论文数字作为「实测结果」；所有指标必须运行代码得到。
- 论文数值只能用于对照讨论。
- 提交的计数必须能从冻结数据 + 代码重算得到一致结果。
