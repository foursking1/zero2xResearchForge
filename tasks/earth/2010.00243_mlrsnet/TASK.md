# Task: 2010.00243 MLRSNet（L1 critical claim，多标签场景分类）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

> 编译状态：**compiled（自测分：待评测）** ｜ 2026-08-13 ｜ 领域：earth ｜ 建议层级 L2 → 产出 L1 题
> 数据：HuggingFace MLRSNet 镜像（真实数据，详见 `data/SOURCE.md`，数据本体在 `$PAPER_BENCH_DATA_DIR`）

## 1. 问题（可证伪）

论文（Qi et al., "MLRSNet: A Multi-label High Spatial Resolution Remote Sensing Dataset for Semantic Scene Understanding", ISPRS J. 2020）核心结果：提出 MLRSNet 多标签高分辨率遥感场景数据集（109,161 张 256×256、60 类标签、平均每图约 5 个标签），并评测 8 种微调 CNN。**最佳模型 MLRSNet-DenseNet201 在 40% 训练比例下 mAP 达 88.77%、F1 0.8538**（Table 6/7）；ResNet50 84.28→86.01（30%/40%）、InceptionV3 82.33→84.84；且训练数据越多性能越高。论文结论：多标签标注 + 深度 CNN 微调可有效完成高分辨率遥感场景的多标签识别。

**可证伪问题**：在给定的冻结真实数据（完整 MLRSNet：109,161 图、60 类多标签；固定 40/60 划分：43,664 训练 / 65,497 测试）上，用你实现的多标签分类方法能否达到/逼近论文报告的 ~88.8% mAP？「DenseNet 系深模型在 MLRSNet 上 mAP 显著优于 VGG（~75%）、且接近 89%」这一 claim 在你的实验条件下成立吗？

**失败条件**：测试 mAP 显著低于论文量级（如 <80%），或仅靠频繁标签/单标签等平凡基线（此时应判定 claim 未复现并给出证据）。

## 2. 数据说明

- **来源**：HuggingFace MLRSNet 镜像（3 parquet 全量；官方数据集 CC BY 4.0）。完整出处/许可/校验见 `data/SOURCE.md`。
- **结构**（`$PAPER_BENCH_DATA_DIR/data/data`）：`train-0000{0,1,2}-of-00003-*.parquet`，合计 109,161 行，列 `image`（JPEG bytes，256×256 RGB）、`label`（int 列表，0–59 共 60 类，类名见 README）。
- **划分**：`mlrsnet_split_40.csv`（固定 40/60，seed 20260813，字段 `shard_file, row_in_shard, split`）。论文协议为 20/30/40% 训练比例随机划分；本卡冻结 40% 一次实例。
- **校验**：4 个冻结文件（3 parquet + 划分 CSV）SHA-256 登记于 `$PAPER_BENCH_DATA_ROOT/checksums.sha256` 与 `data/source_manifest.json`。
- 体积：约 1.3 GB。

## 3. 方向提示（关键点，不构成步骤指导）

- 论文 mAP 88.77% / F1 0.8538（DenseNet201，40%）；ResNet101 85.72、DenseNet169 87.35、InceptionV3 84.84（Table 6）。深而宽的多标签头（sigmoid + 0.5 阈值）是达成高分的关键。
- 60 类、平均约 5 个标签/图；建议报告 mAP、F1、以及 per-class AP 与混淆分析（易混类如 buildings/road/trees）。
- 建议对比平凡基线（频繁标签/全部预测）与 VGG 系（~73–75%）以验证「模型深度」的 claim。
- 防泄漏：统计/增强/阈值只能从训练集估计；不得用测试标签调参。

## 4. 输出要求（结论 + 证据表 + 代码 + 报告）

请在工作目录生成 `submission/`：

1. **结论**（`submission/report.md` 首部）：用 `supported` / `partially_supported` / `contradicted` / `inconclusive` 给出结论并附一句理由；明确写出测试集整体 mAP，并与论文锚 88.77%（Table 6，MLRSNet-DenseNet201，40%）比较（绝对差与相对差）。
2. **证据表**（`submission/results/evidence_table.csv`）：按类汇总，列为 `label, class_name, n_train, n_test, n_correct, precision, recall, f1, ap` + 整体 mAP/F1 行；另附 `submission/results/metrics.json` 含整体 `mAP`、`F1`、每类指标。
3. **代码**（`submission/`）：完整可重跑，从冻结 parquet + `mlrsnet_split_40.csv` 读入并计算上述全部数字。
4. **报告**（`submission/report.md`）：方法描述（模型/预训练/多标签头/阈值）、训练预算与超参、平凡基线与浅模型对照、防泄漏声明、易混类分析、局限性说明。

## 5. 数据铁律提醒

- 只使用冻结的真实数据；**禁止**模拟/合成/手工构造数据，禁止从外部下载替代数据。
- 禁止用测试标签做任何训练/调参。
- 所有关键数字必须能从冻结数据 + 提交代码重算（裁判将抽查）。
- 不许改动冻结文件；SHA-256 见 `data/source_manifest.json`。
