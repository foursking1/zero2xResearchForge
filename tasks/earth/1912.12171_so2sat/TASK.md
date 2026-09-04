# Task: 1912.12171 So2Sat LCZ42 城市局地气候区分类（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

> 编译状态：**compiled（自测分：待评测）** ｜ 2026-08-13 ｜ 领域：earth ｜ 建议层级 L2 → 产出 L1 题
> 数据：So2Sat 官方 validation split（官方 h5 冻结，24,119 样本）

## 1. 问题（可证伪）

论文核心结果（Table V）：在 **So2Sat LCZ42** 数据集（Sentinel-1/2 融合遥感影像，17 个局地气候区 LCZ 类别）上，基于注意力的 **ResNeXt-CBAM** 模型（仅 Sentinel-2 影像）在验证集上达到 **OA 0.61 / WA 0.92 / AA 0.51 / Kappa 0.58**（SVM 基线 OA 0.54 / Kappa 0.49）。即「**深度 CNN+注意力可在 So2Sat LCZ42 上达到约 61% 总体精度（高于 SVM 基线约 7pp）**」。

**可证伪问题**：在给定的冻结真实数据（So2Sat 官方 validation split h5，24,119 个 32×32 像元块，Sentinel-1 8 波段 + Sentinel-2 10 波段，17 类）上，用你实现的分类方法，能否达到/逼近论文报告的 ResNeXt-CBAM OA≈0.61（S2 only）？「深度模型显著超越 SVM 基线的高精度 LCZ 分类」这一 claim 成立吗？结论边界在哪（训练数据规模、波段组合、类别混淆）？

**失败条件**：方法在冻结数据上 OA 显著低于 0.61（如 <0.40），或与 SVM 基线无显著差异（应判定 claim 未复现并给出证据）。

## 2. 数据说明

- **来源**：So2Sat 官方数据（So2Sat LCZ42，ETH 发布；官方 h5 文件，与论文验证集一致）。完整出处/许可见 `data/SOURCE.md`。
- **结构**（`$PAPER_BENCH_DATA_DIR/data/official_h5`）：
  - `validation.h5`：24,119 个样本，keys：`label`（24,119×17 one-hot）、`sen1`（24,119×32×32×8，Sentinel-1 VV/VH 双极化×4 时相）、`sen2`（24,119×32×32×10，Sentinel-2 10 波段）
  - `testing.h5.gz` / `validation.h5.gz`：官方压缩原始包（同源，仅存档）
- **划分**：冻结包为官方 validation split（论文 Table V 的评估集）。论文训练集（约 38 万像元块）未冻结 → 由 agent 从冻结 validation 中按固定种子自行划分训练/评估子集（建议 80/20），并在报告中说明口径差异。
- **许可**：So2Sat 公开研究用途（学术许可）；非医学/隐私。
- **checksum**：逐文件 SHA-256 见 `data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`。
- 体积：约 6.6 GB（含压缩包）。

## 3. 方向提示

- 数据是 32×32 小像元块；S1 为 8 通道（VV/VH×4 时相），S2 为 10 波段反射率。
- 论文最佳为注意力的 ResNeXt（S2 only）；可对比 S1+S2 融合 vs S2 only、以及 SVM/RF 浅层基线。
- 17 个 LCZ 类中建成区子类（compact/midrise/open 等）混淆是主要误差来源；报告混淆矩阵与每类 recall。
- 防泄漏：归一化统计仅从训练子集估计；划分种子固定。

## 4. 输出要求

请在工作目录生成 `submission/`：

1. **结论**（`submission/report.md` 首部）：`supported` / `partially_supported` / `contradicted` / `inconclusive` + 理由。写出 OA/WA/AA/Kappa，与论文锚 OA 0.61（S2 only）比较。
2. **证据表**（`submission/results/evidence_table.csv`）：每类一行 + 整体行，列 `split, class_id, precision, recall, f1, support`；`submission/results/metrics.json` 含 `overall_accuracy`、`weighted_accuracy`、`average_accuracy`、`kappa`、`train_size`、`seed`、`bands_used`。
3. **代码**（`submission/`）：完整可重跑，从冻结 h5 读入并计算全部数字。
4. **报告**（`submission/report.md`）：方法、训练预算、防泄漏声明、波段组合对比、局限性（训练集未冻结、子集划分差异）。

## 5. 数据铁律提醒

- 只使用冻结的真实数据；禁止模拟/合成数据。
- 报告的关键数字必须能从冻结数据 + 提交代码重算（裁判将抽查）。
- 不许改动冻结文件。
