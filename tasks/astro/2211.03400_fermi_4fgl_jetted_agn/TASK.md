# 科研任务：验证 Fermi 4FGL 伽马射线源中喷流 AGN 人口组成的分类论断（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2211.03400_fermi_4fgl_jetted_agn`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Foschini L. et al., "A New Sample of Gamma-Ray Emitting Jetted Active Galactic Nuclei", Universe 8, 587 (2022)，arXiv:2211.03400
- 领域：astro / 高能天体物理 / 费米伽马射线源分类

## 问题（可证伪）

论文核心论断（Abstract）：基于 Fermi-LAT 第四期源表（4FGL），选取 **|b| > 10°**、有河外或未分类对应体（排除星暴/正常星系与银河系源）的伽马射线点源，得到最终样本 **2,980 个**；其中 **BL Lac 占 40%、FSRQ 占 23%、misaligned AGN 占 2.8%、NLS1+Sy+LINER 占 1.9%、changing-look AGN 占 1.1%，约 30% 的源仍无明确分类或完全没有分类**。

请基于冻结的 4FGL-DR1 目录（CDS VizieR J/ApJS/247/33，与论文所用的 4FGL-DR2 同系列、仅小版本差异）回答：

1. **数据规模**：按 `ReadMe` 的 byte-by-byte 说明解析 `4fgl.dat`（gzip 解压，4104 字节定宽/行，无表头），报告总行数与唯一 `Source_Name` 数；对照 ReadMe 的 Records=5065 与摘要的 "5064 sources above 4σ"。
2. **全空天分类分布**：用 `CLASS1` 列（表 7 分类码，注意大小写区分：小写=likely 关联、大写=identified）统计各类计数（bcu/bll/fsrq/PSR/unk/spp/...），并统计 **CLASS1 为空（无对应体）的源数**；对照论文数据源 4FGL 摘要的 **1,336 个无对应体源**。
3. **论文口径样本重建**：|b|>10° 且 CLASS1 非空，排除银河系类（PSR/psr、spp、SNR/snr、PWN/pwn、glc、gal、sbg、SFR/sfr、hmb、lmb 等）后，报告样本大小与组成（bcu / bll+BLL / fsrq+FSRQ / rdg+RDG / nlsy1+NLSY1 / agn+AGN 等）。
4. **人口占比**：计算上述重建样本中 BLL 类、FSRQ 类、bcu（模糊 blazar 候选）、合计无明确分类（bcu + 未含在样本内的无对应体源）占比，与论文的 40% / 23% / ~30% 对比；同时报告 |b|>10° 全部 3,646 源中无对应体（CLASS1 空）的比例。
5. **结论**：用四档标签判定「BLL 主导（~40%）+ FSRQ ~23% + ~30% 无明确分类」论断在冻结数据口径下为 `supported` / `partially_supported` / `contradicted` / `inconclusive`，并说明「无明确分类」定义的敏感度（bcu 是否计入）。

## 数据说明

- 冻结包物理位置：`$PAPER_BENCH_DATA_DIR`（来源 / 许可 / 逐文件 SHA-256 见 `data/SOURCE.md`、`data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 主数据（2 个真实文件，Fermi 4FGL-DR1 官方发布目录）：
  - `4fgl.dat.gz`（6,883,415 B）：CDS VizieR **J/ApJS/247/33** 的 4FGL 点源目录；gzip 解压后 5,065 行 × 4,104 字节定宽（ReadMe Records=5065）。关键列（1-based 字节区间，权威定义见包内 `ReadMe`）：
    - 1–28 `Source_Name`（如 `4FGL J0001.3+4741`）
    - 38–47 `GLON`、49–58 `GLAT`（银经/银纬，度）
    - 3978–3982 `CLASS1`（表 7 分类码：`bcu` blazar 候选不确定型 / `bll` / `fsrq` 小写=likely，`BLL` / `FSRQ` 大写=identified，`PSR` 脉冲星等）
    - 3984–3986 `CLASS2`（次级分类码）
    - 3988–4015 `ASSOC1`（关联源名）
  - `ReadMe`（70,259 B）：VizieR 官方字节级列说明 + Table 7 分类码定义，解析依据。
- 原始来源：CDS VizieR `J/ApJS/247/33`（Abdollahi+ 2020, ApJS 247, 33），`https://cdsarc.cds.unistra.fr/ftp/J/ApJS/247/33/`。
- 版本说明：论文（2022-11）基于 **4FGL-DR2**（5,064 源）与 4LAC；本包冻结 **4FGL-DR1**（5,065 行，2016-08 数据）为最接近的官方稳定目录。两版人口差异小（论文重建样本 2,980 vs 冻结目录 2,866，~4%），差异本身是任务讨论点之一，**禁止直接抄论文数字作为实测结果**。
- 许可：Fermi-LAT 目录公开数据；CDS/VizieR 开放目录数据，无注册门槛。
- 规模：~6.9 MB（gzip，解压 ~20 MB），单机 pandas/纯 Python 即可处理。

## 方向提示

1. **解析方式**：固定宽度（byte slice）解析，严禁按分隔符切列；`ReadMe` 的 Byte-by-byte 表是唯一权威。
2. **大小写敏感**：`CLASS1` 区分大小写（`bll`=likely BL Lac，`BLL`=identified BL Lac；`bcu`、`bll`、`fsrq` 均为小写码）。统计「BLL 类」应合并 `bll`+`BLL`。
3. **筛选口径**：论文「jetted AGN 或未分类 + 低频对应体」在目录层的可操作近似 = `|GLAT| > 10` 且 `CLASS1` 非空，再剔除银河系分类码（PSR/psr、spp、SNR/snr、PWN/pwn、glc、gal、sbg、SFR/sfr、hmb、lmb、unk 酌情处理——`unk` 未在 4FGL-DR1 的 |b|>10 河外筛选中出现，若出现需说明处理）。
4. **版本与口径差异**：冻结目录重建样本 2,866（编译器实测）vs 论文 2,980；bcu 占比 37.4% vs 论文「~30% 无明确分类」（论文做了文献重分类，把部分 bcu 分入其他类）。如实报告并归因，禁止抄论文数字。
5. **对照原则**：论文数值只能用于对照讨论，禁止作为「实测结果」。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）、关键数字、与论文 Abstract 人口占比的逐项对比及差异归因。
2. **`code/`**：完整可复现脚本（固定随机种子），从冻结数据读取并完成解析、统计、筛选重建、交叉验证。
3. **`results/evidence_table.csv`**：至少含全空天 CLASS1 计数表、|b|>10° 筛选重建组成表（列如 `class, n_all_sky, n_absb_gt10, n_in_agn_sample, frac_in_sample`）。
4. **`results/metrics.json`**：总行数、唯一源数、无对应体计数（全空天/|b|>10°）、重建样本大小与组成、人口占比、论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（定宽解析 / 大小写 / 筛选口径 / DR1 vs DR2 版本差异 / 定义敏感度）。

## 数据铁律提醒

- 只使用本包冻结的真实数据；禁止模拟 / 合成数据。
- 禁止手工抄写论文数字作为「实测结果」；所有指标必须运行代码得到。
- 论文数值只能用于对照讨论。
- 提交的计数必须能从冻结数据 + 代码重算得到一致结果。
