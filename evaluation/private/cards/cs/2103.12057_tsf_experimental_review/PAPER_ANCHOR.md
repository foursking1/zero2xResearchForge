# PAPER_ANCHOR：论文核心结果锚（私有，禁止外泄到 TASK.md 之外的公开面）

论文：P. Lara-Benitez, M. Carranza-Garcia, J. C. Riquelme, An Experimental Review on Deep Learning Architectures for Time Series Forecasting, IJNS 31(03) 2130001 (2021)，arXiv:2103.12057。以下数值摘自论文 Table 11，并已用官方仓库 results/results.csv（37,169 行）逐值复算确认。

## 锚 A1 — M3 月度上 GRU 最佳 WAPE
- 数值：**15.182**（results.csv 精确值 15.181845700367338）
- 出处：Table 11 第 4 列（M3），GRU 行；正文 §4.1。
- 定义口径：M3 月度 1,428 条序列、FH=18；固定起点（最后 18 观测 = test）；逐序列 min-max/z-score 归一化（train 拟合）；MIMO 滑窗 `past_history = int(18×1.25) = 22`；Adam lr=0.001、batch 32/64、5 epochs（官方参数网格）；"最佳 WAPE" = 该架构全部超参配置中的最小平均 WAPE（每条序列 WAPE 的均值）。
- 容差（判分用）：相对差 ≤15% 满分档；≤30% 半档；≤50% 低档（详见 SCORE_RUBRIC.md）。

## 锚 A2 — M3 月度上 LSTM 最佳 WAPE
- 数值：**15.282**（results.csv 15.281933229917842）
- 出处：Table 11 第 4 列（M3），LSTM 行。
- 定义口径：同 A1。
- 容差：同 A1。

## 锚 A3 — M3 月度上 MLP 最佳 WAPE（最差架构）
- 数值：**21.114**（results.csv 21.11419619267824）
- 出处：Table 11 第 4 列（M3），MLP 行；正文 §4.1 "MLP models perform the worst overall"。
- 定义口径：同 A1；MLP 网格 = 12 种隐层结构（[8] 至 [32,64,128,64,32]）。
- 容差：相对差 ≤15% 满分档；≤30% 半档；≤50% 低档。

## 锚 A4（辅助）— M3 全列与全局统计结论
- M3 列完整值：ERNN 15.621、TCN 15.587、CNN 15.612、ESN 17.184（Table 11；results.csv 复算一致）。
- 全局结论（§4.1/§4.3/Figure 6）：best-WAPE Friedman 排序 LSTM 第 1、GRU 紧随其后；CD 图显示除 MLP 外各架构最佳配置差异不显著；mean-WAPE 排序 CNN 第 1、LSTM 第 2（对参数化不敏感）；MLP 计算效率第 1 但精度最差。
- 用途：辅助判断 agent 结论；若 agent 声称"MLP 精度与序列模型相当"或"LSTM 显著差于 GRU"等，需给出证据。

## 判分一致性提醒
- 锚 A1/A2/A3 均来自同一 M3 列，可互相交叉核对（A1<A3 必须成立）；判分以 A1（GRU/LSTM 取报告者所用模型的对应锚）与 A3（MLP）为主。
- "最佳 WAPE" 依赖全网格搜索；单配置复现值通常高于锚值，rubric 带宽已考虑（方向性 + 幅度为主）。
