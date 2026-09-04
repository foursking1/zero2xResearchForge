# PAPER_ANCHOR（私有，仅裁判/编译者可见）：2505.01415_everglades_water_level

> 用途：LLM judge 判分基准。本卡为 L1（critical claim）。数值全部摘自 arXiv:2505.01415v2（§3.1 实验设置、Table 1/2、§4 Results），禁止臆造。Table 1 数值已用官方仓库 Results-28days-final.xlsx（模型输出）交叉核验一致。

## 目标论文与协议

- Rangaraj, Shi et al. (2025), "How Effective are Large Time Series Models in Hydrology? A Study on Water Level Forecasting in Everglades"（arXiv:2505.01415v2）。
- 数据（§2.1/Appendix A）：Everglades National Park 区域水文站点日频数据（DBHYDRO + NPS），1,411 天（2020-10-16 → 2024-08-26），37 变量。
- 协议（§3.1）：训练 = 前 1,200 天，验证 ≈ 211 天，测试 = 最后 211 天；输入 = 前 100 天全部变量，预测 5 站点（NP205_stage/P33_stage/G620_water_level/NESRS1/NESRS2）未来 7/14/21/28 天；12 个任务特定模型（neuralforecast，h=28，input=100，max_steps=1000）+ 5 个零样本基础模型；指标 MAE/RMSE（Table 1）+ SEDI（Table 2）。
- 官方仓库：https://github.com/rahuul2992000/Everglades-Benchmark （数据 final_concatenated_data.csv；模型输出 Results-28days-final.xlsx 未冻结——非原始数据）。

## 锚 A1 — 28 天 Overall MAE（Table 1，lead time 28；官方 xlsx 交叉核验一致）

| 模型 | 类别 | Overall MAE（28 天） |
|---|---|---|
| **Chronos** | 零样本基础模型 | **0.088** |
| NBEATS | MLP | 0.176 |
| TSMixer | MLP | 0.186 |
| NLinear | 线性 | 0.185 |
| PatchTST | Transformer | 0.193 |
| RMoK | KAN | 0.191 |
| iTransformer | Transformer | 0.198 |
| KAN | KAN | 0.214 |
| TimeGPT | 基础模型 | 0.238 |
| TimeLLM | LLM | 0.242 |
| TimeMixer | MLP | 0.312 |
| timesfm | 基础模型 | 0.342 |
| TSMixerx | MLP | 0.358 |
| Morai | 基础模型 | 0.364 |
| Timer | 基础模型 | 0.385 |
| **DLinear** | 线性 | **0.392** |
| Informer | Transformer | 0.478 |

- 出处：Table 1（Overall 列，lead 28）；§4 RQ1/RQ2 "Chronos consistently outperforms other models"、"NBEATS, TSMixer, PatchTST, and RMoK consistently outperforming others"、"the linear-based models ... experience a significant drop in performance as the forecasting horizon increases"。
- 判分口径：agent 任务特定模型的 28 天 Overall MAE 与排序模式。

## 锚 A2 — 线性模型短→长 horizon 退化（Table 1，Overall MAE）

| 模型 | 7 天 | 14 天 | 21 天 | 28 天 |
|---|---|---|---|---|
| NLinear | 0.108 | 0.115 | 0.146 | 0.185 |
| DLinear | 0.095 | 0.149 | 0.262 | 0.392 |
| NBEATS | 0.076 | 0.109 | 0.139 | 0.176 |
| Chronos | 0.049 | 0.069 | 0.085 | 0.088 |

- 判分口径：线性类相对增幅（7→28 天）是否显著（DLinear +313%、NLinear +71%）且明显大于 NBEATS（+132%）——以相对增幅排序为主。

## 锚 A3 — Chronos 零样本基础模型 claim（Table 1）

- Chronos 28 天 Overall MAE 0.088，为全部 17 模型最低；7 天 0.049 最低。
- Chronos − 最佳任务特定（NBEATS）= 0.088（28 天）差距 0.088；7 天差距 0.027。
- 其余基础模型：TimeGPT 0.238（与最佳任务特定相当，§4 RQ1 "TimeGPT achieves results comparable to the best task-specific models"）、TimesFM 0.342、Timer 0.385、Moirai 0.364（远差于 Chronos）。
- 判分口径：若 agent 运行 Chronos（chronos-forecasting/autogluon，零样本），其 28 天 Overall MAE 是否显著低于其最佳任务特定模型（差距 ≥ 0.05）；且 Chronos 数值接近 0.088（±50% 容差）。

## 锚 A4（辅助）— 站点难度模式（Table 1，Chronos 28 天分站）

- NP205 0.147 / P33 0.090 / G620 0.083 / NESRS1 0.071 / NESRS2 0.049；所有模型在 NP205 误差最高（§4 RQ1 "the worst scenarios for the NP205 station"）。
- 判分口径：agent 结果中 NP205 是否也为最难站点（MAE 最高）。

## 判分对照速查（judge 用）

- A1 满分带：agent 的 MLP 类 28 天 Overall MAE 相对 NBEATS 锚（0.176）绝对差 ≤ 0.05，且 DLinear 类相对 0.392 ≤ 0.10；排序 MLP < 线性。
- A2 满分带：线性类 7→28 天相对增幅 ≥ 50% 且 DLinear 类增幅 ≥ NLinear 类。
- A3 满分带（仅当 agent 运行 Chronos 或等价零样本基础模型）：Chronos 28 天 Overall MAE 显著低于最佳任务特定（差 ≥ 0.05）。
- A4：NP205 为最难站点 → 方向一致。
- B 抽查字段：冻结 CSV 行数（1,411）、日期范围（2020-10-16 → 2024-08-26）、某模型 NP205 站 28 天 MAE 重算、Overall MAE 重算。
