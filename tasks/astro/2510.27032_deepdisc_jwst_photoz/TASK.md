# TASK: DeepDISC JADES photo-z 目录——94,000 概率式测光红移数据产品的核验与可检验性（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- 任务 ID：`2510.27032_deepdisc_jwst_photoz`
- 层级：L1（critical claim；卡标 L2 → 按新映射造 L1 题）
- 领域：astro（河外天文，JWST 测光红移）
- 裁判：LLM judge（论文锚 + 证据抽查），见 `SCORE_RUBRIC.md`（私有）

## 1. Input（输入：冻结真实数据）

数据包位于 `data/`，全部为**真实公开数据**（论文作者随论文发布的目录，CC-BY-4.0），详见 `data/SOURCE.md`。

### `data/jades_photoz_catalog.csv.gz`（94,000 行，DeepDISC 对 JADES DR2 GOODS-S 测光源的测光红移目录）

论文（目标论文不提供）用 DeepDISC（Detection, Instance Segmentation and Classification with Deep Learning）以 JWST NIRCam 图像直接估计测光红移，并发布本目录。列：

| 列 | 含义 |
|---|---|
| `ID` | 源编号 |
| `z_phot_mode` | 概率密度 PDF 众数作为点估计红移 |
| `l68`/`u68`、`l95`/`u95`、`l99`/`u99` | 68%/95%/99% 置信区间上下界（PDF 分位数） |
| `forced` | 是否强制测量（`True`/`False`） |
| `spec_rep` | 光谱代表标记（值域为小整数，语义需从目录自洽性推断；不是谱红移数值） |

> 注：本包**不含 NIRCam 图像、模型权重、谱红移测试集**——论文的 scatter/outlier 质量指标（见下）需要这些额外数据，冻结数据不可直接复算。

## 2. Output（输出要求）

在你的工作目录下产出以下提交物：

- `claim.md`：你检验的**可证伪科学声称**（一句话）+ 失败条件 + 结论标签（`supported`/`partially_supported`/`contradicted`/`inconclusive`）。
- `code/`：完整可运行的分析代码（Python/R 均可），**所有指标必须从 `data/` 冻结数据重算**。
- `results/evidence_table.csv`：逐项核验表（至少含：检查项、样本量、统计量/通过率）。
- `results/metrics.json`：目录规模、CI 自洽率、z 分布统计、分层分析结果、可检验性清单。
- `results/figure.svg`（或 png/pdf）：至少一张关键图（如 z_phot 分布、CI 宽度随 z 变化、forced 分层对比）。
- `report.md`：方法、结果、结论、边界（≤2 页）。

### 科学目标（Scientific goal）

> **核心论断**：DeepDISC 能从 JWST NIRCam 图像直接产出**概率式**测光红移目录——覆盖 JADES DR2 GOODS-S 全部 ~94,000 个测光源，每源给出点估计（PDF 众数）与 68/95/99% 置信区间；且该估计质量与 EAZY 模板拟合相当（匹配滤光片时 scatter 更低、outlier 更少）。

请基于冻结数据回答：

1. **数据产品 claim**：目录规模是否为 94,000 行？列结构是否与"概率式 photo-z（mode + 68/95/99% CI）"一致？
2. **内部自洽性**：对全部源，`l68 ≤ z_phot_mode ≤ u68` 是否成立？CI 是否随置信度单调（l68≥l95≥l99 且 u68≤u95≤u99，即低置信区间更窄）？有无 NaN/病态值（如 z<0、CI 宽度为负、上下界越界）？给出通过率统计。
3. **分布与分层**：z_phot_mode 的分布形态（峰值、红移覆盖、与 JADES 深场预期一致性）；CI 宽度如何随 z 与 `forced` 变化？`forced=True` 子集的 CI 是否系统性更宽（更不可靠）？
4. **可检验性**：论文声称的质量指标——DeepDISC 测试集（N=298）scatter IQR=0.0311、outlier fraction η=0.0503、bias=0.0035，且匹配滤光片时优于 EAZY（EAZY 9-filter 版 IQR=0.0403/η=0.1242；EAZY+HST 版 IQR=0.0198/η=0.0705）——在**仅含本目录**的情况下，哪些可检验、哪些不可检验？精确列出所需额外数据（谱红移测试集、NIRCam 图像、模型权重），并说明目录本身能否支撑"质量相当/更优"的强结论。
5. **结论**：给出四档结论标签与适用边界。

提示（不给方法步骤）：目录核验 = 结构 + 自洽 + 分布；"概率式"的可检验含义是 CI 自洽与单调性；`spec_rep` 的语义（重复源/混合源代表）应从数据推断，不要臆造；"质量相当"的 claim 需要谱红移，明确说明在本数据上**不可证伪**哪些部分。

## 3. 数据铁律提醒

- **只用 `data/` 内冻结的真实数据**；禁止模拟/合成数据；禁止把论文/README 数值当作自己从数据算出的结果。
- 所有报告数字必须能从冻结数据 + 你的代码重算；裁判会抽查 1-2 个关键数并运行你的代码复核。
- 遵守 `data/SOURCE.md` 记录的许可（CC-BY-4.0，需署名）；数据文件 SHA-256 固定，不得改动。