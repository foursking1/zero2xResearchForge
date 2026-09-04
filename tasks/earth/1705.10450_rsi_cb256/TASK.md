# Task: 1705.10450 RSI-CB256 遥感场景分类（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

> 编译状态：**compiled（自测分：待评测）** ｜ 2026-08-13 ｜ 领域：earth ｜ 建议层级 L2 → 产出 L1 题
> 数据：RSI-CB256 镜像（24,750 图，粗 7 类 + 细 42 类，两级标签）

## 1. 问题（可证伪）

论文核心结果（Table 6）：在 **RSI-CB256**（对象中心遥感场景，256×256，两级层次标注：6 大类 + 35/42 子类）上，VGG-16 达到 **训练 OA 98%+ / 测试 OA 95.13%**；ResNet 测试 OA 95.02%、GoogLeNet 94.07%。即「**深度 CNN 可在 RSI-CB256 对象中心遥感场景上达到 ~95% 测试 OA**」。

**可证伪问题**：在给定的冻结真实数据（RSI-CB256 镜像，24,750 张 256×256，粗标签 7 类 + 细标签 42 类）上，用你实现的分类方法（细类 42 类为主任务，粗类 7 类为辅助），能否达到/逼近论文报告的 VGG-16 测试 OA≈95.13%？「RSI-CB256 高精度场景分类（~95% OA）」这一 claim 成立吗？结论边界在哪（训练划分、类别不平衡、层级标签利用）？

**失败条件**：方法在冻结数据上细类测试 OA 显著低于 95.13%（如 <80%），或仅靠平凡基线（应判定 claim 未复现并给出证据）。

## 2. 数据说明

- **来源**：RSI-CB256 HF 镜像（10 个 parquet shard，24,750 行；label_1 粗类 + label_2 细类）。完整出处/许可见 `data/SOURCE.md`。
- **结构**（`$PAPER_BENCH_DATA_DIR`）：`data/data/train-00000-of-00010-*.parquet` … `train-00009-of-00010-*.parquet`（每 shard 2,475 行，共 24,750；列：label_1、label_2、image struct）。
- **标签**：label_1（7 类：transportation, other objects, woodland, water area, other land, cultivated land, construction land）；label_2（42 类细类：parking lot, avenue, highway, bridge, marina, crossroads, airport runway, pipeline, town, airplane, forest, mangrove, artificial grassland, river protection forest, shrubwood, sapling, …）。
- **划分**：镜像为单一 split；由 agent 按固定种子划分（建议 80/20 train/test），并报告。
- **许可**：镜像许可以 README 为准（原 RSI-CB 数据公开研究用途）。非医学/隐私。
- **checksum**：逐文件 SHA-256 见 `data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`。
- 体积：约 840 MB。

## 3. 方向提示

- 论文 Table 6 的 95.13% 是 VGG-16 测试 OA（RSI-CB256 列；论文按官方划分训练/测试，未公开划分文件 → 用固定种子自行划分并说明）。
- 两级标签：可用 label_2（42 类）为主任务，label_1（7 类）作为层次辅助或多任务。
- 对象中心影像类别间差异大；主要误差来自相似子类（如 avenue/highway）。
- 防泄漏：统计仅用训练子集；划分种子固定。

## 4. 输出要求

请在工作目录生成 `submission/`：

1. **结论**（`submission/report.md` 首部）：`supported` / `partially_supported` / `contradicted` / `inconclusive` + 理由。写出细类测试 OA，与论文锚 95.13% 比较。
2. **证据表**（`submission/results/evidence_table.csv`）：每类一行 + 整体行，列 `split, class_level, class_id, class_name, tp, fp, tn, fn, precision, recall, f1, accuracy`；`submission/results/metrics.json` 含 `overall_accuracy`（label_2）、`macro_f1`、`label1_accuracy`、`seed`、`split_sizes`。
3. **代码**（`submission/`）：完整可重跑，从冻结 parquet 读入计算。
4. **报告**（`submission/report.md`）：方法、训练预算、防泄漏声明、层级标签利用、混淆分析、局限性。

## 5. 数据铁律提醒

- 只使用冻结真实数据；禁止模拟/合成。
- 关键数字必须能从冻结数据 + 代码重算。
- 不许改动冻结文件。
