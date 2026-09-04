# 科研任务：异构云遥测异常检测（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id: `2602.13288_cloud_telemetry_ad`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Benchmarking Anomaly Detection Across Heterogeneous Cloud Telemetry Datasets（arXiv:2602.13288）
- 领域：CS / 云遥测 / 时序异常检测 / 基准评测

## 问题（可证伪）

论文在统一的「训练-only 似然校准 + NAB 评分」协议下（每条序列 70% 训练 / 30% 测试时间切分；验证子集仅从训练期划分；测试标签零泄漏），跨多个异构遥测数据集评测 GRU / TCN / Transformer / TSMixer 重建式自编码器与 Isolation Forest，并报告以下两个可检验结论（论文 Table III）：

- **claim (a)**（Microsoft Cloud Monitoring）：该数据集的 **5 个含异常子组**（application-crash-rate-1、application-crash-rate-2、consumer-purchase-rate、ecommerce-api-incoming-rps、mongodb-machine-rps）上，**GRU 是唯一在全部 5 个子组都取得正归一化 NAB 分（>0）的模型**；其余模型至少在一个含异常子组得分 ≤ 0。
- **claim (b)**（NAB）：该数据集的 **6 个含异常子组**（artificialWithAnomaly、realAdExchange、realAWSCloudwatch、realKnownCause、realTraffic、realTweets）上，**各子组最高 NAB 分的归属分散在至少 3 种不同架构**（论文实测最高分由 GRU×2、Transformer×2、TCN×1、TSMixer×1 取得），即「无单一架构主导」。

可证伪：(a) 若在冻结数据 + 相同协议下 GRU 未能在全部 5 个含异常子组取得正分，或另有模型同样全正；(b) 若最高分归属集中于 ≤2 种架构，则对应 claim 不成立。

## 方向提示（非方法步骤）

- 数据：本包冻结 **NAB**（58 条单变量序列 + `combined_windows.json` 异常窗口）与 **Microsoft Cloud Monitoring**（9 域 60 条单变量序列，CSV 含 `TimeStamp,Value,Label`）。论文另用的 Exathlon（合成注入）与 IBM Console（超高维）不在本任务范围，禁止引入。
- 协议：逐序列按时间 70% 训练 / 30% 测试切分；训练期划 10% 作验证（早停/校准选择）；似然参数（长窗 W、短窗 W'、阈值）只允许在训练期（含验证子集）上选择；测试标签只用于最终评分。模型训练与校准均不得使用测试期任何统计量。
- 模型：GRU / TCN / Transformer / TSMixer 重建式自编码器 + Isolation Forest 基线，实现框架自选；**至少实现 GRU + 任意一个深度模型 + Isolation Forest**（覆盖模型越多，越接近论文判分口径）。
- 指标：归一化 NAB 分（null detector = 0，ideal detector = 100；负分来自 FP 惩罚）。评分按 Numenta NAB 标准实现（异常窗口取自本包 `nab/labels/combined_windows.json`；窗口内仅计最早一次检测为 TP，FP 按时间距离惩罚）。
- 校准：似然校准器自选（论文用 100 次贝叶斯搜索；允许退化为论文 Table IV 参数范围上的网格/随机搜索），必须训练-only、可复现（固定种子）。
- 子组级报告：Microsoft 的 9 个子组与 NAB 的 7 个子组均需按子组聚合（多文件子组取其汇总分数；聚合方式在报告中声明）。

## 数据说明

- 数据包：`data/`（冻结真实数据，来源/许可/checksum 见 `data/SOURCE.md` 与 `data/source_manifest.json`）
  - `data/nab/data/<subgroup>/*.csv`：NAB 58 条单变量序列（列：timestamp,value）
  - `data/nab/labels/combined_windows.json`：NAB 官方异常窗口标签（58 个文件条目，窗口格式 `{filename: [[start,end],...]}`）
  - `data/microsoft/data/<domain>/*.csv`：Microsoft 60 条序列（列：TimeStamp,Value,Label，Label∈{0,1}）
  - `data/microsoft/data/<domain>/*-metadata.json`：各序列元信息（来自官方仓库）
- 来源/许可：NAB（Numenta，MIT 系）；Microsoft Cloud Monitoring Dataset（Microsoft，MIT）。均为真实遥测数据，非合成。详见 `data/SOURCE.md`。
- checksum（sha256）：`data/source_manifest.json`（180 个文件逐文件 size + sha256）。

## 输出要求（提交物）

1. **结论**：对 claim (a)、(b) 分别给出 `supported / partially_supported / contradicted / inconclusive`，并说明证据强度与主要不确定性。
2. **证据表**：`results/evidence_table.csv`，至少含列：`dataset`（microsoft/nab）、`subgroup`、`model`（GRU/TCN/Transformer/TSMixer/IsolationForest）、`nab_score`（归一化 NAB 分）、`has_anomaly_in_test`（测试期是否含异常窗口）、`calibration`（所用似然参数或方法描述）。
3. **代码**：完整可复现的预处理 + 模型训练 + 似然校准 + NAB 评分脚本（固定随机种子），从 `data/` 读取冻结数据；NAB 评分实现需与 NAB 标准一致。
4. **报告**：`report.md`：切分/窗口/校准协议、防泄漏声明、聚合方式、与论文 Table III 的对照（方向/量级）、局限性与种子敏感性。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成/模拟数据替代（包括不引入 Exathlon 或任何外部数据源）。
- 测试期标签与统计量禁止进入训练、验证、校准或早停。
- 每个模型在平衡条件下比较；GRU 与基线必须使用相同的预处理与校准协议。
- 禁止把论文数值当作"本实验实测"；所有分数必须由你的代码从本包数据算出。