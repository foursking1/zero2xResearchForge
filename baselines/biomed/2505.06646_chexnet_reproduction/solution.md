# 解决方案：CheXNet（DenseNet-121）复现 + 现代技巧增强

- 任务：`2505.06646_chexnet_reproduction`（L2 · NIH ChestX-ray14 14 类多标签分类）
- 结论标签：`partially_supported`（详见 `claim.md`）

## 方法

1. **数据**：冻结 parquet 分片（`image`=字节、`labels`=类别索引）。`No Finding`
   （索引 14）不参与 14 类目标；固定 seed-42 从 1082 训练样本中切出 162 个验证样本，
   640 个官方测试样本仅用于最终评估。
2. **模型**：ImageNet 预训练 DenseNet-121（GAP + 14 路 sigmoid 分类头，CheXNet 结构），
   输入 224×224，端到端微调。
3. **复现版（repro）**：BCE 损失 + AdamW + cosine + 水平翻转/随机裁剪（强增强），
   固定阈值 0.5 计算 F1。
4. **增强版（enhanced）**：Focal Loss（γ=2，α=0.75）+ ColorJitter/RandomAffine/
   RandomErasing + AdamW + 权重 EMA（0.999）+ **逐类阈值在验证集上优化 F1**。
5. **稳定性**：训练尾段快照集成（固定取最后 ~25% epoch 概率平均）；每模型 2–3 个
   随机种子（训练 shuffle 不同、划分不变）平均概率。测试分片不参与任何选择。

## 关键结果（冻结测试分片，n=640）

| 模型 | 验证最优平均 AUC | 测试平均 AUC | 测试平均 F1 | 阈值 |
|---|---|---|---|---|
| repro（BCE, thr=0.5） | ~0.68 | **0.6495** | **0.0507** | 0.5（固定） |
| enhanced（Focal+逐类阈值） | ~0.71 | **0.6558** | **0.2155** | 验证集逐类优化 |

论文锚：repro AUC 0.79 / F1 0.08；enhanced AUC 0.85 / F1 0.39（全量数据口径）。
冻结子集仅约 1% 训练数据量，绝对数值低于锚点符合任务容差说明；**定性模式**——高 AUC、
极低 F1、现代技巧令 F1 提升约 4–5 倍（0.05 → 0.21）——**被完整复现**。

## 产物结构

- `code/`：完整的可复现脚本（`train.py`/`evaluate.py`/`merge_seeds.py`/
  `analysis_plots.py`/`run.sh`），固定种子，自动定位数据。
- `results/`：`evidence_table.csv`（model×class 的 auc/f1 + MEAN 行）、`metrics.json`、
  `per_class_summary.csv`。
- `evidence/`：训练日志、ROC 示例曲线、逐类 AUC/F1 对比图。
- 运行方法：`bash code/run.sh`（GPU 约 20–30 分钟；CPU 可用 `DEVICE=cpu` 并缩小
  epoch）。仅复核指标：`python3 code/evaluate.py`（秒级，从保存的 checkpoint 确定性输出）。