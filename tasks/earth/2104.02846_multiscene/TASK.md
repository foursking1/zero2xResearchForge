# Task: 2104.02846 MultiScene（L1 critical claim，多场景识别）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

> 编译状态：**compiled（自测分：待评测）** ｜ 2026-08-13 ｜ 领域：earth ｜ 建议层级 L2 → 产出 L1 题
> 数据：HuggingFace MultiScene 镜像（真实数据，详见 `data/SOURCE.md`，数据本体在 `$PAPER_BENCH_DATA_DIR`）

## 1. 问题（可证伪）

论文（Hua et al., "MultiScene: A Large-scale Dataset and Benchmark for Multi-scene Recognition in Single Aerial Images", IEEE TGRS 2022）核心结果：提出 MultiScene（100,000 张多场景航拍图）与干净标注子集 MultiScene-Clean（14,000 张、36 类、多标签），系统评测 22 个基线。**在 MultiScene-Clean 上（7,000 训练 / 7,000 测试），最强基线 ResNeXt-101 的 mAP 仅 64.8%、OF1 71.3%**（Table II）；传统方法（SVM/RF/XGBOOST）mAP 仅 14.9–16.9%。论文结论：多场景识别极具挑战，深度模型大幅超越传统方法，但绝对性能仍有很大提升空间。

**可证伪问题**：在给定的冻结真实数据（MultiScene-Clean：14,000 图、36 类多标签；固定 50/50 划分：7,000 训练 / 7,000 测试）上，用你实现的深度多标签分类方法能否达到/逼近论文报告的 ~64.8% mAP？「深度模型（mAP~65%）大幅超越传统方法（~15%）」这一 claim 在你的实验条件下成立吗？

**失败条件**：测试 mAP 显著低于论文量级（如 <55%），或仅靠频繁标签等平凡基线（此时应判定 claim 未复现并给出证据）。

## 2. 数据说明

- **来源**：HuggingFace MultiScene 镜像（Clean split，2 parquet；官方数据集 MIT 许可）。完整出处/许可/校验见 `data/SOURCE.md`。
- **结构**（`$PAPER_BENCH_DATA_DIR/data/data`）：`train-0000{0,1}-of-00002-*.parquet`，合计 14,000 行，列 `image`（JPEG bytes，512×512 RGB）、`label`（int 列表，0–35 共 36 类）。
- **划分**：`multiscene_split_50.csv`（固定 50/50，seed 20260813，字段 `shard_file, row_in_shard, split`）。论文协议即 7,000/7,000。
- **校验**：3 个冻结文件（2 parquet + 划分 CSV）SHA-256 登记于 `$PAPER_BENCH_DATA_ROOT/checksums.sha256` 与 `data/source_manifest.json`。
- 体积：约 0.87 GB。

## 3. 方向提示（关键点，不构成步骤指导）

- 论文 ResNeXt-101 mAP 64.8（Table II，MultiScene-Clean）；ResNet-152 63.8、DenseNet-169 63.2；传统方法 mAP 14.9–16.9。
- 36 类、每图 1–8 个标签；单图含多个场景（如 river + train station）是核心难点；建议报告 mAP 与 mCF1/mEF1/OF1 全套。
- 建议对比平凡基线（频繁标签/全部预测）与传统方法（SVM/RF ~15%）以验证「深度大幅超越传统」的 claim。
- 防泄漏：统计/增强/阈值只能从训练集估计；不得用测试标签调参。

## 4. 输出要求（结论 + 证据表 + 代码 + 报告）

请在工作目录生成 `submission/`：

1. **结论**（`submission/report.md` 首部）：用 `supported` / `partially_supported` / `contradicted` / `inconclusive` 给出结论并附一句理由；明确写出测试集整体 mAP，并与论文锚 64.8%（Table II，ResNeXt-101）比较（绝对差与相对差）。
2. **证据表**（`submission/results/evidence_table.csv`）：按类汇总，列为 `label, class_name, n_train, n_test, n_correct, precision, recall, f1, ap` + 整体行；另附 `submission/results/metrics.json` 含整体 `mAP`、`mCF1`、`mEF1`、`OF1`、每类指标。
3. **代码**（`submission/`）：完整可重跑，从冻结 parquet + `multiscene_split_50.csv` 读入并计算上述全部数字。
4. **报告**（`submission/report.md`）：方法描述（模型/预训练/多标签头/阈值）、训练预算与超参、平凡与传统方法基线对照、防泄漏声明、易混类（multi-scene）分析、局限性说明。

## 5. 数据铁律提醒

- 只使用冻结的真实数据；**禁止**模拟/合成/手工构造数据，禁止从外部下载替代数据。
- 禁止用测试标签做任何训练/调参。
- 所有关键数字必须能从冻结数据 + 提交代码重算（裁判将抽查）。
- 不许改动冻结文件；SHA-256 见 `data/source_manifest.json`。
