# agent_solution — MIDOG2022 有丝分裂分类验证（2508.04441_mitotic_benchmark）

目录结构：

```
agent_solution/
├── claim.md                  # 三问判定 + 关键数字 + 结论标签（supported）
├── solution.md               # 方法说明 + 结果摘要 + 复现（精简版）
├── report.md                 # 完整报告：方法/结果/图表/局限/复现
├── code/
│   ├── paths.py              # 冻结数据定位（兼容 data/ 与物理数据盘）
│   ├── 01_parse_annotations.py   # COCO 解析 + patch 裁剪 + 统计
│   ├── 02_extract_features.py    # ResNet18/ViT-B16 冻结特征（4 旋转）
│   ├── 03_train_classify.py      # LinProbe/MLP, 10% vs 100%, bagged CV
│   ├── 04_make_figures.py        # evidence/*.png
│   ├── 05_finetune_cnn.py        # 可选：layer4+fc 微调适配头
│   ├── 06_gather_metrics.py      # 汇总 metrics.json + 结论
│   └── run_all.sh                # 一键复现
├── results/
│   ├── annotations_stats.json    # 子集/全量统计（62 MF / 91 HN）
│   ├── evidence_table.csv        # model,data_fraction,balanced_acc,weighted_f1,auroc
│   ├── metrics.json              # 汇总 + 论文锚对照 + 结论标签
│   ├── fold_predictions.csv      # 逐 patch 池化预测（可重算）
│   ├── classifier_detail.json    # 各配置指标明细
│   ├── patches.npz / features.npz  # 裁剪与特征中间数据
└── evidence/                     # 4 张图表
```

如何运行：

```bash
cd agent_solution
bash code/run_all.sh
```

要点：全部指标由代码计算；固定随机种子；最优模型 Weighted F1 = **0.615**
（ResNet18 冻结特征 + 线性探测，100% 数据），10% vs 100% ΔF1 = **0.088**（≤ 0.15），
子集标注 62 有丝分裂 / 91 难例。结论标签：`supported`。

依赖：`python3` · `numpy` · `torch`(`torchvision`) · `scikit-learn` · `Pillow` · `matplotlib`，
模型权重由本地 torch hub cache 提供（无需联网）。