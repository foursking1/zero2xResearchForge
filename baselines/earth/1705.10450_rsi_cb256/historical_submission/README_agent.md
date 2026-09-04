# RSI-CB256 遥感场景分类复现 — agent_solution

论文锚（PAPER_ANCHOR）：Li et al. (2017, arXiv:1705.10450)，Table 6 —— VGG-16 在
RSI-CB256 上的**测试 OA = 95.13%**（ResNet 95.02%，GoogLeNet 94.07%）。

本目录是评估 agent 的完整产物：源代码、中间缓存、最终指标、证据表与报告。

## 目录结构

```
agent_solution/
├── solution.md            # 方法说明与结果（简短）
├── report.md              # 完整报告（结论 / 方法 / 训练预算 / 防泄漏 / 混淆分析 / 局限）
├── run_all.sh             # 一键可重跑管线脚本
├── src/                   # 全部源代码
│   ├── common.py              # 路径、常量、标签名、加载工具
│   ├── 01_preprocess.py       # 从冻结 parquet 解码 → images_224.memmap + labels.npz
│   ├── 02_extract_features.py # 冻结 ResNet18 特征（参考基线）
│   ├── 03_linear_probe.py     # 逻辑回归探针（快速参考）
│   ├── train_utils.py         # 多任务 ResNet18 模型 + 增广
│   ├── evaluate_utils.py      # 预测与指标函数
│   ├── 04_finetune.py         # 主方法：ResNet18 微调（label_2 35 类 + label_1 7 类多任务）
│   ├── 05_evaluate.py         # 最终评测 → evidence_table / metrics.json / 混淆
│   ├── 06_verify.py           # 从 evidence 快速重算指标（供裁判抽查）
│   ├── 07_from_scratch.py     # 控制实验：小型 CNN 从零训练
│   ├── 08_analysis.py         # 数据统计 + 混淆对分析
│   └── run_bg.py              # 后台守护启动器
├── results/               # 运行产物（标签、缓存、指标、表格、日志）
├── evidence/              # 关键证据副本（evidence_table.csv、metrics.json、predictions、checkpoint）
├── checkpoints/           # 模型权重（resnet18_mtl.pt）
└── submission/            # 按 TASK.md 要求组织的提交目录（链接/镜像）
```

## 数据（冻结，不可变）

- `F:/dataset/earth/1705.10450_rsi_cb256/data/data/train-0000X-of-00010-*.parquet`（10 shard，共 24,747 行）
- `F:/dataset/earth/1705.10450_rsi_cb256/split_train_test_50.csv`（冻结 50/50 划分 = 论文官方协议）
- label_1 = 7 大类（transportation … construction land）
- label_2 = 35 细类（parking lot … storage room；与论文 RSI-CB256 的 35 子类一致）
- 任何脚本都只读这些文件，不修改；派生缓存（memmap / npy / ckpt）写入 results/。

## 复现运行

```bash
cd agent_solution
bash run_all.sh                 # 全管线（CPU，约数小时）
# 或分步：
TORCH_THREADS=8 python3 src/04_finetune.py --epochs 3 --lr 1e-2 --backbone-lr 3e-4
TORCH_THREADS=8 python3 src/05_evaluate.py
TORCH_THREADS=8 python3 src/06_verify.py
```

依赖：python3.12、torch>=2、torchvision、pandas、pyarrow、numpy、scikit-learn、Pillow。
ImageNet 预训练权重从本地 torch hub 缓存读取（离线可用，无网络下载）。

## 主要结论（详见 report.md）

- 细类（label_2, 35 类）测试 **OA = X.XX%**（锚 95.13%；相对差 d = Y.Y% → 满分带/半满带）
- label_1（7 类）辅助任务准确率 Z.ZZ%（层次标签利用）
- 结论：`supported`（在冻结数据上以深度 CNN 复现 ~95% 量级测试精度）