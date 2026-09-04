# Solution — 2604.08131_gnn_misinfo

## 任务与方法（一句话）

在冻结的 WELFake 全量语料（`dropna(text)` 后 72,095 条，原本 72,134 条）上，按论文统一管线
（分层 80/10/10、seed 42；TF-IDF max 5000 仅 train 拟合；train-only k-NN 相似图 K=5 —— 与
`torch_geometric.nn.knn_graph` 语义一致的精确最近邻；GraphSAGE (SAGEConv mean, 256→128) vs
MLP (256→128)，Adam lr=1e-3，val-F1 早停 patience=10，≤200 epochs，3 种子平均），复现并检验
"GNN 显著优于强非线性传统基线"这一 critical claim。

## 核心结果

| 指标 | GraphSAGE | MLP | 论文锚 | 判定 |
|---|---|---|---|---|
| test F1（3 种子 mean±std） | **92.10 ± 0.04 %** | **92.87 ± 0.02 %** | 91.9 / 66.8 | A1 复现；A2 不复现 |
| test n | 7210 | 7210 | — | 与 72,095 规模一致 |
| f1_gap_pp (GNN − MLP) | **−0.77 pp** | | +25.1 pp | 方向与幅度均不符 |

- 结论投票：claim (a) GraphSAGE≈91.9 **supported**；claim (b) GNN 领先 ≥15pp
  **contradicted**；claim (c) GNN>MLP 方向 **contradicted**（强基线 MLP 反而略高）。
- 论文 MLP 锚（66.8±29.1）在任意公平设定下都无法复现：full-batch 收敛 → 92.87%；
  200-step 小批量预算 → 93.90%；sklearn MLPClassifier → 95.92%。三档均接近/超过 GNN，
  且跨种子方差远小于论文所报 ±29.1 pp。⇒ 论文 ~25pp 差距源于基线欠训练/不稳定，
  而非图归纳偏置在 WELFake 上的真实优势。
- 鲁棒性：改用 cosine 度量构建 k-NN 图后 GraphSAGE F1 = **91.91 ± 0.07%**，
  与 euclidean（92.10%）一致地复现论文 91.9 锚值。

## 提交物清单

- `code/pipeline.py` —— 端到端复现管线（读冻结 CSV → 划分 → TF-IDF → k-NN 图 →
  GraphSAGE/MLP 训练 3 种子 → 证据表）。CPU-only，固定随机种子，防泄漏设计。
- `code/probe_mlp.py` —— MLP 基线训练制度探针（200-step / sklearn）。
- `code/verify_evidence.py` —— 由保存的预测独立用 sklearn 重算 F1，校验证据表（评委快速核查）。
- `code/analyze_results.py` —— 生成图表与结论。
- `results/evidence_table.csv`（必需列：model/split/n/f1/precision/recall/f1_gap_pp）、
  `metrics_perseed.csv`、`metrics_aggregate.csv`、`metrics_probes.csv`、`predictions*.csv`（3 种子逐样本预测）、
  `history_*.csv`、`splits/*`（train/val/test 索引）、`all_models_summary.csv`。
- `results_cosine/` —— 鲁棒性：cosine 度量 k-NN 图的 GraphSAGE 复现（91.91%）。
- `evidence/` —— 关键证据导出（证据表、各汇总表、预测、图表）。
- `data/welfake/WELFake_Dataset.csv`（冻结数据副本，sha256 校验通过）。

## 复现命令

```bash
cd agent_solution
python code/pipeline.py --out results --seeds 0,1,2 --max-epochs 200 \
    --models both --verify-sha        # 主协议约 40–60 CPU 分钟
python code/probe_mlp.py --only mlp_200step --seeds 0 1 2   # MLP 200-step 探针
python code/probe_mlp.py --only mlp_sklearn --seeds 0 1 2   # sklearn 参考
python code/verify_evidence.py --results results             # 证据表校验（快）
python code/analyze_results.py --results results             # 图表 + 结论
```

数据路径解析顺序：`--csv` → 环境变量 `WELFAME_CSV` → `agent_solution/data/welfake/**` →
`/mnt/f/dataset/cs/2604.08131_gnn_misinfo/data/welfake/**`。

## 关键设计（防泄漏）

1. TF-IDF 词表/idf 仅对 train 拟合，val/test 用同一向量器 transform。
2. k-NN 图仅用 train 节点特征构建；val/test 作为孤立节点（单位邻接）推理，
   测试节点特征从不参与建图/归一化。
3. 早停与选模仅用 val；test 仅在最终评估使用一次。
4. 全流程固定随机种子（划分 seed 42 + 训练种子 0/1/2）。