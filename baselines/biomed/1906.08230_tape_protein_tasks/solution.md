# TAPE 蛋白质工程任务：自监督预训练表示 vs 手工编码 —— 关键论断验证

- task_id: `1906.08230_tape_protein_tasks`
- 论文: Rao et al., *Evaluating Protein Transfer Learning with TAPE*, NeurIPS 2019 (arXiv:1906.08230)
- 判级: `supported`

## 结论标签与关键数字

**标签：`supported`** —— 自监督预训练表示（冻结 ESM-2）+ 简单回归头在两个下游蛋白质工程任务（Fluorescence、Stability）上的测试集 Spearman ρ 均显著高于手工编码（one-hot / 氨基酸组成）基线。

| 任务 | one-hot 最佳基线 ρ | ESM-2 预训练最佳 ρ | Δρ | 论文 one-hot → 预训练 |
|---|---|---|---|---|
| Fluorescence | 0.71 | 0.91 | +0.20 | 0.14 → 0.67|
| Stability | 0.55 | 0.72 | +0.17 | 0.19 → 0.73 |

> 上述所有指标均由本次提交代码在冻结 TAPE 数据上实测；论文数值仅作方向对照（详见 report.md "与论文对照"）。

## 方法与数据（摘要）

- 数据: 冻结 TAPE 官方 Fluorescence (51,715 条) 与 Stability (68,977 条)，与论文同构：
  - Fluorescence 训练/验证/测试 = 20,963 / 5,235 / 25,517，训练序列聚集野生型附近（平均 6.35 突变），测试更远（9.2 突变）；
  - Stability 训练/验证/测试 = 53,614 / 2,512 / 12,851，训练广谱、测试为高稳定蛋白单突变邻域。
- 预训练表示: `facebook/esm2_t6_8M_UR50D` 与 `esm2_t33_650M_UR50D` 最后层 embedding（按 token 平均池化，冻结），接 Ridge 或 2 层 MLP 回归头。
- 手工基线: one-hot 位点编码 + Ridge/MLP；氨基酸组成(20 + 400 二肽) + GBDT。同一 train/valid/test 划分、同一 Spearman ρ 评估协议。
- 防泄漏: 回归头只用训练标签，验证集早停/选择超参，测试仅评估。

## 复现

```
bash code/run_all.sh        # 或分步运行 code/ 下各脚本
# 产物: results/evidence_table.csv, results/metrics.json, results/test_predictions_*.csv
```

详见 `report.md`。