# Task: 2110.08733 LoveDA 城乡土地覆盖语义分割（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

> 编译状态：**compiled（自测分：待评测）** ｜ 2026-08-13 ｜ 领域：earth ｜ 建议层级 L2 → 产出 L1 题
> 数据：LoveDA HF 镜像（train 子集 2 个 shard，~562 张 1024×1024 影像+掩码）

## 1. 问题（可证伪）

论文核心结果（Table 2/3）：在 **LoveDA**（城乡土地覆盖分割数据集，7 类）上，**HRNet W32 达到 mIoU 49.79%**；加入多尺度训练测试增强（MSTrTe）后 **52.14%**。即「**SOTA 分割网络可在 LoveDA 城乡数据上达到约 50-52% mIoU**」。

**可证伪问题**：在给定的冻结真实数据（LoveDA 镜像 train 子集，约 562 张 1024×1024 影像+像素级掩码，7 类）上，用你实现的分割方法，能否达到/逼近论文报告的 HRNet mIoU≈49.79%？「LoveDA 上约 50% mIoU 的分割性能」这一 claim 成立吗？结论边界在哪（训练数据规模、城乡域差异、类别不平衡）？

**失败条件**：方法在冻结数据上 mIoU 显著低于 49.79%（如 <35%），或仅靠多数类基线（应判定 claim 未复现并给出证据）。

## 2. 数据说明

- **来源**：LoveDA HF 镜像（train 子集）。完整出处/许可见 `data/SOURCE.md`。
- **结构**（`$PAPER_BENCH_DATA_DIR`）：`data/data/train-0000{0,1}-of-00009.parquet`（各 ~281 行，共 ~562；列：image（JPEG 1024×1024）、label（PNG 掩码 1024×1024，像素值 0-6 对应 7 类：background、building、road、water、barren、forest、agriculture——以镜像 README/标注为准））。
- **划分**：镜像为 train split 子集（论文全量 train 2,522 张、val 1,669 张；冻结为 2 shard 子集）；由 agent 按固定种子自行划分训练/评估子集（建议 85/15），并报告口径差异。
- **许可**：LoveDA 公开研究用途（CC BY-NC 类学术许可，以镜像为准）。非医学/隐私。
- **checksum**：逐文件 SHA-256 见 `data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`。
- 体积：约 916 MB。

## 3. 方向提示

- 像素级分割任务；评估 mIoU（7 类均值）。
- 论文最佳 HRNet W32；可对比 DeepLabV3+/UNet 等。
- LoveDA 含城市/乡村双域样本，域间风格差异大；可探索域适应/增强策略。
- 防泄漏：划分种子固定；统计仅用训练子集。

## 4. 输出要求

请在工作目录生成 `submission/`：

1. **结论**（`submission/report.md` 首部）：`supported` / `partially_supported` / `contradicted` / `inconclusive` + 理由。写出 mIoU，与论文锚 49.79%（HRNet）比较。
2. **证据表**（`submission/results/evidence_table.csv`）：每类一行 + 整体行，列 `split, class_id, class_name, iou, precision, recall, f1, pixels`；`submission/results/metrics.json` 含 `mean_iou`、`class_iou`、`model`、`train_size`、`seed`。
3. **代码**（`submission/`）：完整可重跑，从冻结 parquet 读入并计算全部数字。
4. **报告**（`submission/report.md`）：方法、训练预算、防泄漏声明、每类错误分析、城乡域差异、与论文全量口径差异、局限性。

## 5. 数据铁律提醒

- 只使用冻结真实数据；禁止模拟/合成。
- 关键数字必须能从冻结数据 + 代码重算（裁判将抽查）。
- 不许改动冻结文件。
