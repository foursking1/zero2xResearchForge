# agent_solution — 复现工作目录（task 2502.05832_compression_ood）

复现论文 arXiv:2502.05832「班级不平衡下少样本模型压缩的损害（CIFAR-10 部分）」，
验证两个可证伪表述：(a) 等总样本量下长尾不平衡压缩学生的 top-1 显著低于平衡（Δ≥1pp）；
(b) 方向在 N=10/50/100 多档一致。

## 结论速览

- **(a) supported**：N=50 Δ=−4.11pp（6/6 重复）、N=100 Δ=−5.36pp（6/6 重复），方向正确且 ≥1pp。
- **(b) partially_supported**：N=50/100 共 12/12 重复方向一致；N=10 处于噪声层（均值 −1.06pp，4/6 负）。

详情见 `solution.md`（结论）与 `report.md`（完整方法、防泄漏、局限性）。

## 目录结构

```
agent_solution/
├── solution.md            # 结论与方法摘要
├── report.md              # 完整复现报告
├── scripts/               # 01..09 + run_all.sh（全部可运行、固定种子）
├── results/
│   ├── evidence_table.csv      # 必交证据表（config/n_per_class/n_train_total/method/top1_acc/delta_pp + N + seed）
│   ├── metrics.json            # 聚合统计与结论
│   ├── per_class_counts.csv    # 逐类样本量表（seed=42）
│   ├── subsets_summary.json    # 全 6 种子逐类表
│   ├── data_verification.json  # B 抽查点 1：train5000/类 test1000/类、32×32×3
│   ├── teacher_metrics.json    # 教师训练曲线
│   ├── per_class_accuracy.json # 逐类 top-1 机制分解
│   ├── eval_all.json           # 独立复算核验（B 抽查点 3）
│   └── students/<config>_N<N>_seed<s>/{student.pt,metrics.json}   # 36 个学生
├── models/teacher_vgg16.pt     # 教师权重（134.2M）
├── figures/                    # teacher_curve / kd_acc_delta / per_class_counts
└── evidence/                   # 关键证据导出副本
```

## 一键复现

```bash
bash scripts/run_all.sh            # 0 核验 → 1 子集 → 2 教师 → 3 KD(36 run) → 4 证据 → 5 复算核验 → 6 图 → 7 逐类
# 可选环境变量：
#   FROZEN_CIFAR10_DIR=...  # 指向 data/cifar-10-batches-py（默认用 ../data/cifar-10-batches-py）
# 教师训练默认用 GPU；KD 学生训练默认 auto（GPU 可用即 GPU）。
```

各脚本职责：
- `01_verify_data.py`  冻结 pickle 解码核验（train/test 每类计数、形状）。
- `02_prepare_subsets.py`  平衡/长尾子集构造（6 种子，等总量 10N）→ per-class 表。
- `03_train_teacher.py`  VGG-16-BN 从头训练（200 epoch SGD+cosine）→ teacher_vgg16.pt。
- `04_compress_kd.py`   单配置 logit KD 压缩（T=4、α=0.6、StudentNet 1.24M）+ test 最终评估。
- `05_run_kd_all.sh`    36 个 run 编排。
- `06_build_evidence.py` evidence_table.csv / metrics.json。
- `07_evaluate.py`      独立重加载全部 checkpoint 在冻结 test 上复算（防抄数核验）。
- `08_figures.py`       图表。
- `09_perclass_analysis.py` 逐类准确率机制分析。

## 环境

Python 3.12、PyTorch 2.11(+cu128)、torchvision 0.26、numpy、matplotlib、PIL、sklearn。
离线环境；无任何联网下载。全部随机性固定种子（子集 42/7/2024/5/8/13、学生初始化 0、DataLoader seed=子集 seed）。