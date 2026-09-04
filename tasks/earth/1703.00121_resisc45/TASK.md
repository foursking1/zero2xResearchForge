# Task: 1703.00121 RESISC45 遥感场景分类（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

> 编译状态：**compiled（自测分：待评测）** ｜ 2026-08-13 ｜ 领域：earth ｜ 建议层级 L2 → 产出 L1 题
> 数据：RESISC45 官方全量（31,500 图，45 类，每类 700）

## 1. 问题（可证伪）

论文核心结果（Table 6）：在 **RESISC45**（45 类遥感场景，每类 700 张，共 31,500 张）上，Fine-tuned VGGNet-16 在 10% 训练比例下达 **87.15±0.45% OA**、20% 训练比例下达 **90.36±0.18% OA**。即「**深度 CNN 微调可在 RESISC45 上以 10–20% 训练数据达到 87–90% OA 的遥感场景分类性能**」。

**可证伪问题**：在给定的冻结真实数据（RESISC45 31,500 张，45 类，每类 700 张）上，用你实现的分类方法（含按论文口径的 10%/20% 训练比例划分），能否达到/逼近论文报告的 VGGNet-16 87.15%（10%）/90.36%（20%）？「RESISC45 高精度场景分类（~90% OA）」这一 claim 成立吗？结论边界在哪（训练比例、模型容量、类别混淆）？

**失败条件**：方法在冻结数据 10%/20% 训练比例下 OA 显著低于论文对应值（如 10%<70%、20%<80%），或仅靠平凡基线（此时应判定 claim 未复现并给出证据）。

## 2. 数据说明

- **来源**：RESISC45 HF 镜像（31,500 行 parquet，45 类每类 700 张，256×256）。完整出处/许可见 `data/SOURCE.md`。
- **结构**（`$PAPER_BENCH_DATA_DIR`）：`data/data/train-00000-of-00001-d0e01c925a6227a8.parquet`（31,500 行 × 2 列：image struct + label 0-44）；另有 900 张原图（airplane_001.jpg 等，与 parquet 同源）。
- **标签**：0-44 对应论文 45 类（airplane, airport, baseball diamond, basketball court, beach, bridge, chaparral, church, circular farmland, cloud, commercial area, dense residential, desert, forest, freeway, grass, golf course, harbor, industrial area, intersection, island, lake, meadow, medium residential, mobile home park, mountain, overpass, palace, parking lot, railway, railway station, rectangular farmland, river, roundabout, runway, sea ice, ship, snowberg, sparse residential, stadium, storage tank, tennis court, terrace, thermal power station, wetland）。
- **划分**：本卡冻结全量；训练/测试划分按论文口径由 agent 从每类固定比例随机划分（10%/20% 等），需固定种子并报告。
- **许可**：RESISC45 公开研究用途（论文提供下载）；非医学/隐私。本包仅用于学术评测。
- **checksum**：逐文件 SHA-256 见 `data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`。
- 体积：约 440 MB。

## 3. 方向提示

- 复现论文口径：每类随机取 10% 训练/其余测试；建议报告 10% 与 20% 两种训练比例。
- 微调预训练 CNN（ImageNet）是论文最佳方法；也可用其他方法，但需报告与 87.15/90.36 的差距。
- 45 类类别多、类间相似（如 circular/rectangular farmland），混淆矩阵有助于分析。
- 防泄漏：数据划分必须从冻结数据按固定种子完成；统计仅用训练子集。

## 4. 输出要求

请在工作目录生成 `submission/`：

1. **结论**（`submission/report.md` 首部）：`supported` / `partially_supported` / `contradicted` / `inconclusive` + 理由。写出你得到的 10% 与 20% 训练比例 OA，与论文锚 87.15±0.45 / 90.36±0.18 比较。
2. **证据表**（`submission/results/evidence_table.csv`）：每个训练比例各一行 + 每类一行（至少一个比例），列 `split, train_ratio, class_id, class_name, tp, fp, tn, fn, precision, recall, f1, accuracy`；`submission/results/metrics.json` 含各比例 `overall_accuracy`、`seed`、`train_per_class`、`test_per_class`。
3. **代码**（`submission/`）：完整可重跑，从冻结 parquet 读入、按种子划分、计算全部数字。
4. **报告**（`submission/report.md`）：方法、训练预算、防泄漏声明、混淆分析、局限性。

## 5. 数据铁律提醒

- 只使用冻结真实数据；禁止模拟/合成。
- 关键数字必须能从冻结数据 + 代码重算。
- 不许改动冻结文件。
