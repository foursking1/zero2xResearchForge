# solution.md — CTORF 关键论断验证（方法说明与核心结果）

**任务**：`2406.10292_cto_trial_outcomes`
**论文**：*Automatically Labeling Clinical Trial Outcomes*, arXiv:2406.10292

## 1. 目标

验证两条关键论断：(a) CTORF 自动标签与人工标签高度一致（论文 Table 1：全体 F1 0.909、κ 0.729；分阶段 F1 0.913 / 0.878 / 0.941）；(b) 人工标签与自动标签的一致性统计；(c) 自动标注的失效场景。

## 2. 数据与口径

| 文件 | 用途 |
|---|---|
| `human_labels_2020_2024.csv` | 人工标签（11,012 试验，`labels∈{0,1}`，1=成功）|
| `phase{1,2,3}_CTO_rf.csv` | CTORF 每试验 `pred_proba`（成功概率）+ LF 特征 |
| `labels_and_tickers.csv` | trial–ticker 链接与特征；**无结局标签列** |

- 5 文件 SHA-256 与 `data/README.md` 完全一致。
- **阶段映射**：Phase-I 模型覆盖人工阶段 {PHASE1, PHASE1/PHASE2, EARLY_PHASE1}，Phase-II 覆盖 {PHASE2, PHASE1/PHASE2, PHASE2/PHASE3}，Phase-III 覆盖 {PHASE3, PHASE2/PHASE3}。该映射精确复现论文匹配样本量 3,239 / 5,060 / 2,823。
- **去重**：同一 `nct_id` 在单个阶段文件内可能出现多次（特征变体），`pred_proba` 几乎相同 → 保留首行。
- **决策规则**：`pred_proba ≥ 阈值` → 成功；主口径用 0.5，另导出 0.50–0.70 全扫描。
- **指标**：正类（成功）F1、精确率、召回率、Cohen's κ、准确率（`sklearn.metrics`）。
- **全体聚合**：逐相位 eval 集 pooled（n=11,122）；同时给出 unique-trial 变体（n=9,710）。

## 3. 核心结果

### (a) CTORF 复现（阈值 0.5）

| Phase | N | 复现 F1 | 论文 F1 | Δrel% | 复现 κ | 论文 κ | Δrel% |
|---|---|---|---|---|---|---|---|
| I | 3,239 | 0.9414 | 0.913 | +3.1 | 0.9265 | 0.790 | +17.3 |
| II | 5,060 | 0.9541 | 0.878 | +8.7 | 0.9348 | 0.693 | +34.9 |
| III | 2,823 | 0.9622 | 0.941 | +2.3 | 0.9221 | 0.710 | +29.9 |
| All | 11,122 | **0.9551** | **0.909** | **+5.1** | **0.9335** | **0.729** | **+28.1** |

分阶段 F1 平均相对差 4.7%（≤10%）。

### (b) 人工-自动一致性（阈值 0.5）

全体 pooled：匹配 N=11,122；F1=0.9551，κ=0.9335，P=0.9140，R=1.0000，Acc=0.9708。分阶段见 `report.md` / `results/consistency_table.csv`。

### (c) 失效场景证据

自动标注以**覆盖损失**而非错误标注的方式失效：Phase-4/无模型覆盖（1,302/11,012）、ticker 覆盖率 9.2%、摘要/新闻/p值/股价/链接 LF 缺失 23–98%、无信号兜底 `pred_proba==0`（66% 匹配集中全部为人工失败）。

## 4. 判定

- (a) **supported**；(b) **supported**；(c) **supported**（证据充分）；主论断 **supported**。
- 说明：冻结 `pred_proba` 与论文 Table 1 之间数值略有差异（本实现一致性 ≥ 论文水平），方向上支持"高一致"论断；κ 在 0.5 阈值相差 28%（≤40%），在论文"相位优化阈值"口径（0.6–0.65）相差 ≤8%。

## 5. 运行复现

```bash
bash agent_solution/code/run_all.sh          # 或按序运行 01/02/03
# 数据目录自动定位（$CTO_DATA_DIR / /mnt/f/dataset/biomed/2406.10292_cto_trial_outcomes/ ...）
# 产物 → agent_solution/results/*.csv, metrics.json, report_fig/ctorf_vs_paper.png
```

依赖：Python 3、pandas、numpy、scikit-learn、matplotlib。无需 GPU。