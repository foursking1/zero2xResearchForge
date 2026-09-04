# 论文锚：1906.08230_tape_protein_tasks

> 用途：LLM judge 判分基准（私有）。数值来自 arXiv:1906.08230v2（NeurIPS 2019），禁止臆造。

## 锚清单

| # | 指标 | 论文数值 | 出处 | 定义口径 | 容差 |
|---|---|---|---|---|---|
| 1 | Fluorescence Spearman ρ | one-hot 0.14；No-Pretrain ResNet -0.28 / LSTM 0.21；Pretrain Transformer 0.68 / LSTM 0.67 / ResNet 0.21；UniRep 0.67；Supervised LSTM 0.33 | Table 2 | 测试集 Spearman ρ | 方向锚（预训练 ≥ one-hot；±0.10 判一致） |
| 2 | Stability Spearman ρ | one-hot 0.19；No-Pretrain ResNet 0.61；Pretrain Transformer 0.73 / LSTM 0.69 / ResNet 0.73；UniRep 0.73 | Table 2 | 测试集 Spearman ρ | 方向锚 |
| 3 | 主论断 | 「自监督预训练提升几乎所有下游任务；蛋白工程任务上提升显著」 | §Results / Abstract | 方向性 | 方向 |
| 4 | 数据规模 | Fluorescence 训练集 ~21,446 / 测试 ~27,251（GFP 突变体）；Stability 训练集 ~53,680 / 测试 ~15,100 | §Task 4/5 | 与冻结 CSV 核验 | ±1% |

## 备注
- 主论断：预训练表示在蛋白工程（荧光/稳定性）任务上显著优于 one-hot；本卡冻结数据为 TAPE 官方荧光+稳定性子集（同源）。
- 判分提示：以「预训练表示 ρ ≥ one-hot（两任务）」方向为主判据；绝对数值受嵌入模型/实现影响，不强求复现论文绝对 ρ。
