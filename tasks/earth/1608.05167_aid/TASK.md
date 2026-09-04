# Task: 1608.05167 AID 多标签遥感场景分类（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

> 编译状态：**compiled（自测分：待评测）** ｜ 2026-08-13 ｜ 领域：earth ｜ 建议层级 L2 → 产出 L1 题
> 数据：AID_MultiLabel 镜像（3,000 图，17 类多标签，CC0）

## 1. 问题（可证伪）

论文核心结果（Table 6）：在 **AID**（30 类航空场景，10,000 张，0.5–8m）上，GoogLeNet 微调在多种训练比例下 OA 达 **86.39±0.55%～94.71±1.33%**，显著高于手工特征。即「**深度 CNN 微调可在 AID 场景分类上达到 ~90% 量级 OA，且数据越多精度越高**」。

**可证伪问题**：在给定的冻结真实数据（AID_MultiLabel 镜像，3,000 张 600×600 航空影像，17 类多标签）上，用你实现的分类方法（多标签任务，或按镜像标签子集做单标签），能否达到/逼近论文报告的 GoogLeNet OA 量级（86.4%–94.7%）？「CNN 在 AID 场景分类上高精度（OA≥86%）」这一 claim 成立吗？结论边界在哪（多标签 vs 30 类单标签口径、训练数据量）？

**失败条件**：方法在冻结数据上整体指标显著低于论文量级（如多标签 mAP/F1 明显退化或单标签 OA<65%），或仅靠平凡基线（应判定 claim 未复现并给出证据）。

## 2. 数据说明

- **来源**：AID_MultiLabel HF 镜像（SATIN 项目提供的 AID 多标签版本；3,000 图，17 类，CC0）。完整出处/许可见 `data/SOURCE.md`。
- **结构**（`$PAPER_BENCH_DATA_DIR`）：`data/data/train-00000-of-00001-ee58cb5d786e111e.parquet`（3,000 行 × 2 列：image struct + label list<int64>）。
- **标签**：17 类（airplane, bare soil, buildings, cars, chaparral, court, dock, field, grass, mobile home, pavement, sand, sea, ship, tanks, trees, water）；每行可含多个标签（多标签）。
- **划分**：镜像仅有单一 split；由 agent 按固定种子划分 train/validation/test（建议 60/20/20），并报告。
- **许可**：CC0 1.0 Universal（镜像声明；原 AID 数据集公开研究用途）。非医学/隐私。
- **checksum**：逐文件 SHA-256 见 `data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`。
- 体积：约 265 MB。

## 3. 方向提示

- 冻结数据为**多标签** 17 类版本（非论文 30 类单标签全量 10,000 张）。锚比较时需说明口径差异；任务本身按多标签评估（mAP、macro-F1、subset accuracy）与单标签视角（每类二分类）均可。
- 论文量级参考：GoogLeNet 微调 86.39%（20% 训练）→94.71%（80% 训练，Table 6）。
- 600×600 原图较大，可下采样训练；需报告预处理。
- 防泄漏：统计仅用训练子集；划分种子固定。

## 4. 输出要求

请在工作目录生成 `submission/`：

1. **结论**（`submission/report.md` 首部）：`supported` / `partially_supported` / `contradicted` / `inconclusive` + 理由。写出整体多标签指标（mAP 或 macro-F1）与单标签 OA（如适用），与论文 GoogLeNet 86.39–94.71% 量级比较并说明口径。
2. **证据表**（`submission/results/evidence_table.csv`）：每类一行（二分类 tp/fp/tn/fn/precision/recall/f1）+ 整体行（mAP、macro-F1、subset accuracy）；`submission/results/metrics.json` 含 `mAP`、`macro_f1`、`subset_accuracy`、`per_class_count`、`seed`、`split_sizes`。
3. **代码**（`submission/`）：完整可重跑，从冻结 parquet 读入计算。
4. **报告**（`submission/report.md`）：方法、训练预算、防泄漏声明、多标签 vs 单标签口径讨论、局限性。

## 5. 数据铁律提醒

- 只使用冻结真实数据；禁止模拟/合成。
- 关键数字必须能从冻结数据 + 代码重算。
- 不许改动冻结文件。
