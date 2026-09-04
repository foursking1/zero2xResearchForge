# 科研任务：验证 VIPERS 角向近邻偶然投影与 SED 光度红移基线质量论断（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2211.01901_neznet_vipers_photoz`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Tosone F. et al., "Augmenting photometric redshift estimates using spectroscopic nearest neighbours", A&A 672, A85 (2023)，arXiv:2211.01901
- 领域：astro / 河外天体物理 / 光度红移（VIPERS 巡天）

## 问题（可证伪）

论文核心论断（Abstract/§3–5/Fig 1）：VIPERS 巡天中星系与其角向近邻的红移相关被**大量偶然投影（chance superpositions）稀释**——只有一部分角向近邻是真实物理对（红移相近）；基于 SED 模板拟合的光度红移（Moutard+ 2016）基线质量为 **σ≈0.08、离群率≈3%**（σ 为归一化 RMS，离群定义为 |z_spec−z|≥0.15(1+z_spec)）；训练在图神经网络 NezNet 后，剔除低置信邻居可将子样本（保留 ~75%）的离散度降到 **0.04**、离群率降到 **0.8%**。

请基于论文官方发布的数据（NezNet 仓库附带的 VIPERS W1/W4 光度-光谱匹配表）回答：

1. **数据规模**：解析 `W1_PHOT-SPEC_MATCH_PDR.txt` 与 `W4_PHOT-SPEC_MATCH_PDR.txt`（`#` 开头为列说明注释行），报告数据行数、0.5<z_spec<1.2 子集行数；对照论文 §4 的 W1 训练约 3×10⁴、W4 测试约 2×10⁴ 口径。
2. **基线光度红移质量**：用论文 Eq.(5)–(8) 的 σ / bias / |bias| / 离群率定义，在 W4（安全光谱标记 zflg≤14 且 z_spec>0，论文「96.1% 置信度」口径）上计算 zphot 相对 zspec 的质量指标；对照论文基线 σ≈0.08、离群≈3%。
3. **偶然投影与角向相关**：用 haversine 公式（论文 Eq.3）计算每颗星最近角向邻居的角距与红移差；报告不同角距分箱（如 <5″、5–10″、10–20″、20–50″、50–200″）中「物理对」（|Δz|≤0.08(1+z)）占比；验证「近角距对红移强相关、随角距增大被偶然投影稀释」的 Fig 1 论断。
4. **可验证边界**：讨论论文的「0.08→0.04、3%→0.8%、保留 ~75%」改进数值需要 NezNet 模型推理（本包不含模型权重），从数据层面可验证的是基线质量与角向相关结构。
5. **结论**：用四档标签判定「VIPERS 角向近邻中大量偶然投影 + SED 光度红移基线 σ≈0.08/离群≈3%」论断在冻结数据口径下为 `supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 冻结包物理位置：`$PAPER_BENCH_DATA_DIR`（来源 / 许可 / 逐文件 SHA-256 见 `data/SOURCE.md`、`data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 主数据（3 个真实文件，论文官方 GitHub 仓库发布）：
  - `W1_PHOT-SPEC_MATCH_PDR.txt`（5,483,397 B）：VIPERS W1 场光度-光谱匹配表（40,315 数据行）。列（1-based）：
    1 `num`（源 ID）、2 `alpha`（赤经 deg）、3 `delta`（赤纬 deg）、4 `selmag`（mag）、5 `zspec`（光谱红移）、6 `zflg`（光谱质量标记）、7 `zphot`（SED 光度红移，Moutard+ 2016）、8–19 `u_T07/g_T07/r_T07/i_T07/z_T07/Ks` 及误差（Tresse+ 2007 系统）
  - `W4_PHOT-SPEC_MATCH_PDR.txt`（3,799,468 B）：VIPERS W4 场（27,961 数据行），列同 W1
  - `NezNet_README.md`（656 B）：仓库说明与 MIT 许可
- 原始来源：https://github.com/tos-1/NezNet （arXiv:2211.01901 官方代码/数据仓库）。
- 口径说明：VIPERS PDR2 光谱质量标记 zflg（1–4 置信度递增；11–14/21–24/31–34 为多发射线位掩码）；论文用「96.1% 置信度」的安全标记（zflg=1 对应 96.1%）；推荐 zflg≤14 且 z_spec>0 作为安全样本的稳健近似（编译器实测与论文基线量级一致）。
- 许可：MIT License（仓库）；VIPERS 数据依 VIPERS PDR2 公开发布政策。
- 规模：~9.3 MB（F 盘），numpy/scipy 即可处理（最近邻分析用 cKDTree）。

## 方向提示

1. **解析**：按空格/制表符切分；`#` 注释行记录列定义（权威）。
2. **σ 定义**：论文 Eq.(5) σ = sqrt(mean(((z_spec−z)/(1+z_spec))²))（归一化 RMS，非 MAD）；Eq.(8) 离群 |z_spec−z| ≥ 0.15(1+z_spec)。
3. **基线口径**：W4 全样本 zflg≤14 且 z_spec>0 时 σ≈0.089、离群≈3.9%（编译器实测），与论文 0.08/3% 同量级；样本切法不同会有小幅差异，需如实报告并归因。
4. **物理对定义**：论文 §4 用 |Δz| ≤ Δz·(1+z_spec)（典型 Δz=0.08）。
5. **对照原则**：论文数值只能用于对照讨论，禁止作为「实测结果」；模型改进数值（0.04/0.8%/75%）不可从数据单独重算，需说明边界。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）、关键数字、与论文 Abstract/§5 论断的逐项对比及差异归因。
2. **`code/`**：完整可复现脚本（固定随机种子），从冻结数据读取并完成解析、指标计算、最近邻分析。
3. **`results/evidence_table.csv`**：至少含基线质量汇总行与最近邻角距分箱表（列：`ang_bin_arcsec, n_pairs, n_physical, frac_physical, median_dz`）。
4. **`results/metrics.json`**：W1/W4 行数、σ/bias/|bias|/离群率、最近邻物理对占比与分箱、论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（样本切法 / 模型改进不可重算 / 匹配表语义）。

## 数据铁律提醒

- 只使用本包冻结的真实数据；禁止模拟 / 合成数据。
- 禁止手工抄写论文数字作为「实测结果」；所有指标必须运行代码得到。
- 论文数值只能用于对照讨论。
- 提交的计数必须能从冻结数据 + 代码重算得到一致结果。
