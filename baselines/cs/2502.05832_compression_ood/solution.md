# solution.md — 少样本类不平衡模型压缩复现（arXiv:2502.05832）

- task_id: `2502.05832_compression_ood`
- 论文：Wu, T.-S., Lyu, S.-H., Chen, N., Qu, Z., Ye, B., "Compressing Model with Few Class-Imbalance Samples: An Out-of-Distribution Expedition" (arXiv:2502.05832v1)
- 复现的核心论断（Table 1 / §5.2 RQ1）：在「少量样本 + 长尾类不平衡 ratio=100」条件下，少样本压缩出的学生模型 top-1 显著低于**等总样本量**的平衡配置。
- 方法：VGG-16 教师 + 子集 logit 知识蒸馏压缩（学生 ≈1.24M 参数，约为教师的 1/100）。
- 数据：本卡冻结的官方 CIFAR-10（pickle 批次）——只从 5 个训练批次采样；`test_batch` 仅用于最终评估。

## 结论（claim 判定）

- **claim (a)**（不平衡显著损害少样本压缩，Δ ≥ 1.0pp）：**supported**。
  两个主实体档位 N=50、N=100 上，长尾不平衡的压缩学生准确率显著更低：N=50 Δ=−4.11pp（6/6 次重复为负），N=100 Δ=−5.36pp（6/6 为负）；N=10 档均值也为负（−1.06pp）。
- **claim (b)**（下降方向跨样本量档一致）：**partially_supported（主要档位一致）**。
  N=50 与 N=100 共 12/12 次重复方向一致且均 ≥1pp；N=10 因多数类样本律（40/1）与极端稀疏（少数类仅 1 个样本）而处于噪声层（6 次重复中 4 负 2 正，均值 −1.06pp）。方向在 N=50/100 上强一致成立。

## 结果总表（top-1 测试准确率，均值 ± std，每配置 6 个独立子集种子）

| N | 平衡 adjusted top-1 (%) | 长尾不平衡 top-1 (%) | Δ(pp) | 方向一致重复 |
|---|---|---|---|---|
| 10 | 19.24 ± 1.37 | 18.18 ± 0.71 | **−1.06** ± 1.56 | 4/6 |
| 50 | 25.34 ± 0.37 | 21.23 ± 0.52 | **−4.11** ± 0.52 | 6/6 |
| 100 | 28.21 ± 0.46 | 22.85 ± 0.52 | **−5.36** ± 0.48 | 6/6 |

（逐重复值与逐类分解见 `results/evidence_table.csv`、`results/per_class_accuracy.json`、`results/metrics.json`。）

## 方法概述

1. **数据核验**：从冻结 pickle 解码——train=50,000（每类恰好 5,000）、test=10,000（每类恰好 1,000）、32×32×3 uint8（`01_verify_data.py`，`results/data_verification.json`）。
2. **子集构造**（固定种子，可重算）：
   - 平衡：每类 N 个（总 10N），N∈{10,50,100}；
   - 不平衡：长尾指数衰减 `n_j ∝ 100^(−j/9)`，各类下限 1，余量并入多数类，**总样本严格 = 10N**（等总量公平约束）；多数/少数 = 40/1、202/2、402/4（N=10/50/100），有效 ratio≈100（N=50/100）。
   - 6 个重复种子 {42, 7, 2024, 5, 8, 13}；主档 seed=42；逐类样本量表见 `report.md` §3 与 `results/per_class_counts.csv`。
3. **教师**：VGG-16-BN（torchvision 结构、随机初始化）在冻结 CIFAR-10 全训练集上从头训练 200 epoch。SGD(mom=0.9, wd=5e-4)、lr=0.05 cosine、warmup 5、batch 256，增强=RandomCrop(4)+Flip。**来源声明**：本环境离线、无 ImageNet 预训练权重，故采用任务允许口径「CIFAR-10 上从头训练的 VGG-16」，详见报告 §4 与 §8。
4. **压缩管线**：logit KD——`L = α·T²·KL(s/t) + (1−α)·CE(s,y)`，T=4、α=0.6；学生 StudentNet 1.24M 参数；AdamW(lr=1e-3, wd=5e-4)、cosine、epoch 400/300/260（N=10/50/100）、batch 32、RandomCrop(4)+Flip，归一化由**各自训练子集**拟合；平衡/不平衡除子集外完全一致（含学生权重初始化种子）；固定 epoch、无验证/早停。
5. **评估**：测试集单次前向；另以独立脚本 `07_evaluate.py` 从保存 checkpoint 重算全部 36 个学生，与训练时数值逐一吻合。
6. **机制分解**（`09_perclass_analysis.py`）：长尾配置下头部类（≥50% 多数类样本量）平均准确率反而更高（Δ≈+33~+36pp），但尾部类系统性崩塌（Δ≈−10~−15pp），尾部崩坏在 top-1 上占据主导 → 净效应 imbalanced < balanced，与论文机理一致。

## 与论文锚对照（方向 + 量级带，不逐值复现）

| N | 论文 CD Δ(pp) | 本实验 Δ(pp) | 方向 |
|---|---|---|---|
| 10 | −3.55 | −1.06 | 一致 |
| 50 | −2.39 | −4.11 | 一致 |
| 100 | −1.32 | −5.36 | 一致 |

本实验按评测口径只判「方向 + |Δ|≥1.0pp 即显著」，与论文一致（论文 Δ∈[0.35, 5.26]pp 全程为负）。

## 交付物

- `scripts/01_verify_data.py … 09_perclass_analysis.py` + `run_all.sh`（一键全流程，固定种子可复现）
- `results/evidence_table.csv`（必交列齐全）、`results/metrics.json`、`results/per_class_counts.csv`、`results/per_class_accuracy.json`、`results/eval_all.json`
- `figures/teacher_curve.png`、`figures/kd_acc_delta.png`、`figures/per_class_counts.png`
- `report.md`（完整报告）