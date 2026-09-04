# SCORE_RUBRIC（私有，仅裁判/编译者可见）：2509.16616_risky_investors_ranking

- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 总分：100 = A 核心结果达成度 60 + B 证据真实性 25 + C 方法与报告 15
- 判分模型：任意强 LLM judge 均可执行；跨 agent 比较同一任务时必须使用同一 judge 模型，数值带固定
- 判分依据：agent 提交物 + 冻结数据（`data/`，SHA-256 固定）+ PAPER_ANCHOR.md 锚值
- 难度说明：L1 给方向提示（指标、数据、预处理、模型参考），不给逐步实现；目标区间 40–50（±10）。

## A. 核心结果达成度（60 分）

### A1. 信用卡欺诈：with-prior 下 PA-RiskRanker 最优（30 分）

以 agent 实测（with-prior、3-fold CV 平均、本包 creditcard 冻结数据）判定：

| 分段 | 得分 | 判定条件 |
|---|---|---|
| 满分带 | 30 | PA-RiskRanker 的 F1 为所有已报告基准中最高 且 financial loss 为最低；且 F1 ≥ Rankformer − 0.01（方向与论文一致：0.9870 vs 0.9820） |
| 半满带 | 18 | F1 最高或 loss 最低仅其一成立；或 PA-RiskRanker 与 Rankformer 差距 < 0.005 且未讨论 |
| 低分带 | 8 | PA-RiskRanker 优于多数基准但非最高；或只实现 PA-RiskRanker 无对照 |
| 零分带 | 0 | PA-RiskRanker 被 Rankformer/多数基准反超且无法归因于实现差异；或未实现 PA-RiskRanker |

### A2. 岗位盈利：with-prior 下 PA-RiskRanker 最优（20 分）

| 分段 | 得分 | 判定条件 |
|---|---|---|
| 满分带 | 20 | 同 A1 条件（论文：F1=0.9491 vs Rankformer 0.8539，loss=19,363.32 vs 59,177.19） |
| 半满带 | 12 | F1 最高或 loss 最低仅其一成立；或差距显著缩小（<0.01）且未讨论 |
| 低分带 | 5 | 仅部分基准被超越；或无对照 |
| 零分带 | 0 | 被反超且无法归因；或未实现 |

### A3. 跨数据集方向一致性与摘要声明处理（10 分）

| 分段 | 得分 | 判定条件 |
|---|---|---|
| 满分带 | 10 | 两个数据集方向一致（A1+A2 均满分带）；正确区分"摘要声明基于专有数据、本卡仅验证附录 D 公开数据"（不把摘要 8.4%/10-17% 当本卡锚） |
| 半满带 | 6 | 两个数据集方向一致但 A1/A2 有一个半满；或未明确区分摘要声明与附录 D |
| 低分带 | 2 | 方向部分一致；或将摘要声明误作本实验结论 |
| 零分带 | 0 | 跨数据集方向冲突且未解释 |

- 方向性校验：若 agent 报告 without-prior 且 jobprofit 上 LGBM/XGB 反超、PA-RiskRanker 第 2（与论文 Table 8/9 without prior 块一致）→ A3 给满分参考（体现对论文边界的理解）；若 agent 声称 PA-RiskRanker 在所有设置全胜（与论文矛盾）且无解释 → A3/C 降档。

## B. 证据真实性（25 分）

- 提交必须含**可运行代码**（预处理 + PA-RiskRanker + ≥1 排序基线 + 3-fold 评估）+ `results/evidence_table.csv` + `results/metrics.json`——缺任一 → ≤10 分。
- 裁判抽查 2 个关键数，运行提交代码从冻结数据重算：
  1. **数据事实**：冻结原始 CSV 规模（creditcard 官方 284,807 行 × 31 列；job_profitability 9,998 行）、top-1% 正类标签构造与 70/10/20 划分可复算（固定种子）、正类比例 ≈ 1%；
  2. **with-prior 的 F1/loss**（如 creditcard 上 PA-RiskRanker 与 Rankformer 的 F1/loss）：从 agent 代码 + 冻结数据重算，核对与 evidence_table 一致。
- 计分：
  - 两个抽查数均可重算且与报告一致 → **25**。
  - 每个抽查数不可重算/不一致 → 各扣 8–12 分。
  - 无代码/代码不可运行 → 扣 8 分；evidence_table 缺失或列不完整 → 扣 5–10 分。
  - 报告把外部数字当实测（抄数）→ B 直接 ≤10 分。

## C. 方法与报告（15 分）

| 子项 | 分值 | 判分要点 |
|---|---|---|
| C1 方法合理性 | 5 | 标签/划分/ranking group 构造与论文 §3.2/附录 D 对应；PA-BCE 损失与 self-cross-trader attention 的实现描述；with-prior 口径声明 |
| C2 实验严谨性 | 6 | 3-fold CV 口径；固定种子；train/val/test 隔离（无泄漏）；financial loss 按 Amount/profitability 计罚的口径；指标计算（F1/AUC/Precision/Sensitivity/Specificity）正确 |
| C3 结论与边界 | 4 | (a)-(d) 结论标签与证据匹配；讨论局限（专有主数据不可得、仅验证公开数据集、实现与论文可能有差异）；区分摘要声明与附录 D |

- 明显泄漏（用 test 划分训练/调参）→ C 总分 ≤5，且 B 中该数不可信。

## 判定流程（judge 步骤）

1. 读 `TASK.md` → 确认提交物齐全（代码 + evidence_table.csv + report.md）。
2. 按 A1/A2/A3 数值带与模式给 A 分（从 evidence_table 读取 F1/loss，必要时重算）。
3. 从冻结数据重算抽查 2 数（fold 结构/正类比例 + 重跑 F1/loss）→ 打 B。
4. 依 C1-C3 打 C。
5. 总分 = A+B+C；将得分与理由写入评测报告。

## 难度校准

- L1 设计目标区间 40–50（±10）。校准记录见 CALIBRATION.md（自测执行：待评测阶段执行，本批次跳过）。