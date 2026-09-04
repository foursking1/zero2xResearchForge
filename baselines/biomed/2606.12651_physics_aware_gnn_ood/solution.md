# solution.md — 方法摘要与结果

本方案对论文 arXiv:2606.12651 的核心论断（物理感知 GINE 辅助损失在 COCONUT 单源 OOD 上显著提升 easy/hard 二分类 ROC-AUC）进行完整复现验证，结论标签：**`partially_supported`**。

## 复现流程（全部可重算，`code/` 内固定种子）

1. **标签（SAScore 阈值）**：`data_pipeline.py` 从原始 SMILES 用 RDKit sascorer 计算 SAScore，`<4→easy(label=1)`，`>5→hard(label=0)`，`[4,5]` 丢弃；无 RDKit 时回退读取冻结 `data/*_sascore.parquet`（已验证两路径结果一致）。
2. **图特征**：27 维原子 / 5 维键特征；连续图块组成的纯张量数据集。
3. **物理辅助目标**：complexity = log(BertzCT+1)（训练均值 6.458，σ 0.748）；strain = UFF 2D 初始到松弛的能量降（max(0,ΔE)，失败率 1.2%），均按训练侧 z-score 标准化。
4. **GINE**（纯 PyTorch，无 torch_geometric 依赖）：3 层 GINE(64) + mean/max 池 + 分类头；辅助 MSE 头（λ=0.1）。
5. **划分**：train/val 仅 HIV+Tox21（固定 10% 验证），**COCONUT 仅作 OOD 测试**；5 个种子；验证 AUC 早停 + 最优模型。
6. **统计**：配对 Δ（变体−baseline 同 seed）；5 个 Δ 重采样 10,000 次 bootstrap 95% CI。

双协议：**A**（默认，pos_weight=True、λ=0.1，主报告数字）；**B**（敏感性，`--pos_weight 0 --aux_w 0.5`）。

## 结果（主协议；5 seeds）

| 指标 | 实测 | 论文 | 判定 |
|---|---|---|---|
| 基线 mean OOD AUC | **0.98521** | 0.9774 | 相对差 +0.80% ≤5%（A1 ✓） |
| +complexity Δ | −0.00115（CI [−0.00547,+0.00376]） | +0.0060 | 未达到显著 |
| +strain Δ | +0.00151（CI [−0.00132,+0.00444]） | +0.0032 | 方向对，CI 含 0 |
| **+both Δ** | **+0.00243（CI [+0.00094,+0.00393]，不含 0）** | +0.0066（[+0.0038,+0.0093]） | **显著且同向，组合最优（A2 ✓）** |
| easy/hard 分布 | **53,552/12,009（81.7/18.3）** | 53,159/12,018（82/18） | 相对差 ~0.4% ≤15%（A3 ✓） |

敏感性（协议 B，plain-BCE、λ=0.5）：+both Δ=−0.0033（显著为负）、+complexity Δ=−0.0039 → 效应协议依赖、不鲁棒。

## 判定
- **Q1 基线复现**：支持（0.98521，≤5%）。
- **Q2 消融对比**：至少一个变体（+both，协议 A）Δ 为正且 CI 不含 0 → 支持；但 +complexity/+strain 未显著、协议 B 反转，更强叙述仅部分支持。
- **Q3 标签忠实性**：支持（81.7/18.3 ≈ 82/18）。
- **结论：`partially_supported`**

## 产物
- `code/`：`config.py`、`data_pipeline.py`、`model.py`、`train_eval.py`、`analyze.py`、`run_all.sh`
- `results/`：`raw_evals.csv`、`evidence_table.csv`（variant,seed,ood_auc,delta,ci_low,ci_high）、`metrics.json`、`label_stats.json`、`regime1_posw/`、`regime2_plaince/`
- `evidence/`：`evidence_table.csv`
- `cache/corpus_features.pkl`：中间特征（356MB，用于无 RDKit 环境的确定性复现）