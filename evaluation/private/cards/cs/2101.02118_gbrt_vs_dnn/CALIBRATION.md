# CALIBRATION：难度校准记录（私有）

- 任务：`2101.02118_gbrt_vs_dnn`（L1 critical claim）
- 设计目标区间：**L1 = 40-50（±10）**

> **自测执行：待评测阶段执行（本批次跳过）**
> 本卡不包含实测分数；难度校准将在评测阶段由同级 agent 按 SCORE_RUBRIC.md 执行并回填。

## 校准杠杆（设计说明）

| 杠杆 | 本卡设定 |
| --- | --- |
| 方向提示颗粒度 | 给数据划分（t′/τ）、w=h=24、逐序列独立、多输出 GBRT 与基线（GBRT(Naive)/ARIMA）、指标公式（RMSE/WAPE/MAE）；不给 XGBoost 具体超参与 DNN 复现细节 |
| 论文锚容差 | A1 RMSE ±25% 满分带（[100,160]）且需低于 naive/ARIMA；A2 ±30% 满分带且本地最优；A3 方向比较 |
| 证据核查严格度 | 抽查文件维度（7,588×8 等）与某模型 RMSE 重算 |

## 关键设计决策与对锚的影响

- 冻结数据为 Lai 官方仓库原始四数据集（LSTNet 论文同源）。论文对 Electricity/Traffic 做了 n=70/90 子采样（§2.2）但未公开所选序列子集；因此 A1 的绝对 RMSE 锚（125.626）依赖子采样与 XGBoost 实现细节 → 带宽放大（±25%），方向性（低于 naive 与 ARIMA）作为主要判据。
- Exchange-Rate（8 条全量，无子采样）与 Solar-Energy（137 条全量）锚更干净，作为 A2/A3 主锚。
- agent 若用 sklearn HistGradientBoosting（原生多输出）替代 XGBoost，RMSE 预计相近但非完全一致；带宽已覆盖。
- 若 agent 只跑 Exchange-Rate（算力小）不跑 Electricity → A1 得 0，总分上限约 55-60，符合 L1 需覆盖主锚的设计。
- **风险**：electricity 321×26k 训练窗口量大（约 8M 样本 × 24 特征）→ 任务明确允许固定种子子采样 70 条（对齐论文 n=70）或说明全量口径；judge 以方向性与带宽判分。

## Rubric 定稿说明

- 100 分制：A 60（A1 25 + A2 20 + A3 10 + 方向性校验 5）/ B 25 / C 15。
- 定稿于 2026-08-13（本批次跳过自测执行，评测阶段回填实测分数与调整动作）。

## 实测记录（评测阶段回填）

| 项 | 值 |
| --- | --- |
| 自测 Electricity RMSE | 待评测 |
| 自测 Exchange-Rate RMSE | 待评测 |
| 自测 A / B / C 得分 | 待评测 |
| 总分 | 待评测 |
| 调整动作 | 待评测 |
