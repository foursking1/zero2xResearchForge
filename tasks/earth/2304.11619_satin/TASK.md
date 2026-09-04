# Task: 2304.11619 SATIN（SATellite ImageNet）零样本遥感分类（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

> 编译状态：**compiled（自测分：待评测）** ｜ 2026-08-13 ｜ 领域：earth ｜ 建议层级 L2 → 产出 L1 题
> 数据：SATIN 的 SAT-4 组件（HF 官方镜像，100,000 张 28x28 图，4 类）

## 1. 问题（可证伪）

论文核心结果（摘要 + Table 3）：在 **SATIN（SATellite ImageNet，27 个遥感数据集的元基准）** 上，最强的零样本视觉-语言模型（**OpenCLIP ViT-G/14，LAION-2B 预训练**）整体分类准确率仅 **52.0%**；在 **SAT-4**（Task 1 Land Cover 组件）上 OpenCLIP 达到 **0.54**（Table 6）。即「**即便最强的开放 VL 模型，零样本遥感分类在 SATIN 元基准上也只有约 52% 的准确率**」。

**可证伪问题**：在给定的冻结真实数据（SAT-4 官方全量 100,000 张 28x28 图块，4 类：barren land / trees / grassland / buildings）上，用你实现的分类方法（零样本 CLIP 风格或微调均可），能否达到/逼近论文报告的 SAT-4 OpenCLIP 准确率 0.54？「SAT-4 上零样本 VL 模型准确率约 54%」这一 claim 在你的实验条件下成立吗？结论边界在哪（模型规模、预训练数据、类别粒度）？

**失败条件**：方法在冻结数据上 OA 显著低于 0.54（如 <0.40），或仅靠多数类基线（应判定 claim 未复现并给出证据）；若用全监督微调，则应与零样本基线对比并说明口径差异。

## 2. 数据说明

- **来源**：SATIN 元数据集 HF 官方镜像（`jonathan-roberts1/SATIN`）的 SAT-4 配置（与论文 Table 6 的 SAT-4 行一致：28x28、4 类、单标签）。完整出处/许可见 `data/SOURCE.md`。
- **结构**（`$PAPER_BENCH_DATA_DIR`）：
  - `data/data/SAT_4.parquet`：100,000 行 x 2 列（`image`：struct{bytes,path}，PNG 编码 28x28 影像；`label`：int64 0-3）
  - `data/SATIN.py`（HF 加载脚本）、`data/README.md`、`data/.gitattributes`
- **标签**：0=barren land, 1=trees, 2=grassland, 3=buildings（SAT-4 原始 4 类；镜像 label 0-3 与原始数据集类序一致）。
- **划分**：镜像为单一 train split（官方 SAT-4 与 DeepSat 一致为全量数据）；由 agent 按固定种子划分训练/评估子集（如 80/20），或按论文零样本协议直接用全量评估，并如实报告。
- **许可**：HF 镜像 license=other（学术用途）；SAT-4 原始数据公开提供。非医学/隐私数据。
- **checksum**：逐文件 SHA-256 见 `data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`。
- 体积：约 170 MB。

## 3. 方向提示

- 数据为官方 SAT-4 全量（28x28 小图、4 类）；论文主要关注零样本 VL 模型，但本卡不限制方法：零样本 CLIP 家族、微调 CNN/ViT 均可，需报告与论文锚的可比口径。
- 论文锚 0.54 是零样本（OpenCLIP ViT-G/14 2B）；若你使用更小模型或微调，应报告与锚的口径差异（模型规模、预训练数据量）。
- 类间混淆（grassland/trees、barren land/grassland）是主要误差来源，建议报告混淆矩阵与每类准确率。
- 防泄漏：统计（归一化均值/方差）仅从训练子集估计；禁止用测试标签调参。
