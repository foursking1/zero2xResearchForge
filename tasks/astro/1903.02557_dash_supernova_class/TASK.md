# TASK: DASH 超新星光谱自动分类——关键主张验证（L1）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

## 0. 任务类型与层级

- 层级：**L1（关键主张验证，critical claim）**
- 总分 100（评分规则见私有 `SCORE_RUBRIC.md`：A 核心结果达成度 60 / B 证据真实性 25 / C 方法与报告 15）
- 本 TASK.md 为公开部分；目标论文全文不提供，仅给出主张与出处。

## 1. 待验证的关键主张（claim）

论文 **Muthukrishna et al. 2019, arXiv:1903.02557（MNRAS），"DASH: Deep Learning for the Automated Spectral Classification of Supernovae and their Hosts"** 主张：

> 不经模板匹配的深度卷积网络 DASH（Deep Automated Supernova and Host classifier），在 212 条真实 OzDES 光纤光谱（2015–2017 年 ATel 发布）上自动分类，**93%（197/212）与 ATel 分类一致**（Table 1：Ia 127/129、Ia? 34/43、II 25/28、II? 7/9、Ibc 1/1、Ibc? 2/2），且**全部 212 条在 20 秒内自主完成分类**，无需人工目视检查（论文 §5.2）。

你的任务：仅使用本任务冻结的真实数据（官方发布的 DASH 模型 v06 + 官方仓库随附的 OzDES 真实光谱与 ATel 标签），复跑 DASH 分类，量化匹配率与耗时，判断该主张在冻结子集上是否成立，并与论文锚数值（Table 1/Table 2）对比。

## 2. 数据说明

### 2.1 数据组成（`data/`，全部文件清单/大小/SHA-256 见 `data/MANIFEST.tsv`）

| 路径 | 内容 | 规模 |
|---|---|---|
| `data/OzDES_data/` | 69 条真实 OzDES/DES 超新星光谱（ATel run 24–28 共 5 个目录）+ `all_atels.txt` 标签表 | 71 文件，约 26 MB |
| `data/training_set/` | 642 个 SNID 格式真实训练光谱（`.lnw`/`.dat`，CfA+Berkeley SN Ia 程序，论文 §2.1 数据来源） | 642 文件，约 66 MB |
| `data/models_v06.zip` | 官方发布 DASH 模型（Zenodo 记录 7760927，含 4 个 TF1 checkpoint 模型 + host 模板） | 218,267,769 字节 |
| `data/MANIFEST.tsv` | 全部 715 文件的 `path | size_bytes | sha256` | — |

### 2.2 Schema

- `.dat` 光谱：3 列 ASCII（波长 Å、流量、流量误差），每文件约 5000 行，log 波长等间隔采样；为 DES 巡天组合光谱（文件名含 `combined_..._v10_b00`）。
- `all_atels.txt`：管道分隔（`|`）9 列：`Name | RA (J2000) | Dec (J2000) | Discovery Date (UT) | Discovery Mag (r) | Spectrum Date (UT) | Redshift | Type | Phase | Notes`；`Type` 可能带 `?`（不确定）。
- `models_v06.zip`：解压后 `models_v06/models/{zeroZ, agnosticZ, zeroZ_classifyHost, agnosticZ_classifyHost}/tensorflow_model.ckpt.{meta,index,data-00000-of-00001}` 及 `sn_and_host_templates.npz`。旧版 TensorFlow checkpoint（`tf.Session` 风格），需 TF1.x 兼容环境（如 `tensorflow==1.15` + Python 3.7，或按 `astrodash_env.yml`）。

### 2.3 来源与许可

- OzDES 光谱与标签、训练光谱：官方 astrodash GitHub 仓库 `daniel-muthukrishna/astrodash`（`templates/OzDES_data/`、`templates/training_set/`），仓库 **MIT License**（Copyright 2017 Daniel Muthukrishna）。底层为 OzDES/DES 巡天真实观测光谱，作者在论文 §5.2 用作评测数据并随软件分发；下载时间 2026-08-13。
- 模型：Zenodo 记录 7760927（astrodash trained models，`models_v06.zip`），随官方软件分发。
- 复核：所有文件 SHA-256 已固定于 `MANIFEST.tsv`，不得改动。

### 2.4 冻结子集与论文评测集（212 条）的差异（必须在报告中说明）

- 论文全集覆盖 2015–2017 全部 OzDES ATel（212 条）；冻结子集为官方仓库随附的 run 24–28（69 条光谱，67 个唯一天体；`DES16C3bq`、`DES16E1dcx` 各含 2 个历元）。
- 冻结子集标签分布：Ia 47、SNIa? 9、II 9、SNII? 2、Ibc 2。
- 模型版本：论文发表（2019）时模型与当前官方 v06 可能存在细微差异；本任务以官方 v06 为准。

## 3. 实验要求

### 3.1 运行 DASH

- 安装：`pip install astrodash`（或从官方 GitHub 安装）；将 `data/models_v06.zip` 解压到 astrodash 包内模型目录（包导入时会按 `download_data_files` 逻辑自动从 Zenodo 拉取；离线时应使用冻结的 zip 放置到 `astrodash/models_v06/`）。
- 对全部 69 条冻结光谱运行 `astrodash.Classify(filenames, knownRedshifts, knownZ=True, smooth=6)`（红移取 `all_atels.txt` 对应值），取 top-1 类型。
- 环境注明：TF1 兼容环境（见 2.2）；记录所用 `astrodash` 版本、TF 版本、机器。

### 3.2 匹配口径（与论文 Table 1 一致，必须明确写出）

1. 将 DASH 预测子类型归并到大类：**Ia** = {Ia-norm, Ia-91T, Ia-91bg, Ia-csm, Ia-02cx, Ia-pec}；**II** = {IIP, IIL, IIn}；**Ibc** = {Ib-norm, Ibn, IIb, Ib-pec, Ic-norm, Ic-broad, Ic-pec}。
2. ATel 标签同样归并；带 `?` 的标签视为该大类不确定，仍归入该大类。
3. **匹配** = 预测大类 == 标签大类。`Ic-broad` 预测按论文口径（§5.2：视为宿主污染而非真实 Ic-broad）单列报告，不计入匹配。
4. 逐条给出 69 条的结果表（对象名/历元/红移/ATel 标签/DASH top-1 类型/软标签概率/Reliable 标志/是否匹配）。

### 3.3 必报指标（`results/metrics.json` 等）

- 冻结子集总体匹配率（论文口径）及分型（Ia / Ia? / II / II? / Ibc / Ibc?）匹配率；
- 与论文 Table 1 类型级比率的绝对差；
- 与论文 Table 2 逐对象 DASH 记录的同大类复现一致率（冻结对象中能对上的占比）；
- 全 69 条单批次自动分类墙钟耗时（自主运行、无人工干预）；
- 结论判定：主张在冻结子集上「成立 / 不成立 / 部分成立」+ 依据（含子集差异、模型版本差异的讨论）。

### 3.4 提交物（对齐 v3 规范）

`submission/run.sh`、`analysis_plan.md`、`results/{metrics,evidence_table,critical_checks,uncertainty}.json`、`figures/`、`report.md`、`provenance/`。

## 4. 数据铁律（必须遵守）

- 只用 `data/` 冻结的真实数据；**禁止模拟/合成光谱**。
- 不得修改冻结文件；以 `MANIFEST.tsv` 的 SHA-256 为准核验。
- 不得引入外部光谱集冒充冻结数据（如需补充分析，须显式声明为附加实验且不参与主张判定）。
- 模型必须使用官方 v06；不得用自行训练的模型替换（重训仅可作为附加实验并显式声明）。
