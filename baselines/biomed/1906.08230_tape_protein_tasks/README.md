# agent_solution — TAPE 蛋白质工程任务论断验证

复现并验证 Rao et al., *Evaluating Protein Transfer Learning with TAPE* (NeurIPS 2019,
arXiv:1906.08230) 的核心论断：自监督预训练表示在 Fluorescence / Stability 两个蛋白质工程
下游任务上的测试集 Spearman ρ 显著优于 one-hot 等手工编码基线。

## 结构

```
agent_solution/
├── claim.md            # 论断判定（四档标签 + 关键数字）
├── solution.md         # 方法与结果摘要
├── report.md           # 完整报告（方法/结果/局限/与论文对照）
├── data/               # 冻结 TAPE 数据副本（与 F:\dataset 一致，哈希校验通过）
├── code/
│   ├── config.py               # 路径与公共配置（固定种子 42）
│   ├── dataset_stats.py        # A1: 数据统计 + train/test 结构核验
│   ├── embed_esm.py            # ESM-2 平均池化 embedding（t6_8M 与 t33_650M）
│   ├── featurize_per_position.py  # ESM-2 650M 逐残基 hidden states（fp16 memmap）
│   ├── regression_head.py      # one-hot/组成 基线 + ESM embedding 回归头 + 评估
│   ├── train_seq_head.py       # 位置敏感 1D-CNN 头（对齐论文的注意力/LSTM 头）
│   ├── make_metrics.py         # 由 evidence_table.csv 汇总 metrics.json 与判定
│   ├── make_figures.py         # evidence/figures/*.png
│   └── run_all.sh              # 一键全流程
├── results/
│   ├── evidence_table.csv      # 每任务×每表示一行：spearman_rho, rmse
│   ├── metrics.json            # 样本统计、各方法 ρ、Δρ、论文锚、结论标签
│   ├── dataset_stats.json      # 数据规模与划分结构
│   ├── test_predictions_*.csv  # 逐样本预测（可复核 Spearman）
│   └── embeddings/, seqcache/  # 中间表示缓存
└── evidence/
    ├── figures/*.png           # ρ 对比、标签分布、预测散点
    └── regress.log, featurize.log  # 运行日志
```

## 运行

```bash
cd code
bash run_all.sh          # 顺序执行：统计 → 嵌入 → 回归头/基线 → 评估 → 图
# 可选附加（位置敏感头，增强预训练表示）：
python3 train_seq_head.py --task fluorescence
python3 train_seq_head.py --task stability
```

依赖：python3 3.12，numpy/pandas/scipy/scikit-learn/torch(≥2.x)/transformers(≥4.45)。
ESM-2 权重从本地 HuggingFace 缓存加载（`facebook/esm2_t6_8M_UR50D`,
`facebook/esm2_t33_650M_UR50D`）；如无缓存且可联网，transformers 会自动下载。
数据路径自动解析（`data/` → 任务目录 → `F:\dataset\...`），也可用环境变量
`TAPE_DATA_DIR` 覆盖。embedding 计算使用 GPU（fp16）；回归头/基线训练轻量，CPU 可跑。

## 核心结果（测试集 Spearman ρ）

| 任务 | 手工编码最佳 | ESM-2 预训练最佳 | Δρ |
|---|---|---|---|
| Fluorescence | ~0.70 (one-hot ridge) | ~0.9x (ESM-2 650M 位置敏感头/MLP) | > +0.1 |
| Stability | ~0.58 (aa-comp GBDT) | ~0.77 (ESM-2 650M MLP/CNN头) | > +0.15 |

完整数字见 `results/evidence_table.csv` 与 `solution.md`。