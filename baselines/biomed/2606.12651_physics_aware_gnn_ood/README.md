# agent_solution — 物理感知 GNN OOD 泛化论断复现（2606.12651_physics_aware_gnn_ood）

评价入口文件：
- **`claim.md`** — 三问判定与结论标签（`partially_supported`）
- **`report.md`** — 完整报告（方法/结果/局限）
- **`solution.md`** — 方法摘要与结果速览

## 目录结构
```
agent_solution/
├── code/            # 完整可复现脚本（固定种子）
│   ├── config.py           # 路径与超参
│   ├── data_pipeline.py    # SAScore 标签 / 图特征 / complexity & strain 辅助目标
│   ├── model.py            # 纯 PyTorch GINE + 辅助头（无 torch_geometric 依赖）
│   ├── train_eval.py       # 变体×种子训练 + COCONUT OOD AUC
│   ├── analyze.py          # 配对 bootstrap CI → evidence_table.csv / metrics.json
│   └── run_all.sh          # 一键复现（--quick / 默认 / --sensitivity）
├── results/         # raw_evals|evidence_table.csv, metrics.json, label_stats.json,
│                    # regime1_posw/（主协议）、regime2_plaince/（敏感性）
├── evidence/        # evidence_table.csv
├── cache/           # corpus_features.pkl（中间特征，无 RDKit 时复现亦一致）
├── claim.md / report.md / solution.md
```

## 环境
- Python 3.12/3.13；依赖：numpy、pandas、pyarrow、torch（CPU 亦可）、sklearn（仅 AUC 交叉验证）、RDKit（可选）。
- RDKit 仅用于 SAScore / 特征 / 辅助目标计算；**缺失时自动回退**到冻结 `data/*_sascore.parquet` 与 `cache/corpus_features.pkl`，结果一致。
- 训练默认自动使用 GPU（CUDA）；不可用时回退 CPU。

## 一键复现
```bash
cd code
bash run_all.sh            # 完整主协议（协议 A）：4 变体 × 5 seeds（~30–60 min；GPU 自动）
bash run_all.sh --quick    # 快速冒烟：baseline+complexity × 1 seed × 8 epochs
bash run_all.sh --sensitivity  # 协议 A + 敏感性协议 B（plain-BCE, λ=0.5）
```

或分步：
```bash
python data_pipeline.py                       # 标签 + 特征 + 辅助目标
python train_eval.py --variants baseline complexity strain both \
       --seeds 0 1 2 3 4 --device cuda --out raw_evals.json
python analyze.py                              # 统计 + evidence_table + metrics.json
python verify_report.py                        # 快速核验（无需重训）
```

数据放回 `data/` 之后，`python verify_report.py` 可在数秒内核验标签分布、
基线 AUC 与 bootstrap CI 与 `results/` 一致。

## 输入数据（勿动，冻结）
`../data/`：`HIV.csv`、`tox21.csv.gz`、`COCONUT_30k_seed42.csv`（checksum 见 `data/README.md`）