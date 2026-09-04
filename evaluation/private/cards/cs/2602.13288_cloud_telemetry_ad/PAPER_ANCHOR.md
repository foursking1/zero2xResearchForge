# PAPER_ANCHOR（私有，仅裁判/编译者可见）：2602.13288_cloud_telemetry_ad

> 用途：LLM judge 判分基准。本卡为 L1（critical claim，论文不隐藏——TASK.md 已公开论文标题与编号，但判分锚值仅见本文件）。所有数值从 arXiv:2602.13288v1 抽出（§V、Table II/III/V），禁止臆造。

## 目标论文与协议

- Islam, M. S., Miranskyy, A. (2026), "Benchmarking Anomaly Detection Across Heterogeneous Cloud Telemetry Datasets"（arXiv:2602.13288v1，Preprint，cs.NI）。
- 评测协议（§IV-A）：每条序列按时间 70% 训练 / 30% 测试；训练期 10% 作验证；似然校准（长窗/短窗/阈值）仅用训练期，论文用 W&B 100 次贝叶斯搜索（§IV-B）；NAB 归一化评分（null=0 / ideal=100）。
- 数据：论文用 NAB + Microsoft + Exathlon + IBM 四数据集；本 L1 题只冻结 NAB + Microsoft（Exathlon 为合成注入排除；IBM 超高维不冻结）。

## 锚 A1 — claim(a)：Microsoft 上 GRU 唯一全正（Table III，判 claim(a)）

| 项 | 值 |
|---|---|
| 指标名 | 各子组 × 各模型测试期（30%）归一化 NAB 分 |
| 论文数值（Table III，Microsoft 9 子组；GRU/TSMixer/Transformer/TCN/IF） | application-crash-rate-1: 31.76 / 31.68 / 29.34 / 23.13 / 11.25；application-crash-rate-2: 35.70 / 29.64 / 32.01 / 33.20 / 0.00；consumer-purchase-rate: 48.24 / 62.93 / 44.16 / 48.12 / 0.00；ecommerce-api-incoming-rps: 36.83 / 19.07 / 45.71 / 6.95 / 9.93；mongodb-machine-rps: 18.01 / 0.00 / 0.00 / 0.00 / 0.00；data-ingress-rate / middle-tier-api-dependency-latency / mongodb-application-rps† / service-unavailable†: 全模型 0.00 |
| 出处 | Table III（Microsoft 块）；Table II（best model 列：acr-1 GRU 31.76、acr-2 GRU 35.70、cpr TSMixer 62.93、ecom Transformer 45.71、mm-rps GRU 18.01） |
| 判分口径 | 5 个含异常子组上 GRU 全部 >0 且为唯一全正模型；其余已实现模型至少 1 个在 ≥1 个含异常子组 ≤0（论文中 TSMixer/Transformer/TCN 在 mongodb-machine-rps 为 0.00，IF 在 4/5 子组为 0.00） |

## 锚 A2 — claim(b)：NAB 上无主导架构（Table III，判 claim(b)）

| 项 | 值 |
|---|---|
| 指标名 | 各子组最高（正）NAB 分的归属架构；含异常子组集合 |
| 论文数值（Table III，NAB 7 子组） | artificialWithAnomaly: GRU 11.06（唯一正分）；realAdExchange: Transformer 5.52（TCN 2.77）；realAWSCloudwatch: TCN 16.44（TSMixer 9.83 / GRU 5.82）；realKnownCause: TSMixer 2.30；realTraffic: GRU 20.26（TSMixer 18.27 / Transformer 3.85）；realTweets: Transformer 6.11；artificialNoAnomaly†: 全 0.00 |
| 出处 | Table III（NAB 块）；正文 §V-B："no single architecture consistently dominates all telemetry settings" |
| 判分口径 | 6 个含异常子组中，最高分归属架构数 ≥3（论文实测 GRU×2 / Transformer×2 / TCN×1 / TSMixer×1 = 4 种）即支持 claim(b) |

## 辅助数据事实（裁判 B 维度抽查基准；从冻结数据直接核验）

| 字段 | 冻结参考值 | 备注 |
|---|---|---|
| NAB 序列数 | 58 条 CSV / 7 子组 | `nab/data/**/*.csv` 计数 |
| NAB 标签条目 | combined_windows.json 含 58 个文件条目 | 键为相对路径 |
| Microsoft 序列数 | 60 条 CSV / 9 域目录 | 域目录名与论文 Table III 子组名一一对应 |
| Microsoft 总行数/异常标签 | 225,445 行 / Label=1 共 4,555 | 逐域计数从冻结 CSV 重算 |
| Microsoft CSV 列 | TimeStamp,Value,Label（Label∈{0,1}） | 首行表头 |
| 论文 Table I 声称 | NAB 58 序列、MS 67 流、~3K 行/文件 | 本包以冻结数据为准（60 条 CSV） |

## 判分对照速查（judge 用）

- A1 满分（claim(a) 支持）：已实现 ≥3 模型（GRU+TSMixer+IF）覆盖 ≥4 个含异常 MS 子组；GRU 全部 >0 且为唯一全正；防泄漏声明明确。
- A2 满分（claim(b) 支持）：≥4 个含异常 NAB 子组有报告，最高分归属架构数 ≥3。
- B 抽查两数：(1) 冻结数据事实（NAB 58 序列 / MS 60 CSV 9 域、MS 总行数 225,445/异常 4,555）；(2) 运行 agent 提交代码从冻结数据重算一个子组的 GRU NAB 分，核对正负号与量级。
- 容差说明：论文未开源结果存档，NAB 分对似然窗口/校准高度敏感；判分以**正负号 + 排序/归属**为主，不强求逐值复现。若 agent 报告的 GRU NAB 分与锚值方向相反（该正却负）且 |Δ|≥15，判 claim(a) 不成立；归属架构数差 ≤1 视为容差内。