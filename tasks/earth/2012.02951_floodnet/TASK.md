# Task: 2012.02951 FloodNet 洪灾航拍视觉问答（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

> 编译状态：**compiled（自测分：待评测）** ｜ 2026-08-13 ｜ 领域：earth ｜ 建议层级 L2 → 产出 L1 题
> 数据：FloodNet 官方 VQA 问答（train 4,511 对含答案）+ 官方影像（takara HF 镜像，train/valid 图）

## 1. 问题（可证伪）

论文核心结果（Table 5）：在 **FloodNet**（飓风 Harvey 后无人机航拍影像数据集）VQA 任务上，**MFB with Co-Attention** 模型在 **Validation 达到整体准确率 0.72、Testing 0.73**（其中 Yes/No 类 0.98-0.99、条件识别类 0.96-0.97、简单计数 0.29-0.31、复杂计数 0.26-0.28）。即「**多模态 VQA 模型可在洪灾航拍影像上达到约 72-73% 整体准确率（计数类难题除外）**」。

**可证伪问题**：在给定的冻结真实数据（FloodNet 官方 VQA：4,511 个训练问-答对（含标准答案）+ 对应航拍影像）上，用你实现的 VQA 方法，能否达到/逼近论文报告的 MFB 整体准确率 0.72（validation）？「FloodNet VQA 约 72-73% 整体准确率」这一 claim 成立吗？结论边界在哪（训练数据量、问题类型、语言偏差）？

**失败条件**：方法在冻结评估子集上 OA 显著低于 0.72（如 <0.55），或主要靠问题先验回答（不依赖图像，应判定 claim 未复现并给出证据）。

## 2. 数据说明

- **来源**：FloodNet 官方 VQA 标注（Google Drive 官方发布；Track 2）+ 官方影像（takara-ai HF 镜像，与官方 JPG 一致）。完整出处/许可见 `data/SOURCE.md`。
- **结构**（`$PAPER_BENCH_DATA_DIR`）：
  - `data/vqa_questions/Training_Question.json`：4,511 个问-答对（字段：Image_ID、Question、Ground_Truth（标准答案）、Question_Type（Condition_Recognition / Simple_Counting / Complex_Counting / Yes_No））
  - `data/vqa_questions/Valid_Question.json`：1,415 个验证问题（**不含答案**，官方保留给评估服务器）
  - `data/takara_track2/train_image/img/*.JPG`（约 1,448 张）、`data/takara_track2/valid_image/img/*.JPG`（450 张）：航拍影像（与官方同源）
  - `data/Test/image/*.jpg`：官方 Test 影像（309 张）
- **划分**：官方 Valid/Test 答案未发布 → 由 agent 用固定种子从官方 Training 问-答对划分训练/评估子集（建议 85/15），并在报告中说明口径差异；论文锚 0.72（validation）/0.73（test）为参照量级。
- **许可**：FloodNet 公开研究用途（挑战赛数据）；非医学/隐私。
- **checksum**：逐文件 SHA-256 见 `data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`。
- 体积：全冻结包约 24 GB（6,906 文件；核心影像 3.4 GB + 官方 Test/Validation + takara 镜像）。

## 3. 方向提示

- 任务：影像+问题 → 答案（多分类，答案集约 40+ 个）；评估整体准确率与按类型准确率。
- 论文最佳 MFB with Co-Attention（VGG16 图像特征 + 双层 LSTM 问题特征 + 双线性融合）。
- 问题类型差异大：Yes/No 与条件识别接近 0.97+，计数类（简单/复杂）只有 0.26-0.31——报告按类型分解。
- 语言偏差消融（随机换图）可检验模型是否真正在看图。
- 防泄漏：评估子集答案不得用于调参。

## 4. 输出要求

请在工作目录生成 `submission/`：

1. **结论**（`submission/report.md` 首部）：`supported` / `partially_supported` / `contradicted` / `inconclusive` + 理由。写出整体 OA，与论文锚 0.72（validation）比较。
2. **证据表**（`submission/results/evidence_table.csv`）：每问一行 + 整体行，列 `split, question_type, image_id, question, answer, prediction, correct`；`submission/results/metrics.json` 含 `overall_accuracy`、`accuracy_by_type`、`train_size`、`seed`、`random_image_ablation_accuracy`。
3. **代码**（`submission/`）：完整可重跑，从冻结 JSON + 影像读入并计算全部数字。
4. **报告**（`submission/report.md`）：方法（图像/文本编码、融合）、训练预算、防泄漏声明、按问题类型分析、语言偏差消融、局限性（官方 valid/test 答案未发布）。

## 5. 数据铁律提醒

- 只使用冻结真实数据；禁止模拟/合成。
- 关键数字必须能从冻结数据 + 代码重算（裁判将抽查）。
- 不许改动冻结文件。
