# solution.md

### 任务
复现 **Benchmarking Anomaly Detection Across Heterogeneous Cloud Telemetry
Datasets** (arXiv:2602.13288, Table III) 的两个可检验结论，冻结数据为
**NAB**（58 条单变量序列）+ **Microsoft Cloud Monitoring**（60 条 / 9 域）。

### 方法（一句话）
逐序列 **70% 训练 / 30% 测试** 时间切分（训练期后 10% 作验证），以
**重建式高斯似然自编码器**（GRU / TCN / Transformer / TSMixer，每点输出
Gaussian NLL）与 **Isolation Forest** 基线，在验证期上做
**仅训练期** 的似然校准（长窗 W、短窗 W'、阈值 θ 网格搜索），随后用
**NAB 归一化评分**（null=0 / ideal=100；窗口内最早检测计 TP、FP 按距离惩罚）
对测试期评分。

### 关键结果

**claim (a) Microsoft 5 个含异常子组 × per-model 归一化 NAB 分**

| 子组 | GRU | TCN | Transformer | TSMixer | IsolationForest |
|---|---|---|---|---|---|
| application-crash-rate-1 | **30.74** | 30.44 | 21.36 | 20.87 | 26.48 |
| application-crash-rate-2 | **56.82** | 47.67 | 60.30 | 53.09 | 47.54 |
| consumer-purchase-rate | **84.43** | 53.87 | −24.88 | 42.01 | 17.12 |
| ecommerce-api-incoming-rps | **31.87** | 14.39 | 34.96 | 15.20 | 35.19 |
| mongodb-machine-rps | **26.10** | 15.56 | 4.36 | 4.41 | −1.16 |

→ **GRU 在全部 5 个含异常子组均为正**（种子 0、种子 7、以及更严阈值变体下
稳健），与论文一致；但 **TCN 与 TSMixer 同样全正**（尤其 mongodb-machine-rps
上分别 +4~16、+4~7 贴近 0），因此"GRU 唯一全正"在本复现中**不成立**。

**claim (b) NAB 6 个含异常子组最高分归属**

| 子组 | 最高分归属 | 分数 |
|---|---|---|
| artificialWithAnomaly | Transformer | 36.92 |
| realAdExchange | Transformer | 66.79 |
| realAWSCloudwatch | IsolationForest | 16.34 |
| realKnownCause | TCN | 47.14 |
| realTraffic | IsolationForest | 56.12 |
| realTweets | IsolationForest | 51.06 |

→ 最高分归属 **3 种架构**（种子 7 为 4 种：GRU/TCN/Transformer/IF），
**无单一架构主导**（种子 7 中 GRU 在 realAWSCloudwatch 与 realTraffic 夺冠，
与论文 Table III 的 GRU 归属一致）。

### 结论
- **claim (a): `partially_supported`** — GRU 全正部分成立且稳健；"唯一全正"部分
  未复现（TCN/TSMixer 同全正）。
- **claim (b): `supported`** — 无主导架构，最高分归属架构数 ≥3（两个种子下
  分别为 3 与 4）。

### 防泄漏声明
仅训练期（含验证子集）用于拟合、早停与似然校准；测试标签/统计量只出现在最终
NAB 评分的 detections 对照中。详见 report.md。

### 产物
- `results/evidence_table.csv` — 80 行子组 × 模型 NAB 分（含 required 6 列）
- `results/metrics.json`、`results/series_raw.csv`、`results/claim_summary.json`
- `results/paper_comparison_table.csv`、`results/robustness_summary.json`、
  `results/seed_sensitivity_table.csv`、`results/nab_best_attribution.csv`
- `results/fig_*.png` — 热力图 / 分组柱状图 / 示例检测图
- `code/` — 完整可复现代码；`run_all.sh` 一键复现