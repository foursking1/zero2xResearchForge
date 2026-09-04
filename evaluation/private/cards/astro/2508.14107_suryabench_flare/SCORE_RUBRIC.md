# SCORE_RUBRIC（私有，仅裁判/编译者可见）：2508.14107_suryabench_flare

- 层级：L2（端到端科研再发现；目标论文隐藏）
- 总分：100 = A 核心结果达成度 60 + B 证据真实性 25 + C 方法与报告 15
- 判分模型：任意强 LLM judge（Claude / GLM 均可）均可执行；**跨 agent 比较同一任务时必须使用同一 judge 模型**，并严格按下方数值带打分（数值带已固定，judge 不得自行放宽）。
- 判分依据：agent 提交物 + 冻结数据（`data/`，SHA-256 固定）+ PAPER_ANCHOR.md 锚值。

## A. 核心结果达成度（60 分）

判分基准（PAPER_ANCHOR A3）：论文在官方 test 期（2020–2024）报告的 5 个 CNN 基线 TSS ∈ [0.261, 0.359]（AlexNet 最佳 0.359）。容差带如下（已按冻结数据可达范围校准，见 CALIBRATION.md）：

| 分段 | 得分 | 判定条件（agent 报告的 test 期 label_max TSS） |
|---|---|---|
| 满分带 | **60** | TSS ∈ [0.20, 0.42] **且** 同步报告 HSS **且** 完成 base-rate 漂移分析（train≈0.121 → test≈0.294）**且** 给出阈值敏感性或不确定性区间 |
| 半满带 | **30** | TSS ∈ [0.10, 0.20) ∪ (0.42, 0.70]；或落入满分带但漂移/阈值敏感性分析缺任一项 |
| 零分带 | **0** | TSS < 0.10（无可证正技能）；或 TSS > 0.70（见下注）；或将高技能直接归因为"无漂移的纯泛化"（数据上 base rate 0.121→0.294 明确漂移，属结论失真） |

> 注（>0.70 判 0 的理由）：冻结数据仅含 GOES 派生标签序列；TSS>0.70 通常来自 GOES 历史特征中的强 persistence 型信息（自测基线 0.9162），与论文 SDO 影像 CNN 基线（0.26–0.36）不同源，不是对论文结果的复现。该约束使 A 满分在冻结数据下不可达，属本卡固有难度（B+C 是良构科学的主要得分面）。若未来提供影像数据可放宽此带。

## B. 证据真实性（25 分）

- 提交必须含 **代码** + **证据表**（`results/evidence_table.csv`，列：`period,n,base_rate,threshold,tp,fp,tn,fn,tss,hss`，TSS/HSS 可从 TP/FP/TN/FN 重算）+ `results/metrics.json`。
- 裁判**抽查 2 个关键数**，运行提交代码从冻结数据重算：
  1. **test 期 label_max base rate = 0.2943**（n=43,848，正样本 12,903）——冻结值（PAPER_ANCHOR 辅助事实）；
  2. **test 期 TSS**（从 agent 的预测/混淆计数重算，须与 agent 报告值一致，相对差 ≤1e-6）。
  - 可选追加抽查：train 期 base rate 0.1211。
- 计分：
  - 两个抽查数均可从冻结数据+代码重算且与报告一致，证据表行级可重算 → **25**（满分）。
  - 每个抽查数不可重算/与报告不一致 → 各扣 8–12 分。
  - 无代码或代码不可运行 → 扣 8 分；证据表缺失/列不完整 → 扣 5–10 分。
  - 证据表 TSS/HSS 无法从 TP/FP/TN/FN 重算（抄数嫌疑）→ 该项直接 0–8 分。

## C. 方法与报告（15 分）

| 子项 | 分值 | 判分要点 |
|---|---|---|
| C1 方法合理性 | 5 | 特征严格滞后于窗口开始时刻（无未来泄漏）；warm-up 缺失行被显式处理并报告；模型/特征选择有依据 |
| C2 泛化评估严谨性 | 6 | 报告 base-rate 漂移及其对技能的贡献；阈值敏感性或重采样不确定性区间；分年或分活动水平（如 2020 极小期 vs 2023–2024 峰值）分析 |
| C3 报告与边界 | 4 | 结论用四档标签（supported/partially_supported/contradicted/inconclusive）；scope 与 limitations 明确（输入口径=GOES 历史、无影像；不宣称物理因果）；报告≤2 页可读 |

## 判定流程（judge 步骤）

1. 读 `TASK.md` → 确认提交物齐全（claim/code/evidence_table/metrics/figure/report）。
2. 按 A 数值带对 agent 报告的 test 期 TSS 打分（60/30/0）。
3. 运行提交代码（Python 3.11+，numpy/pandas/sklearn），从 `data/` 冻结数据重算抽查 2 数 → 打 B。
4. 依 C1–C3 打 C。
5. 总分 = A+B+C；将得分与理由写入 `CALIBRATION.md`（若为后续 agent 复测）或评测报告。