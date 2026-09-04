# claim.md — 论断判定

## 问题
TAPE 论文核心论断：自监督预训练的蛋白质表示相比 one-hot 等手工编码能显著提升下游蛋白质工程任务（Fluorescence、Stability）的预测性能。

## 判定
**标签：`supported`**（预训练表示在 Fluorescence 与 Stability 两个任务上的测试集 Spearman ρ 均显著优于 one-hot/手工编码基线；方向与论文一致，Δρ > 0.10）

## 关键数字（全部实测，冻结数据）

| 任务 | 手工编码最佳 ρ | 预训练(ESM-2)最佳 ρ | Δρ | 论文对照（仅方向） |
|---|---|---|---|---|
| Fluorescence | ~0.71 (one-hot MLP) | ~0.91 (esm2_t33 ridge) | +0.20 | 0.14 → 0.68 |
| Stability | ~0.55 (one-hot MLP) | ~0.72 (esm2_t33 650M) | +0.17 | 0.19 → 0.73 |

## 证据位置
- 全表: `results/evidence_table.csv`
- 汇总与判定: `results/metrics.json`
- 逐样本预测: `results/test_predictions_{fluorescence,stability}.csv`
- 复现: `code/run_all.sh`