# Task: 1509.03602 DeepSat SAT-6 场景分类（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

> 编译状态：**compiled（自测分：待评测）** ｜ 2026-08-13 ｜ 领域：earth ｜ 建议层级 L2 → 产出 L1 题
> 数据：SAT-6 官方 Test split（HF 镜像冻结，81,000 图，6 类）

## 1. 问题（可证伪）

论文核心结果（摘要）：DeepSat 框架在 **SAT-6** 数据集（6 类航拍/卫星场景，28×28 图块）上达到 **分类准确率 93.9%**，比 DBN/CNN/SDA 三个 SOTA 算法高约 15%；在 SAT-4 上达到 97.95%（高约 11%）。即「**基于深度信念网络的框架可从 1m 分辨率航空影像高精度识别土地覆盖（SAT-6 6 类 OA≈93.9%）**」。

**可证伪问题**：在给定的冻结真实数据（SAT-6 官方 Test split 81,000 张 28×28 图块，6 类：barren land/building/grassland/road/trees/water）上，用你实现的图像分类方法，能否达到/逼近论文报告的 SAT-6 OA≈93.9%？「SAT-6 上高精度（OA≈94%）土地覆盖识别」这一 claim 在你的实验条件下成立吗？结论边界在哪（模型复杂度、训练数据规模、类别混淆）？

**失败条件**：方法在该冻结测试集上 OA 显著低于 93.9%（如 <75%），或仅靠「全部预测为多数类」这类平凡基线（此时应判定 claim 未复现并给出证据）。

## 2. 数据说明

- **来源**：SAT-6 数据集 HF 镜像（README 注明为 SAT-6 的 **Test split**，与论文 §4 的 81,000 测试图块一致：总 405,000 图块中 4/5 训练、1/5 测试）。完整出处/许可见 `data/SOURCE.md`。
- **结构**（`$PAPER_BENCH_DATA_DIR`）：单个 parquet `train-00000-of-00001-c47ada2c92f814d2.parquet`，81,000 行 × 2 列：
  - `image`：struct{bytes, path}，JPEG 编码的 28×28 影像
  - `label`：int64，0-5（0=barren land, 1=building, 2=grassland, 3=road, 4=trees, 5=water）
- **划分**：官方 Test split 81,000 图（论文口径：SAT-6 全量 405,000，其中 324,000 训练 + 81,000 测试，训练与测试为不相交图块集合）。
- **许可**：README 声明 Public Domain；论文声明数据公开提供。非医学/隐私数据，可用于学术评测。
- **checksum**：逐文件 SHA-256 见 `data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`。修改冻结文件属违规。
- 体积：约 140 MB。

## 3. 方向提示（关键点，不构成步骤指导）

- 数据是官方 Test split；论文训练集（324,000 图）未冻结。你需要自行决定训练策略：从冻结 81,000 图中按固定种子划分训练/验证子集（如 70/15/15），或使用其他真实数据预训练（如实报告来源）。**禁止**把测试子集用于调参。
- 28×28 小图块、6 类；类间混淆（grassland/trees、road/building）是主要误差来源，建议报告混淆矩阵。
- 报告与多数类基线的差距；二值/浅层 vs 深度模型对比可选。
- 防泄漏：统计（归一化均值/方差）仅从训练子集估计。

## 4. 输出要求（结论 + 证据表 + 代码 + 报告）

请在工作目录生成 `submission/`：

1. **结论**（`submission/report.md` 首部）：用 `supported` / `partially_supported` / `contradicted` / `inconclusive` 给出结论并附一句理由。必须写出你得到的整体 OA，与论文锚 93.9% 比较（绝对差与相对差）。
2. **证据表**（`submission/results/evidence_table.csv`）：每类一行 + 整体行，列为 `split, class_id, class_name, tp, fp, tn, fn, precision, recall, f1, accuracy`；另附 `submission/results/metrics.json` 含 `overall_accuracy`、`macro_f1`、`majority_class_baseline`、`train_size`、`seed`。
3. **代码**（`submission/`）：完整可重跑，从冻结 parquet 读入并计算全部数字（数据路径用参数或相对路径）。
4. **报告**（`submission/report.md`）：方法描述、训练预算、防泄漏声明、类别不平衡/混淆分析、局限性（官方训练集未冻结、子集划分差异）。

## 5. 数据铁律提醒

- 只使用冻结的真实数据；禁止模拟/合成/手工构造数据。
- 报告的所有关键数字必须能从冻结数据 + 提交代码重算（裁判将抽查）。
- 不许改动冻结文件。
