# 科研任务：少样本类不平衡模型压缩（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id: `2502.05832_compression_ood`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Compressing Model with Few Class-Imbalance Samples: An Out-of-Distribution Expedition（arXiv:2502.05832）
- 领域：CS / 模型压缩 / 少样本学习 / 类别不平衡

## 问题（可证伪）

论文在「少量样本 + 长尾类不平衡」条件下研究少样本模型压缩（few-sample model compression，即用极少样本把大教师模型压缩成小模型，如知识蒸馏/剪枝式压缩），并报告核心结论：**类别不平衡会显著损害少样本压缩模型的测试准确率——与等总样本量的平衡配置相比，压缩后模型 top-1 准确率明显下降（论文 Table 1 的 16 个单元格全部满足 imbalanced < balanced，下降幅度 0.35–5.26 个百分点）。**

可证伪表述：基于冻结的 CIFAR-10 数据，(a)「在少量样本压缩设置下，长尾类不平衡配置的 top-1 准确率显著低于平衡配置（Δ ≥ 1.0 pp）」是否成立；(b)「该下降方向在多个样本量档（N=10/50/100）下保持一致」是否成立。

## 方向提示（非方法步骤）

- 指标：top-1 准确率（%，越高越好；论文主指标，§5.1 Evaluation Metric）。
- 数据：本包冻结 CIFAR-10（`data/cifar-10-batches-py/`，标准 pickle 批次格式，5 个训练批次 + test_batch + batches.meta）。训练只允许从 5 个训练批次采样；`test_batch` 只用于最终评估。
- 少量样本子集构造（固定种子，可复现）：
  - 平衡配置：每类 N 个样本（总 10N），N ∈ {10, 20, 50, 100}（论文 Table 1 的 Num 档）。
  - 不平衡配置：长尾分布，imbalance ratio = 100（多数类 N 个、按指数衰减到少数类 ≈ N/100 个），总样本量控制在 10N 量级（与平衡配置等量，保证公平比较）。
  - 采样种子固定并在报告中声明；禁止从测试集采样。
- 压缩方法：自选一种少样本压缩管线（如教师-学生知识蒸馏、剪枝+微调等），但必须满足：(1) 教师模型为 CIFAR-10 上训练/微调过或公开的预训练 VGG-16（论文所用教师；报告须声明教师来源）；(2) 平衡与不平衡配置使用**完全相同**的压缩管线与超参，仅训练子集不同；(3) 学生模型更小（参数量显著低于教师）。
- 防泄漏：test_batch 不得参与子集构造、教师微调、验证或早停；所有统计/归一化只能由训练子集拟合。

## 数据说明

- 数据包：`data/`（冻结真实数据，来源/许可/checksum 见 `data/SOURCE.md` 与 `data/source_manifest.json`）
  - `data/cifar-10-batches-py/data_batch_{1..5}`：官方 CIFAR-10 训练集 50,000 张（每类 5,000，标准 pickle：`data`(N×3072 uint8) + `labels`）
  - `data/cifar-10-batches-py/test_batch`：官方测试集 10,000 张（每类 1,000）
  - `data/cifar-10-batches-py/batches.meta`：类别名（airplane…truck，10 类）
- 来源：CIFAR-10（Krizhevsky & Hinton 2009，80 Million Tiny Images 子集）；本包从多伦多大学官方 HuggingFace 镜像 `uoft-cs/cifar10`（plain_text parquet）下载并按官方 pickle 批次格式转换；标签分布已核验（train 每类 5,000 / test 每类 1,000）。
- 许可：CIFAR-10 为学术研究用途数据集（原始主页 https://www.cs.toronto.edu/~kriz/cifar.html；无商业再分发授权）；本包仅用于学术研究评测。
- 注意：本包批次文件的内容与官方 `cifar-10-python.tar.gz` 相同（同图同标签、标签分布逐类一致），但**图像顺序可能与官方 tar 的批次文件不完全一致**（由 HF parquet 转换而来）；因此与论文 Table 1 的逐值对齐时需考虑抽样差异，详见 `PAPER_ANCHOR.md` 容差说明。
- checksum（sha256）：见 `data/source_manifest.json`（含每文件 size 与 sha256）。

## 输出要求（提交物）

1. **结论**：对 claim (a) 与 (b) 分别给出 `supported / partially_supported / contradicted / inconclusive`，并说明数据支持的强度。
2. **证据表**：`results/evidence_table.csv`，至少含列：`config`（balanced/imbalanced）、`n_per_class`（多数类 N）、`n_train_total`、`method`（压缩管线名）、`top1_acc`、`delta_pp`（imbalanced − balanced）。
3. **代码**：完整可复现的子集构造 + 教师准备 + 压缩 + 评估脚本（固定随机种子），从 `data/` 读取冻结数据。
4. **报告**：`report.md`：子集构造协议（含每类样本数表）、教师来源与训练细节、压缩管线描述、防泄漏说明、局限性与种子敏感性。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成/模拟数据替代（包括不存在的"额外 OOD 数据"）。
- 测试集只用于最终评估；禁止用于采样、验证、早停或调参。
- 平衡/不平衡两个配置必须等总样本量（论文 Table 1 口径），且除训练子集外一切设置相同。
- 禁止把论文数值当作"本实验实测"；所有指标必须由你的代码从本包数据算出。