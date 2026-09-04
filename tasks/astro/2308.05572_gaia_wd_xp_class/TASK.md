# 科研任务：验证 Gaia 白矮星 XP 光谱大规模分类的人口组成断言（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2308.05572_gaia_wd_xp_class`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Vincent D. et al., "Classification and parameterisation of a large Gaia sample of white dwarfs using XP spectra", A&A 682, A5 (2024)，arXiv:2308.05572
- 领域：astro / 恒星天体物理 / 白矮星光谱分类

## 问题（可证伪）

论文核心论断：基于 Gaia DR3 XP 光谱的机器学习分类，将 **100,886 个高置信白矮星候选**（PWD>0.9、G<20.5）分为六类（DA/DB/DC/DO/DQ/DZ）；在置信阈值 0.65 下得到 **89,188 个 high-confidence 分类、11,698 个 uncertain**；各类数量（Table 2）为 **DA 77,330 / DB 5,688 / DC 4,082 / DO 215 / DQ 601 / DZ 1,272**，**DA 占绝对主导**。论文同时声称分类概率与最可能光谱类型已随 VizieR 目录 **J/A+A/682/A5** 发布。

请基于冻结数据回答（数据规模 → 分类组成 → 物理参数完整性 → 论断判定）：

1. **数据规模**：解析 `catalog.dat`（定宽 338 字节/行，无表头），报告总行数与唯一 GaiaDR3 源数；验证是否等于论文 §3.2 的 100,886。
2. **最可能类型计数**：用 `SpType` 列（`:` 后缀 = uncertain 标注）统计六类数量；并用六列概率 `PDA..PDZ` 的 argmax 交叉验证；逐类对比论文 Table 2。
3. **high-confidence 判定**：用「SpType 无冒号」规则统计每类与总数；用「max(P) ≥ 0.65」规则重复统计；对比论文 89,188 / 11,698；解释两种规则的差异来源（目录概率为两位小数舍入，而冒号标注基于未舍入概率判定）。
4. **物理参数完整性**：统计 `Teff = -999`（谱拟合未收敛/无效）数量；统计 DA 中 `Teff > 300,000 K` 的极端热星数量；对比论文 §4.2 的 1,080 与 34，讨论发布版本漂移。
5. **结论**：用四档标签判定「DA 主导 + 89,188 high-confidence」论断在冻结数据口径下为 `supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 冻结包物理位置：`$PAPER_BENCH_DATA_DIR`（来源 / 许可 / 逐文件 SHA-256 见 `data/SOURCE.md`、`data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 主数据（2 个真实文件，论文引用的官方发布目录）：
  - `catalog.dat.gz`（11,292,494 B）：CDS VizieR **J/A+A/682/A5** 的 Gaia WD DR3 XP-classification catalogue；gzip 解压后 100,886 行 × 338 字节定宽。关键列（1-based 字节区间，权威定义见包内 `ReadMe`）：
    - 1–19 `GaiaDR3`（唯一 Gaia DR3 源标识）
    - 21–23 `SpType`（最可能光谱类型；分类概率 < 0.65 时带 `:` 后缀标注 uncertain，如 `DA:`）
    - 25–67 SDSS 合成 ugriz 星等（`-999` = 不可用）
    - 69–182 五波段通量误差
    - 184–212 `PDA PDB PDC PDO PDQ PDZ`（六类分类概率，0–1，两位小数）
    - 214–283 `Teff / logg / M` 及误差（`-999` = 拟合无效）、`umagcor` u 带校正
    - 285–338 模型大气成分 `comp`、`logCHe`、`logL` 及误差
  - `ReadMe`（7,986 B）：VizieR 官方 byte-by-byte 列说明，解析依据。
- 原始来源：CDS VizieR `J/A+A/682/A5`（Vincent+ 2024），`https://cdsarc.cds.unistra.fr/ftp/J/A+A/682/A5/`。
- 许可：CDS/VizieR 开放目录数据（学术用途，无注册门槛）。
- 规模：~11 MB（gzip，解压 ~35 MB），单机 pandas/纯 Python 即可处理。

## 方向提示

1. **解析方式**：固定宽度（byte slice）解析，严禁按分隔符切列；`ReadMe` 的 Byte-by-byte 表是唯一权威。
2. **uncertain 规则**：`SpType` 带 `:` 即论文的 uncertain 标注（§3.2）；目录中「无冒号」总数 = 89,188、「带冒号」总数 = 11,698，与论文完全一致——这是最可靠的判定口径。
3. **概率列**：两位小数舍入，`PDA..PDZ` 之和不一定严格等于 1；阈值判定请以 `SpType` 标注为准，`max(P) ≥ 0.65` 只是近似。
4. **版本漂移**：论文 §4.2 的「1,080 未收敛 / 34 个 Teff>300,000 K 的 DA」与发布目录（实测约 1,396 / 68）存在漂移；如实报告并归因（发布版重跑、筛选差异），禁止直接抄论文数字。
5. **对照原则**：论文数值只能用于对照讨论，禁止作为「实测结果」。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）、关键数字、与论文 Table 2 的逐类对比及差异归因。
2. **`code/`**：完整可复现脚本（固定随机种子），从冻结数据读取并完成解析、统计、交叉验证。
3. **`results/evidence_table.csv`**：至少含逐类计数表（列：`class, n_high_conf, n_uncertain, n_argmax, frac_high_conf`）与数据规模统计行。
4. **`results/metrics.json`**：数据规模统计、逐类计数、high-confidence 总数与占比、`Teff=-999` 计数、DA `Teff>300,000 K` 计数、论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（定宽解析 / 舍入 / 冒号规则 / 版本漂移）。

## 数据铁律提醒

- 只使用本包冻结的真实数据；禁止模拟 / 合成数据。
- 禁止手工抄写论文数字作为「实测结果」；所有指标必须运行代码得到。
- 论文数值只能用于对照讨论。
- 提交的计数必须能从冻结数据 + 代码重算得到一致结果。
