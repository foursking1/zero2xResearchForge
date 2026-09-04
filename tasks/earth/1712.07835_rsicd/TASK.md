# Task: 1712.07835 RSICD（L1 critical claim，图像描述）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

> 编译状态：**compiled（自测分：待评测）** ｜ 2026-08-13 ｜ 领域：earth ｜ 建议层级 L2 → 产出 L1 题
> 数据：HuggingFace RSICD 镜像（真实数据，详见 `data/SOURCE.md`，数据本体在 `$PAPER_BENCH_DATA_DIR`）

## 1. 问题（可证伪）

论文（Lu et al., "Exploring Models and Data for Remote Sensing Image Caption Generation", IEEE TGRS 2018）核心结果：提出 RSICD 遥感影像描述数据集（10,921 张、每图 5 句人工描述）并系统比较模型。在 RSICD 上（80% 训练 / 10% 验证 / 10% 测试），**注意力式 captioning 模型（attention-based）的 CIDEr 达 1.98**（Table IX，AlexNet 特征 + hard attention；BLEU-1 0.69、BLEU-4 0.37、METEOR 0.34、ROUGE-L 0.63），显著优于手工特征（Table IV 最佳 CIDEr 1.05）与简单 CNN 特征 LSTM（Table VI 最佳 CIDEr 2.05，AlexNet）。论文结论：深度 CNN 特征与注意力机制显著提升遥感影像描述质量。

**可证伪问题**：在给定的冻结真实数据（RSICD 官方子集镜像：1,000 训练 / 200 验证 / 200 测试图，224×224，每图 5 句描述）上，用你实现的 captioning 方法能否生成接近论文质量的描述（CIDEr ~1.98）？「CNN 特征显著优于手工特征（CIDEr 约 1.98 vs 1.05）」这一 claim 在你的实验条件下成立吗？

**失败条件**：测试 CIDEr 显著低于论文量级（如 <0.8），或描述退化为重复模板句（此时应判定 claim 未复现并给出证据）。

## 2. 数据说明

- **来源**：HuggingFace RSICD 镜像（`train/test/valid` 3 parquet；官方数据集由论文作者发布）。完整出处/许可/校验见 `data/SOURCE.md`。
- **结构**（`$PAPER_BENCH_DATA_DIR/data/data`）：
  - `train-00000-of-00001.parquet`：1,000 行；`valid-`：200 行；`test-`：200 行。列 `filename, captions`（5 句列表）, `image`（224×224 RGB）, `text`（首句，供参考）。
  - 官方 RSICD 共 10,921 图；本镜像为官方子集（1,400 图），详见 SOURCE.md §4。
- **划分**：冻结即官方 train/valid/test 划分（本镜像 1,000/200/200）。论文协议为 80/10/10，镜像比例一致。
- **校验**：4 个冻结文件 SHA-256 登记于 `$PAPER_BENCH_DATA_ROOT/checksums.sha256` 与 `data/source_manifest.json`。
- 体积：约 70 MB。

## 3. 方向提示（关键点，不构成步骤指导）

- 论文 Table IX（attention-based，RSICD）：AlexNet-hard CIDEr 1.98312 / BLEU-1 0.68968 / BLEU-4 0.36895 / METEOR 0.33521 / ROUGE-L 0.62673；Table VI（multimodal CNN+LSTM）AlexNet CIDEr 2.05261；Table IV（手工特征 LSTM）最佳 CIDEr ~1.05。
- 评测指标：BLEU-1..4、METEOR、ROUGE-L、CIDEr（5 句参考）；**CIDEr 为主锚**。
- 建议对比平凡基线（最频繁模板句）与手工特征（SIFT/BOW/FV/VLAD + LSTM ~CIDEr 1.05）以验证「深度特征优势」的 claim。
- 224×224 输入、句子长度 ~8–15 词；训练 1,000 图规模有限，建议预训练 CNN 特征 + 注意力解码器。
- 防泄漏：所有统计/词表/超参只能从训练划分估计；不得用测试图或测试句调参。

## 4. 输出要求（结论 + 证据表 + 代码 + 报告）

请在工作目录生成 `submission/`：

1. **结论**（`submission/report.md` 首部）：用 `supported` / `partially_supported` / `contradicted` / `inconclusive` 给出结论并附一句理由；明确写出测试集 CIDEr，并与论文锚 1.98（Table IX，AlexNet-hard attention）比较（绝对差与相对差）。
2. **证据表**（`submission/results/evidence_table.csv`）：按 200 张测试图汇总，列为 `filename, bleu1, bleu2, bleu3, bleu4, meteor, rouge_l, cider` + 整体均值行；另附 `submission/results/metrics.json` 含各指标整体均值与逐图分值。
3. **代码**（`submission/`）：完整可重跑，从冻结 parquet 读入并计算上述全部数字。
4. **报告**（`submission/report.md`）：方法描述（特征/解码器/是否预训练）、训练预算与超参、平凡/手工基线对照、防泄漏声明、失败样例（描述与真值对比）、局限性说明。

## 5. 数据铁律提醒

- 只使用冻结的真实数据；**禁止**模拟/合成/手工构造数据，禁止从外部下载替代数据。
- 禁止用测试集 caption 做任何训练/调参。
- 所有关键数字必须能从冻结数据 + 提交代码重算（裁判将抽查）。
- 不许改动冻结文件；SHA-256 见 `data/source_manifest.json`。
