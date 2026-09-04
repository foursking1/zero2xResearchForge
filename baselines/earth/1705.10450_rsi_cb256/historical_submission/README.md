# submission — task 1705.10450_rsi_cb256（RSI-CB256 深度 CNN 场景分类复现）

> 裁判/读者导航：本目录是 TASK.md 要求的标准提交结构；完整工程（含 4GB 缓存）位于
> 上级 `agent_solution/`。两者内容一致。

## 结论速览（详见 report.md）

- **结论：`supported`** — 冻结真实数据上，微调 ResNet-18 深度 CNN 的 label_2（35 细类）
  测试 **OA = 95.06%**，与论文锚 VGG-16 95.13% 几乎等同（相对差 d = 0.08%）。
- 高精度变体（ImageNet 预训练特征 + 训练化 MLP 头）= 98.83%；线性探针 = 98.53%。
- 去近重复（cos≥0.99 剔除 4.5% 测试样本）后主方法 OA 94.86% —— 结论稳健。

## 目录

- `report.md` / `solution.md` — 完整报告与方法说明
- `src/` — 全部源代码（`run_all.sh` 一键复现）
- `results/` — 证据表、指标、预测、混淆、数据统计
  - `evidence_table.csv`、`metrics.json`、`predictions.npz`、`confusion_label2.csv`、
    `confusion_top_pairs.csv`、`data_stats.json`、`duplicate_analysis.json`、
    `robustness_study.json`、`features_resnet18_224.npz`（缓存特征）、`variant_mlp/`
- `evidence/` — 关键证据副本（表/指标/预测/2 张图/checkpoint）
- `checkpoints/resnet18_mtl.pt` — 主模型权重

## 快速复核（裁判抽查路径）

```bash
cd agent_solution
python3 src/06_verify.py        # 从 evidence/predictions.npz 重算 OA / macro-F1 / 单类指标（<1 min）
python3 src/11_study.py         # 去近重复稳健性
head -3 results/evidence_table.csv
```

全流程重算（从冻结 parquet 开始，CPU 约 4–6 h）：

```bash
cd agent_solution && bash run_all.sh
```