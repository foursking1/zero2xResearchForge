# Task: 1709.00029 EuroSAT RGB 场景分类（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

> 编译状态：**compiled（自测分：待评测）** ｜ 2026-08-13 ｜ 领域：earth ｜ 建议层级 L2 → 产出 L1 题
> 数据：EuroSAT RGB 官方镜像（27,000 图，10 类，train/validation/test 划分）

## 1. 问题（可证伪）

论文核心结果（摘要）：在 **EuroSAT**（Sentinel-2 多光谱影像，10 类土地覆盖，覆盖 13 个光谱波段与多时相）上，基于深度 CNN 的分类系统达到 **整体分类准确率 98.57%**；论文另报告浅层 CNN（§III）在部分设置下达 89.03%。即「**CNN 可在 Sentinel-2 影像上以 ~98.6% OA 进行 10 类土地覆盖分类**」。

**可证伪问题**：在给定的冻结真实数据（EuroSAT RGB 27,000 张 64×64 影像，10 类，官方 train/validation/test 划分 16200/5400/5400）上，用你实现的分类方法，能否达到/逼近论文报告的 OA≈98.57%？「Sentinel-2 上高精度（OA≈98.6%）土地覆盖分类」这一 claim 在你的实验条件下成立吗？结论边界在哪（RGB-only vs 多光谱、类别混淆、数据划分）？

**失败条件**：方法在冻结 test 集上 OA 显著低于 98.57%（如 <85%），或仅靠平凡基线（此时应判定 claim 未复现并给出证据）。

## 2. 数据说明

- **来源**：EuroSAT RGB HF 镜像（`tjackpenny/EuroSAT` 或同源官方划分；README 与论文一致：10 类、64×64、Sentinel-2 RGB 三波段）。完整出处/许可见 `data/SOURCE.md`。
- **结构**（`$PAPER_BENCH_DATA_DIR`）：3 个 parquet：
  - `train-00000-of-00001.parquet`：16,200 行（image struct + label 0-9 + filename）
  - `validation-00000-of-00001.parquet`：5,400 行
  - `test-00000-of-00001.parquet`：5,400 行
  - 标签：0=Annual Crop, 1=Forest, 2=Herbaceous Vegetation, 3=Highway, 4=Industrial Buildings, 5=Pasture, 6=Permanent Crop, 7=Residential Buildings, 8=River, 9=SeaLake
- **划分**：官方 60/20/20 划分（论文 §III：27,000 图，每类 2,700）。
- **许可**：HF README 标注 unknown（EuroSAT 原数据据论文为公开研究用途；非医学/隐私）。本包仅用于学术评测。
- **checksum**：逐文件 SHA-256 见 `data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`。
- 体积：约 170 MB。

## 3. 方向提示

- 冻结数据为 RGB 三波段（论文主结果基于 13 波段 Sentinel-2 或 RGB 均报告）；请明确你用的是 RGB 通道。
- 类别不平衡：EuroSAT 每类 2,700 张基本均衡；混淆主要在 Annual Crop/Permanent Crop、Residential/Industrial。
- 建议报告与多数类基线（10%）的对比。
- 防泄漏：统计仅从 train 估计；不得用 validation/test 调参（validation 仅用于最终报告可选）。

## 4. 输出要求

请在工作目录生成 `submission/`：

1. **结论**（`submission/report.md` 首部）：`supported` / `partially_supported` / `contradicted` / `inconclusive` + 理由。写出整体 OA 并与论文锚 98.57% 比较。
2. **证据表**（`submission/results/evidence_table.csv`）：每类一行 + 整体行，列 `split, class_id, class_name, tp, fp, tn, fn, precision, recall, f1, accuracy`；`submission/results/metrics.json` 含 `overall_accuracy`、`macro_f1`、`majority_class_baseline`、`channels_used`。
3. **代码**（`submission/`）：完整可重跑，从冻结 parquet 读入计算。
4. **报告**（`submission/report.md`）：方法、训练预算、防泄漏声明、混淆分析、局限性（RGB-only 与论文 13 波段主结果差异）。

## 5. 数据铁律提醒

- 只使用冻结真实数据；禁止模拟/合成。
- 关键数字必须能从冻结数据 + 代码重算。
- 不许改动冻结文件。
