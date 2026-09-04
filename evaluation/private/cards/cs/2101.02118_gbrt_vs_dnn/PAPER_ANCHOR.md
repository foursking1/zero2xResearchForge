# PAPER_ANCHOR（私有，仅裁判/编译者可见）：2101.02118_gbrt_vs_dnn

> 用途：LLM judge 判分基准。本卡为 L1（critical claim）。数值全部摘自 arXiv:2101.02118v2（§4 方法、§5 实验、Table 1/2/3/4），禁止臆造。

## 目标论文与协议

- Elsayed, Thyssens, Rashed, Jomaa, Schmidt-Thieme (2021), "Do We Really Need Deep Learning Models for Time Series Forecasting?"（arXiv:2101.02118v2）。
- 方法（§4）：把时序预测重构为窗口回归；滑窗 w，展平历史 w 个目标值（+ 可选最后时点协变量）→ 多输出 GBRT（每个 horizon 步一个回归器，单目标变换）；w = h = 24（表 1；§5.2 "the lookup window size used is equivalent to the forecasting window size"）。
- 数据（表 1）：Electricity n=70/T=26,136/h=24/t′=25,968/τ=168；Traffic n=90/T=10,560/h=24/t′=10,392/τ=168；Exchange-Rate n=8/T=7,536/h=24/t′=6,048/τ=1,488；Solar-Energy n=137/T=52,600/h=24/t′=42,048/τ=10,512。
- 指标（附录 B）：RMSE、WAPE（归一化偏差 Σ|e|/Σ|y|）、MAE；表 4 用 RSE 与 Corr（LSTNet 原始设置）。
- 模型实现：XGBoost 版 GBRT（§4）；naive GBRT 为点对点回归（§4 公式 2）；ARIMA 为传统拟合基线（§5.1）。

## 锚 A1 — Electricity（Table 2，无协变量）

| 模型 | RMSE | WAPE | MAE |
|---|---|---|---|
| LSTNet | 1095.309 | 0.997 | 474.845 |
| TRMF | 136.400 | 0.095 | 53.250 |
| DARNN | 404.056 | 0.343 | 194.449 |
| GBRT(Naive) | 523.829 | 0.878 | 490.732 |
| ARIMA | 181.210 | 0.310 | 154.390 |
| **GBRT(W-b)** | **125.626** | **0.099** | 55.495 |

- 判分口径：agent 的窗口化 GBRT RMSE 与 125.626 比较；GBRT(W-b) 为六模型最低（表 2 粗体），相对 GBRT(Naive) 提升 4.17×、相对 ARIMA 提升 1.44×。

## 锚 A2 — Exchange-Rate（Table 2，无协变量）

| 模型 | RMSE | WAPE | MAE |
|---|---|---|---|
| LSTNet | 0.018 | 0.017 | 0.013 |
| TRMF | 0.018 | 0.015 | 0.011 |
| DARNN | 0.025 | 0.022 | 0.016 |
| GBRT(Naive) | 0.081 | 0.456 | 0.068 |
| ARIMA | 0.123 | 0.170 | 0.101 |
| **GBRT(W-b)** | **0.017** | **0.013** | **0.010** |

- 判分口径：GBRT(W-b) 的 RMSE/WAPE/MAE 全为六模型最优；相对 GBRT(Naive) 提升 4.76×（RMSE）、35×（WAPE）；相对 ARIMA 7.2×。

## 锚 A3 — Solar-Energy（Table 4，h=24，RSE/Corr）

| 模型 | RSE | Corr |
|---|---|---|
| LSTNet*（原文报告） | 0.464 | 0.887 |
| **GBRT(W-b)** | **0.455** | **0.896** |

## 锚 A4 — 表 3 与表 5（可选参考）

- 表 3（带时间协变量）：Electricity GBRT(W-b) RMSE 119.051 / WAPE 0.089 / MAE 50.150 vs DeepGlo 141.285 / 0.094 / 53.036；Traffic GBRT(W-b) RMSE 0.014 vs DeepGlo 0.026。
- 表 5（WAPE）：ElectricityV2 GBRT(W-b) 0.067 vs TFT 0.055；TrafficV2 0.148 vs TFT 0.095——TFT 是论文中唯一一致优于 GBRT(W-b) 的 DNN（§5.2 结论）。

## 数据事实（B 抽查用）

- exchange_rate.txt.gz：7,588×8（8 国）；solar_AL.txt.gz：52,560×137；electricity.txt.gz：26,304×321；traffic.txt.gz：17,544×862。
- 论文 t′/τ（表 1）：exchange_rate 6,048/1,488；solar 42,048/10,512；electricity 25,968/168；traffic 10,392/168。
- 注：冻结文件为仓库当前版本（总时点数与论文表 1 的 T 略有出入，协议按「丢弃最前多余行、t′/τ 不变」执行）。

## 判分对照速查（judge 用）

- A1 满分带：agent RMSE ∈ [100, 160]（±25% 围绕 125.626）且 < GBRT(Naive) 与 < ARIMA。
- A2 满分带：RMSE ∈ [0.012, 0.022]（±30% 围绕 0.017）且为提交模型中最优。
- A3：RSE < 0.464 且 Corr > 0.887 → 满分。
- B 抽查：文件维度；exchange_rate 测试段重算某模型 RMSE。
