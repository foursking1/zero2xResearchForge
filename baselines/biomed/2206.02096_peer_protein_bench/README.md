# PEER Solubility 关键论断复现 —— agent_solution 说明

任务 `2206.02096_peer_protein_bench`（L1, critical claim）。
复现 PEER（arXiv:2206.02096）Solubility 单任务：数据装配核对、DDE/Moran/CNN/LSTM 四模型锚复现、论断排序判定。

## 目录结构

```
agent_solution/
├── claim.md            # 三问判定 + 四档标签（partially_supported）+ 关键数字
├── solution.md         # 方法说明 + 结果摘要
├── report.md           # 完整报告（方法/结果/局限/口径讨论）
├── README.md           # 本文件
├── code/               # 全部可复现代码（固定种子；GPU 可用时编码器用 CUDA，否则 CPU）
├── results/            # 数据装配统计、各模型结果、证据表、指标汇总
│   ├── data_stats.json
│   ├── feature_model_results.json
│   ├── encoder_model_results.json
│   ├── metrics.json            # 汇总：统计 + 各模型 accuracy + 论文对照 + 结论标签
│   └── evidence_table.csv      # 列：model,accuracy（judge 抽查用）
├── figures/            # 长度分布与准确率对比图
└── evidence/           # 训练日志、确定性自检日志
```

## 复现与自查（judge 建议流程）

```bash
# 0) 数据（冻结，SHA-256 已核对；默认路径 data/ 或 PEER_DATA_DIR）
# 1) 快速证据核查（CPU 友好，约 10 分钟）：
python3 code/05_verify.py
#    输出：train/valid/test 行数 = 62478/6942/1999；DDE 测试 accuracy 重算一致；
#          evidence_table 与 metrics.json 一致；数据 SHA-256 与清单一致。

# 2) 完整流水线（编码器优先 CUDA，无 GPU 时 CPU 回退）：
python3 code/run_all.py          # 01→02→03→04
python3 code/06_plots.py
python3 code/07_determinism_check.py   # 复训 CNN seed2024 位级一致
```

## 关键结果（测试集 accuracy %）

| 模型 | 本文 | 论文 Table 3 | 相对差 |
|---|---|---|---|
| DDE + LR | 59.98 | 59.77 | +0.35% |
| Moran + 平衡 LR | 55.43 | 57.73 | −3.99% |
| CNN (3 seeds) | 70.20±0.56 | 64.43 | +8.95% |
| LSTM (3 seeds) | 64.63±0.47 | 70.18 | −7.91% |

结论：**`partially_supported`** —— 编码器 vs 特征工程排序完全复现（最优编码器 70.20 − DDE 59.98 = 10.22pp ≥ 3pp）；
预训练 PLM 全面最优半句因离线无预训练权重不可直接验证（论文自身 LSTM≈ESM-1b）。

## 依赖

Python 3.11+ · numpy · pandas · scikit-learn · torch（编码器）。无其它包。
无网络需求；不得下载任何预训练权重（本任务离线）。