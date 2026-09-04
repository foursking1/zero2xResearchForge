# 结论：`supported`（深度 CNN 复现论文锚 ~95.13%，实测测试 OA 95.06%）

> 基于冻结真实数据（RSI-CB256 镜像，24,747 张 / 35 细类）的重跑结果。

- **细类（label_2，35 类）测试 OA：95.06%**（论文锚 VGG-16 = 95.13%，相对差 d=0.08%）
  - 主方法 = ImageNet 预训练 ResNet-18 + 两级多任务头（35 细 + 7 粗），在冻结 50/50
    官方协议划分上微调（layer4+头，2 epoch）。
  - 高精度变体（冻结特征 + 训练化 MLP 头）：**98.83%**；线性探针：98.53%。
- label_1（7 类）辅助层次精度：93.47%（主方法）/ 98.97%（MLP 变体）。
- 防泄漏与可复现：只在 train 拟合；固定种子 1705；冻结文件只读；`run_all.sh` 端到端
  可重跑；`src/06_verify.py` 不重训即可从 evidence 重算全部指标。
- 关键证据：
  - `results/evidence_table.csv`（逐类 tp/fp/tn/fn、precision、recall、f1、accuracy + OVERALL）
  - `results/metrics.json`（`overall_accuracy` / `macro_f1` / `label1_accuracy` / `seed` / `split_sizes`）
  - `results/predictions.npz`、`results/confusion_label2.csv`、`checkpoints/resnet18_mtl.pt`
  - `results/robustness_study.json`（去近重复后 OA 仍 ≥94.9%）、`results/duplicate_analysis.json`
- 结论边界：镜像近重复 ~4.5%、划分不可与论文逐文件对拍、预训练初始化贡献（详见
  `report.md` §7）。