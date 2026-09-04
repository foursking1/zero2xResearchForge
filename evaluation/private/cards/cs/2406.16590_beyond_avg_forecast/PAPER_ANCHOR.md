# PAPER_ANCHOR（私有，仅裁判/编译者可见）：2406.16590_beyond_avg_forecast

> 用途：LLM judge 判分基准。本卡为 L2（RCBench 端到端科研再发现，目标论文隐藏——TASK.md 不给论文标题/编号；锚值仅见本文件）。数值/结论从 arXiv:2406.16590v1 抽出（§3 Materials、§4 Experiments、§5 Discussion、Table 1、Fig 1/3/4/6/7），禁止臆造。

## 目标论文与协议

- Cerqueira, V., Roque, L., Soares, C. (2024), "Forecasting with Deep Learning: Beyond Average of Average of Average Performance"（arXiv:2406.16590v1）。
- 协议（§3）：7 方法（NHITS 深度全局 + ARIMA/ETS/SNaive/RWD/SES/Theta 经典局部）；SMAPE；测试 = 每条序列最后 H 观测（月度 18 / 季度 8 / 年度 6）；多视角评估（overall / horizon / frequency / difficulty / anomalies / win-loss）。
- 数据（§3.1 Table 1）：M3（3,003 条：月 1,428 / 季 756 / 年 645）、Tourism（1,311 条：月 366 / 季 427 / 年 518）、M4 月季年子集（95,000 条）；合计 99,140 条、14,898,364 观测。
- **本卡冻结数据 = M3 + Tourism（论文的 4,314 条子集）；M4 排除（官方测试值无公开托管，见 SOURCE.md）。因此 agent 的绝对数值必然与论文不同（论文数值含 M4），判分以模式/方向一致为主。**

## 锚 A1 — 数据集组成与协议（Table 1，判数据正确性）

| 项 | 值 |
|---|---|
| M3 序列数 | 3,003（月度 1,428 / 季度 756 / 年度 645） |
| Tourism 序列数 | 1,311（月度 366 / 季度 427 / 年度 518） |
| 测试 horizon | 月度 18 / 季度 8 / 年度 6 |
| 输入窗 p（论文给深度模型的启发式） | p = ceil(max(H, frequency) × 1.25)（月度 23 / 季度 10 / 年度 8） |
| 出处 | §3.1 Table 1 |

## 锚 A2 — 多视角评估的核心发现（§4-5，判 Q1-Q3 模式）

| 发现 | 论文表述 | 出处 |
|---|---|---|
| F1 整体：NHITS 最优，Theta 为最佳经典方法 | "NHITS presents the best score, outperforming all classical approaches. Among these, the Theta method exhibits the best performance." | §4.1 / Fig 1a |
| F2 horizon：首步 NHITS 与 Theta/ETS 相当；末步 NHITS 明显占优 | "for the first horizon, NHITS shows comparable performance with several classical approaches, such as Theta and ETS. However, in the last horizon, NHITS outperforms other approaches."；"NHITS is particularly suited in forecasting multiple steps ahead" | §4.1 / Fig 3；§5 发现 4 |
| F3 频率：NHITS 在月/季/年均最优，但年度上优势减小 | "NHITS shows the best performance in all three sampling frequencies... less competitive for time series with low sampling frequencies, such as yearly" | §4.1 / Fig 2；§5 发现 1 |
| F4 异常：NHITS 被 ETS（overall SMAPE）与 SES/Theta（expected shortfall）超越 | "NHITS is outperformed by ETS in terms of overall SMAPE and by SES and Theta in terms of expected shortfall" | §4.3 / Fig 7 |
| F5 胜率：NHITS vs Theta 约 50% 序列胜出（非稳定全胜） | "NHITS outperforms Theta in about 50% of the 99140 time series" | §4.1 / Fig 4a |
| F6 困难问题：NHITS 优势显著缩小 | "NHITS also shows the best performance in difficult problems. However, the advantage is considerably smaller" | §4.2 / Fig 6；§5 发现 5 |

## 判分对照速查（judge 用）

- A1 满分：数据事实正确（3,003/1,311 序列、H=18/8/6、末 H 留测）、切分无泄漏。
- A2 满分：agent 在冻结数据上独立复现 ≥4/6 个发现的方向（F1-F6），且与 Q2/Q3 的结论标签一致。
- 容差说明：论文数值基于 M3+M4+Tourism 全量（99,140 条），本包只冻结 M3+Tourism（4,314 条）→ 绝对 SMAPE/胜率数值必然不同。判分以**方向 + 相对排序**为主：F5 的"~50%"按 30%-70% 带判定（支持"并非稳定全胜"结论）；F2/F4 以"首步 vs 末步""正常 vs 异常"的排名是否翻转判定。
- B 维度抽查：从冻结 .tsf 重算序列数与末 H 切分（如 M3 月度任意序列长度 ≥ H，且测试段 = 最后 18 值）；重跑 agent 代码核对某视角 SMAPE 与 evidence_table 一致。