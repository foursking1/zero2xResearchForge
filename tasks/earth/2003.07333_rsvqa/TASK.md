# Task: 2003.07333 RSVQA 遥感视觉问答（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

> 编译状态：**compiled（自测分：待评测）** ｜ 2026-08-13 ｜ 领域：earth ｜ 建议层级 L2 → 产出 L1 题
> 数据：RSVQA LR validation 2,000 问答子集（HF 镜像冻结）

## 1. 问题（可证伪）

论文核心结果（Table II）：在 **RSVQA**（遥感影像视觉问答）LR 数据集测试集上，提出的 CNN-LSTM VQA 模型达到 **总体准确率 79.08%（±0.20）**；其中 Presence 类问题 87.46%、Rural/Urban 90.00%、Comparison 81.50%、Count 67.01%（Table II）。即「**多模态 CNN-LSTM 模型可在遥感影像上回答关于对象存在性/数量/比较/城乡的视觉问题，总体准确率约 79%**」。

**可证伪问题**：在给定的冻结真实数据（RSVQA LR validation 2,000 问-答对子集，每对含影像+英文问题+标准答案）上，用你实现的 VQA 方法，能否达到/逼近论文报告的 LR 测试 OA≈79.08%？「遥感 VQA 总体准确率约 79%」这一 claim 成立吗？结论边界在哪（训练数据量、问题类型分布、语言偏差）？

**失败条件**：方法在冻结数据上 OA 显著低于 79.08%（如 <60%），或主要靠问题先验回答（不依赖图像，应判定 claim 未复现并给出证据）。

## 2. 数据说明

- **来源**：RSVQA LR 数据集 HF 镜像（validation split 的 2,000 问答子集）。完整出处/许可见 `data/SOURCE.md`。
- **结构**（`$PAPER_BENCH_DATA_DIR`）：`data/data/validation-00000-of-00001.parquet`（2,000 行 × 3 列：`image`（JPEG 影像）、`question`（英文问题）、`answer`（标准答案字符串））。
- **划分**：镜像为 validation 子集（2,000 问答对，来自论文 LR 数据集的 validation split）；由 agent 按固定种子自行划分训练/评估子集（建议 80/20），并报告口径差异。
- **许可**：CC BY 4.0（镜像声明）；RSVQA 原始数据公开（rsvqa.sylvainlobry.com）。非医学/隐私。
- **checksum**：逐文件 SHA-256 见 `data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`。
- 体积：约 174 MB。

## 3. 方向提示

- 任务：图像+问题 → 答案（多选分类或自由文本，按镜像答案集合映射）；评估用准确率（答案完全匹配）。
- 论文 LR 主要问题类型：Count/Presence/Comparison/Rural-Urban/Area 等；报告按类型分解准确率。
- 论文 73.78% 是「随机换图」语言偏差消融结果：若你的模型在换图后准确率不掉，说明真正在看图。
- 防泄漏：训练只用训练子集；不得用评估子集答案调参。

## 4. 输出要求

请在工作目录生成 `submission/`：

1. **结论**（`submission/report.md` 首部）：`supported` / `partially_supported` / `contradicted` / `inconclusive` + 理由。写出整体 OA，与论文锚 79.08% 比较。
2. **证据表**（`submission/results/evidence_table.csv`）：每问一行 + 整体行，列 `split, question_type, question, answer, prediction, correct`；`submission/results/metrics.json` 含 `overall_accuracy`、`accuracy_by_type`、`random_image_ablation_accuracy`、`train_size`、`seed`。
3. **代码**（`submission/`）：完整可重跑，从冻结 parquet 读入并计算全部数字。
4. **报告**（`submission/report.md`）：方法（图像/文本编码、融合）、训练预算、防泄漏声明、按问题类型分析、语言偏差消融、局限性。

## 5. 数据铁律提醒

- 只使用冻结真实数据；禁止模拟/合成。
- 关键数字必须能从冻结数据 + 代码重算（裁判将抽查）。
- 不许改动冻结文件。
