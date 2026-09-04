# 科研任务：验证 Evryscope 南天极区高幅变星巡天的发现统计与人口组成（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`1905.02738_evryscope_variable_stars`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Ratzloff J.K. et al., "Variables in the Southern polar region Evryscope 2016 data set", PASP 131, h4201 (2019)，arXiv:1905.02738
- 领域：astro / 恒星变星 / 巡天（Evryscope 南天极区）

## 问题（可证伪）

论文核心论断（Abstract/§4.4–4.6）：在 160,000 颗亮星（m_v<14.5、赤纬 −75° 至 −90°、9<m_v<14.5）中搜寻高幅（≥5%）变星，**恢复 346 个已知变星（VSX 返回率 17.9%）**，**新发现 303 个变星**（含 **168 个食双星** + 135 个非食变星）；303 个新发现中 **267 个主序星、34 个巨星、2 个未分类**（光谱型 G 最常见）；食双星多数周期 ≤75 h、振幅 5–25%，变量星振幅更小、周期更短。

请基于官方发布的发现目录（CDS VizieR J/PASP/131/H4201）回答：

1. **发现目录规模**：解析 `table10.dat`（Variable Star discoveries）与 `table11.dat`（Eclipsing Binary discoveries），报告各表行数与总发现数；对照论文 §4.5 的 168 EB + 135 变量 = **303**。
2. **组成核对**：表 11（EB）159 条 vs 论文 168；表 10（变量）135 条 vs 论文 135（精确一致）。差异 9 条全部为主序星（对照 §4.6 的 267 MS）：从目录的 `Size` 列验证 MS/giant 计数（258/34/2 vs 267/34/2），归因差异。
3. **分类验证**：统计两表合并的 `Size`（ms / giant / 空）与 `SpType` 分布；验证「G 型最常见」「巨星中变量（24）多于食双星（10）」。
4. **分布特征**：对表 11 验证「多数周期 ≤75 h（实测 ~84%）、振幅 5–25%（实测 ~72%）」；对表 10 验证「振幅更小、周期更短」（振幅 ≥5% 占比 ~60% vs EB ~97%）。
5. **结论**：用四档标签判定「303 新发现（168 EB + 135 变量）与人口组成」论断在冻结目录口径下为 `supported` / `partially_supported` / `contradicted` / `inconclusive`，并说明 EB 计数差异（159 vs 168）的可能原因。

## 数据说明

- 冻结包物理位置：`$PAPER_BENCH_DATA_DIR`（来源 / 许可 / 逐文件 SHA-256 见 `data/SOURCE.md`、`data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 主数据（3 个真实文件，论文官方发布目录）：
  - `table10.dat`（12,960 B，135 行）：Variable Star discoveries（95 字节/行定宽）
  - `table11.dat`（15,264 B，159 行）：Eclipsing Binary discoveries（95 字节/行定宽）
  - `ReadMe`（5,108 B）：VizieR 官方字节级列说明（列定义见下）
  - 两表同构，关键列（1-based 字节区间）：`ESID` 1–22（EVRJ 格式源标识）、`APASS` 24–31、`RAdeg` 33–40、`DEdeg` 42–49、`Vmag` 51–55、`RPM` 57–61、`B-V` 63–67、`Size` 69–73（ms/giant）、`SpType` 75–79、`Per` 81–89（小时）、`Amp` 91–95（振幅，mag）
- 原始来源：CDS VizieR `J/PASP/131/H4201`（Ratzloff+ 2019），`https://cdsarc.cds.unistra.fr/ftp/J/PASP/131/H4201/`。
- 版本说明：论文正文（§4.5）报告 168 EB，发布目录 table11 为 159 条（差 9）；非食变量 135 完全一致。差异本身是任务的讨论点，**禁止直接抄论文数字作为实测结果**。
- 许可：CDS/VizieR 开放目录数据（学术用途）；Evryscope 巡天公开数据；无注册门槛。
- 规模：~33 KB，纯 Python 秒级。

## 方向提示

1. **解析方式**：固定宽度（byte slice）解析，按 `ReadMe` 的 Byte-by-byte 说明（每行 95 字节）。
2. **口径差异**：论文 303 = 168 EB + 135 变量；目录 294 = 159 EB + 135 变量。EB 差 9 对应 §4.6 MS 计数差 9（267 vs 258），可推断发布目录删除了 9 条主序 EB（可能为后续证认/版本更新）；如实报告并归因，禁止直接否定论文。
3. **分类验证**：`Size` 列空值 = 论文「2 not classified」；giant 计数 34 与论文完全一致。
4. **分布特征**：振幅/周期为连续数值，验证「多数」用占比表述（如周期 ≤75 h 占比）。
5. **对照原则**：论文数值只能用于对照讨论，禁止作为「实测结果」。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）、关键数字、与论文 §4.4–4.6 的逐项对比及差异归因。
2. **`code/`**：完整可复现脚本（固定随机种子），从冻结数据读取并完成解析、统计、分布验证。
3. **`results/evidence_table.csv`**：至少含两表合并的逐行解析表与汇总表（列：`table, esid, size, sptype, per_h, amp` + 汇总行）。
4. **`results/metrics.json`**：两表行数、总发现数、EB/变量计数、Size 分布、SpType top 分布、振幅/周期占比、论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（定宽解析 / 目录 vs 论文版本差异 / EB 差 9 归因）。

## 数据铁律提醒

- 只使用本包冻结的真实数据；禁止模拟 / 合成数据。
- 禁止手工抄写论文数字作为「实测结果」；所有指标必须运行代码得到。
- 论文数值只能用于对照讨论。
- 提交的计数必须能从冻结数据 + 代码重算得到一致结果。
