# 科研任务：验证 Radio Galaxy Zoo DR1 公民科学分类目录的规模、共识阈值与多分量占比声称（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2412.14502_radio_galaxy_zoo_dr1`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Wong O.I. et al., "Radio Galaxy Zoo Data Release 1: 100,185 radio source classifications from the FIRST and ATLAS surveys", 2024, arXiv:2412.14502（MNRAS，Released 2024-07-01）
- 领域：astro / 射电天体物理 / 星系射电形态与宿主星系交叉认证

## 问题（可证伪）

论文核心论断（Abstract/§1/§5）：**Radio Galaxy Zoo（RGZ）数据发布 1（DR1）由公民科学家的加权共识分类构成，总计 100,185 条分类（99,602 条 FIRST 目录条目 + 583 条 ATLAS），对应 99,146 个唯一 FIRST 射电源与 583 个 ATLAS 射电源；所有被收录分类的 consensus level ≥ 0.65，平均 reliability 为 0.83；在 99,146 个 FIRST 源中，16,354 个（~16.5%）由多于一个射电分量组成（multicomponent）**。

请基于冻结的官方 DR1 目录（Zenodo 10.5281/zenodo.10656393，4 个 CSV）回答：

1. **规模声称**：解析 4 个 CSV，报告 `DR1_FIRST_radio_classifications.csv` 与 `DR1_ATLAS_radio_classifications.csv` 的行数、`RGZID` 唯一源数、总计分类数（99,602 + 583 = 100,185）；检查 FIRST 中重复出现的 `RGZID`（同一源多条分类）数量。
2. **共识阈值声称**：`CL`（consensus level）列是否全部 ≥ 0.65？报告 min / Q1 / median / mean 与 `CL<1` 占比；对照论文「consensus ≥ 0.65 才收录」（§3.3/§5.4）与「平均 reliability 0.83」（Abstract）——注意 reliability 由专家子集标定，说明其是否可从本包直接重算。
3. **多分量占比**：分别用两个口径统计 FIRST 多分量源数量：(a) 行级 `N_comp > 1`；(b) 唯一 `RGZID` 级 `N_comp > 1`；另报告唯一源级 `N_peaks > 1` 数量。对照论文 §5.1 的 **16,354**，判断哪个口径最接近，并归因差异（目录版本 / 口径定义）。
4. **ATLAS 子样本**：报告 ATLAS 分类表 583 行的多分量（`N_comp>1`）数量与 `CL` 分布。
5. **结论**：用四档标签判定「DR1 目录为高质量、高共识的公民科学分类目录（规模 100,185 / 唯一源 99,146+583 / consensus ≥ 0.65 / ~16.5% 多分量）」论断在冻结数据口径下为 `supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 冻结包物理位置：`$PAPER_BENCH_DATA_DIR`（来源 / 许可 / 逐文件 SHA-256 见 `data/SOURCE.md`、`data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 主数据（4 个真实文件，Zenodo 官方发布，CC-BY-4.0）：
  - `DR1_FIRST_radio_classifications.csv`（10,180,988 B，99,602 行）：FIRST 源分类。关键列：`CatID`、`RGZID`（唯一源标识）、`ZooniverseID`、`RA`/`Dec`、`N_votes`（参与投票用户数）、`N_total`、`CL`（加权 consensus，0–1）、`N_comp`（组成射电源的射电分量数）、`N_peaks`（亮度峰数）、`LAE`/`TSA`/`OL`/`TF`/`TF_err`/`DC`（形态量，定义见论文 §3 与附录）。
  - `DR1_FIRST_host_properties.csv`（12,293,965 B，99,602 行）：FIRST 源对应的 WISE 宿主星系。关键列：`#CatID`、`RGZID`、`ZooniverseID`、`Host_RA`/`Host_Dec`、`WISEID`、`W1`–`W4`（星等/误差/信噪比）、`N^WISE_MATCH`、`DWM`、`z_phot0`。
  - `DR1_ATLAS_radio_classifications.csv`（58,806 B，583 行）：ATLAS 源分类（列同上，SWIRE 口径）。
  - `DR1_ATLAS_host_properties.csv`（78,068 B，583 行）：ATLAS 源 SWIRE/IRAC 宿主星系（`IRAC_3.6um` 等、`z_sp`、`z_ph`）。
- 原始来源：Zenodo record **10.5281/zenodo.10656393**（"Radio Galaxy Zoo Data Release 1"，Wong+ 2024，CC-BY-4.0；文件 `RGZ_DR1_tables.tar.gz`，7,577,955 B，官方 md5 `6e6c681075528dfbbcba9e0cf9f56941`）。
- 版本说明：论文正文数字（99,146 唯一 FIRST 源 / 16,354 多分量）来自论文所用发布版本；本包冻结的 Zenodo v1 目录实测：唯一源 99,146（一致）、行级 `N_comp>1` 16,531 / 唯一源级 16,334（与论文 16,354 存在 ~0.1–1% 版本差，需如实归因）。
- 许可：Zenodo 开放数据（CC-BY-4.0），无注册门槛；纯 CSV，单机 pandas 秒级可解析。

## 方向提示

1. 用 `pandas.read_csv` 直接读 4 个 CSV（UTF-8）；`RGZID` 去重用 `drop_duplicates(subset="RGZID")`。
2. `CL` 列即 consensus level；论文阈值 0.65；先验证 min，再给分布。
3. `N_comp` 是每个源的分量数；多分量 = `N_comp > 1`。行级与唯一源级口径都要报告；`N_peaks > 1` 是另一个（更宽松的）口径。
4. 论文「平均 reliability 0.83」由专家子集标定（§3.3.1），CSV 中无该列，无法直接重算——正确做法是说明其不可从本包重算，并聚焦 consensus 分布与规模/占比声称。
5. 所有统计都必须由提交代码从冻结 CSV 重算；论文数值只能用于对照。

## 输出要求

- `results/evidence_table.csv`：关键证据表（如逐源 `rgzid, ra, dec, n_comp, n_peaks, cl` + 分项汇总行）。
- `results/metrics.json`：上述 1–5 问的数值结论（行数、唯一源数、CL 分布、多分量两口径、ATLAS 统计、四档结论）。
- `code/`：可运行的解析/统计代码（Python），读取 `$PAPER_BENCH_DATA_DIR` 下的冻结 CSV。
- `REPORT.md`：方法（口径定义）、结果表、与论文数值的逐项对照与差异归因、四档结论与局限。

## 数据铁律提醒

- 禁止使用模拟/合成数据；禁止把论文数值直接抄作「实测」。
- 提交的计数必须能从冻结数据 + 代码重算得到一致结果。
