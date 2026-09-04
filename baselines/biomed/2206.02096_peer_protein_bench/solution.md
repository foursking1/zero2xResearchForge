# solution.md — 方法说明与结果摘要

## 1. 任务与数据

- 复现目标：PEER（arXiv:2206.02096）Solubility 单任务分类关键论断验证（L1 critical claim）。
- 冻结数据：`data/solubility_{train,valid,test}.csv`（SHA-256 与清单一致）。
  train 62,478 / valid 6,942 / test 1,999；二分类（1=可溶）；指标 accuracy（%）。
- 数据卫生：测试集仅用于最终评估一次；DDE/Moran 统计量与标准化均值/方差只由 train 拟合；所有超参（LR 的 C、编码器早停）只用 valid。

## 2. 实现的方法（`code/`，全部固定种子，可重跑）

| 脚本 | 内容 | 模型 |
|---|---|---|
| `01_data_stats.py` | 样本/类别/长度统计 → `results/data_stats.json` | 数据装配 |
| `02_feature_models.py` | DDE(400d)+LR；Moran(10 理化指标×5 滞后=50d)+平衡 LR，valid 网格选 C | 特征工程族 |
| `03_encoder_models.py` | CNN 与 BiLSTM 从零训练：Emb(128)→卷积池化/双层 BiLSTM→池化→MLP；截断 512；AdamW；valid 早停；3 seeds | 从零训练编码器族 |
| `04_assemble_results.py` | 汇总 → `results/metrics.json`、`results/evidence_table.csv`、四档标签 | 交付物 |
| `05_verify.py` | 复算 test 行数、DDE 测试准确率、SHA-256 → ALL CHECKS PASSED | 证据核查 |
| `06_plots.py` | `figures/*.png`（长度分布、准确率对比） | 图表 |
| `07_determinism_check.py` | 复训 CNN seed2024，比对位级一致 | 可复现性自检 |

设备：编码器用 CUDA（RTX 4080；代码在无 GPU 时自动回退 CPU）；特征模型纯 CPU。
确定性：全局种子 + `cudnn.deterministic=True` + `DataLoader(num_workers=0)`（多 worker 会乱序导致不可复现），`07` 验证位级一致。

## 3. 结果（测试集 accuracy %）

| 模型族 | 模型 | 本文实测 | 论文 Table 3 | 相对差 |
|---|---|---|---|---|
| 特征工程 | DDE + LR | 59.98 | 59.77 | +0.35% |
| 特征工程 | Moran + 平衡 LR | 55.43 | 57.73 | −3.99% |
| 从零训练编码器 | CNN（3 seeds mean±std） | 70.20 ± 0.56 | 64.43 | +8.95% |
| 从零训练编码器 | LSTM（3 seeds mean±std） | 64.63 ± 0.47 | 70.18 | −7.91% |

编码器最优（70.20）− 特征工程最优（59.98）= **10.22 pp ≥ 3 pp** →「从零训练编码器 > 特征工程」完全复现。
CNN/LSTM 每 seed：69.43/70.74/70.44 与 64.03/65.18/64.68。

## 4. 结论

四档标签：**`partially_supported`**
- 「从零训练编码器 > 特征工程」：supported（差 10.22pp，方向与量级与论文一致）。
- 「预训练 PLM 全面最优」：离线无预训练权重（ESM-1b/ProtBert 不可得），无法直接实证；论文自身显示 LSTM 与 ESM-1b 持平，本文未发现矛盾证据 → 该半句不可验证。

局限：未运行 ESM-1b/ProtBert（离线无权重）；编码器实现与 PEER torchdrug 管线有差异（超参/截断），但族间排序不受影响。详见 `report.md`。

## 5. 复现命令

```bash
cd agent_solution/code
python3 run_all.py        # 01→02→03→04（编码器优先 CUDA，无则 CPU）
python3 05_verify.py      # 自检：ALL CHECKS PASSED
python3 06_plots.py       # 图表
python3 07_determinism_check.py
```

依赖：Python 3.11+，`numpy`、`pandas`、`scikit-learn`、`torch`。数据目录：默认 `data/`（或环境变量 `PEER_DATA_DIR`）。