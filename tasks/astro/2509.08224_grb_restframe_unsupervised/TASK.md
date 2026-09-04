# 科研任务：验证 GRB rest-frame 参数双族人口结构与占比论断（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2509.08224_grb_restframe_unsupervised`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Zhu S.-Y. et al., "Unsupervised machine learning classification of gamma-ray bursts based on the rest-frame prompt emission parameters", A&A (2025)，arXiv:2509.08224
- 领域：astro / 高能天体物理 / 伽马射线暴分类

## 问题（可证伪）

论文核心论断（Abstract/§2.2/§3）：基于 rest-frame 伽马射线暴参数（T90,z、Ep,z、Eiso）做无监督降维（t-SNE/UMAP），370 个 GRB 被清晰分为两簇：**GRBs-I（小簇，~14%）与 GRBs-II（大簇，~86%）**；t-SNE 得 **54 个 GRBs-I（14.59%）**、UMAP 得 **53 个（14.32%）**；两簇中位数 **T90,z = 0.31 vs 13.84 s、Ep,z = 523.83 vs 407.94 keV、Eiso = 0.28 vs 75.19 ×10⁵¹ erg**；短暴 GRB 060614（合并起源）落入 GRBs-I，SN 关联的 GRB 980425/171205A 等落入 GRBs-II。论文样本主体为 **M20 目录（Minaev & Pozanenko 2020，314 个中剔除 14 个红移不准 → 300）+ 70 个新 GRB**。

请基于冻结的 M20 官方目录（论文样本主干）回答：

1. **目录规模与分类计数**：解析 `tablea1.dat`（152 字节定宽/行），报告总行数、`Type` 列各值计数；验证 ReadMe 摘要的 **45 个 Type I + 275 个 Type II（共 320）**。
2. **人口占比**：计算 Type I 占比；对照论文的 GRBs-I 占比（t-SNE 14.59%、UMAP 14.32%）与 M20 Type I 占比的一致性（应均 ~14%）。
3. **参数中位数**：分别计算 M20 Type I / Type II 的 T90z、Epz、Eiso 中位数（T90i/Epi 列即 rest-frame 值，Eiso 单位 10⁴⁴ J = ×10⁵¹ erg），与论文 GRBs-I/II 中位数（0.31/523.83/0.28 vs 13.84/407.94/75.19）逐项对比。
4. **双峰结构**：统计 T90,z < 2 s 的 GRB 数量与占比；Type I 中短暴占比 vs Type II 中短暴占比；验证论文「仅靠 T90 分类不可靠」的动机（有非 I 型短暴）。
5. **特定事件交叉验证**：在目录中查 GRB 060614、GRB 980425、GRB 171205A、GRB 110402A 的 Type 与参数，对照论文的 GRBs-I/II 归属论断（060614→GRBs-I；980425/171205A→GRBs-II；110402A 两方法不一致）。
6. **结论**：用四档标签判定「rest-frame 参数可将 GRB 分为 ~14% / ~86% 两族，且两族参数中位数显著分离」论断在冻结数据口径下为 `supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 冻结包物理位置：`$PAPER_BENCH_DATA_DIR`（来源 / 许可 / 逐文件 SHA-256 见 `data/SOURCE.md`、`data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 主数据（2 个真实文件，M20 官方发布目录）：
  - `tablea1.dat`（48,918 B，320 行）：M20 GRB 目录（152 字节/行定宽）。关键列（1-based 字节区间，权威定义见包内 `ReadMe`）：
    - 1–7 `GRB`（如 `060614A`）、9 `f_GRB`
    - 11–17 `T90i`（**rest-frame 持续时间，秒**）
    - 19–25 `z`（红移）、27–30 / 32–35 红移误差、37–38 `f_z`（`P`=测光红移）
    - 40–50 `Eiso`（10⁴⁴ J = ×10⁵¹ erg）、52–61 / 63–72 误差
    - 74–80 `Epi`（**rest-frame 峰值能量，keV**）、82–89 / 91–97 误差
    - 99–105 `Type`（M20 分类：`I` / `I+EE` / `II` / `II+SNph` / `II+SNsp`）
    - 107–116 `Exp`（实验）、134–138 `EH`（能量硬度参数）
  - `ReadMe`（7,655 B）：VizieR 官方字节级列说明。
- 原始来源：CDS VizieR `J/MNRAS/492/1919`（Minaev & Pozanenko 2020, MNRAS 492, 1919），`https://cdsarc.cds.unistra.fr/ftp/J/MNRAS/492/1919/`。
- 版本说明：论文样本 = M20（320 中剔除 14 个红移不准，取 300）+ 70 个新 GRB（论文 Table A.1）= 370；本包冻结的是 M20 官方目录 320 行全表。论文的 t-SNE/UMAP 嵌入与 370 样本的精确重建依赖论文的剔除名单与 Table A.2（机器可读版，arXiv 仅给出部分），本卡聚焦可精确复现的 **M20 目录层面人口结构**；无法复现的部分需如实说明。
- 许可：CDS/VizieR 开放目录数据（学术用途）；GRB 观测公开数据；无注册门槛。
- 规模：~57 KB，纯 Python 秒级。

## 方向提示

1. **解析方式**：固定宽度（byte slice）解析，按 `ReadMe` 的 Byte-by-byte 说明（每行 152 字节，latin-1）。
2. **Type 判定**：`Type` 列取 1-based 字节 99–105（0-based 98–104）；`I` 与 `I+EE` 均为 Type I（45 个）；`II`、`II+SNph`、`II+SNsp` 均为 Type II（275 个）。
3. **单位**：`Eiso` 单位 10⁴⁴ J，数值 ×10⁵¹ erg 与论文的 ×10⁵¹ erg 口径一致；`T90i`、`Epi` 即论文的 `T90,z`、`Ep,z`（rest-frame）。
4. **一致性对照**：M20 Type I 占比 14.06%（45/320）与论文 GRBs-I 占比 14.32–14.59% 高度一致；Type I/II 中位数与论文 GRBs-I/II 中位数同量级（T90z 0.27 vs 0.31 s；Eiso 0.69 vs 0.28）。如实报告小差异并归因（样本版本差异、聚类方法不同），禁止直接抄论文数字。
5. **边界说明**：论文的 370 样本、t-SNE/UMAP 嵌入结果（Table A.2）不在冻结包内，无法逐点重算；本卡验证的是论文样本主干的目录层面论断。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）、关键数字、与论文 Abstract/§3 论断的逐项对比及差异归因。
2. **`code/`**：完整可复现脚本（固定随机种子），从冻结数据读取并完成解析、计数、中位数、分族统计。
3. **`results/evidence_table.csv`**：至少含逐行解析表（列：`grb, t90z_s, z, epz_keV, eiso_e51, type`）与分族汇总行。
4. **`results/metrics.json`**：总行数、Type 计数与占比、Type I/II 中位数（T90z/Epz/Eiso）、T90z<2 s 统计、特定事件查询结果、论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（定宽解析 / M20 与 370 样本差异 / 无 Table A.2 故不重算嵌入）。

## 数据铁律提醒

- 只使用本包冻结的真实数据；禁止模拟 / 合成数据。
- 禁止手工抄写论文数字作为「实测结果」；所有指标必须运行代码得到。
- 论文数值只能用于对照讨论。
- 提交的计数必须能从冻结数据 + 代码重算得到一致结果。
