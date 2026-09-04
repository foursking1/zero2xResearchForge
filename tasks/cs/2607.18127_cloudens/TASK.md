# 科研任务：ClouDens 云遥测上下文感知异常检测（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id: `2607.18127_cloudens`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：ClouDens: Operational Context-Aware Anomaly Detection for Large-scale Cloud System Monitoring（arXiv:2607.18127，IEEE TNSM 投稿）
- 领域：CS / 云系统监控时序异常检测（ST-GNN + 运营上下文图）

## 问题（可证伪）

在冻结的 IBM Cloud Telemetry 真实生产云遥测数据上，验证论文的核心结论：**利用遥测日志 schema 中编码的运营上下文属性（部署位置、通信角色、组件、HTTP 方法/状态码、端点等）构建"上下文感知图"，能显著提升大规模云监控的异常检测性能**。具体可证伪子 claim（论文 Table IV，5xx count 子集、滑窗 w=6）：

1. **claim A（方向性，主 claim）**：在 Mahalanobis Distance（MD）评分下，ClouDens（A3T-GCN + 上下文图）NAB Standard = 20.94、LowFN = 26.24，远超无图的 GRU 基线（5.89 / 10.95）——即上下文感知图带来约 3.6x（Standard）与 2.4x（LowFN）的 NAB 提升。
2. **claim B（检测质量）**：ClouDens 比 GRU 检出更多真异常（TP 16 vs 13）、更少误报（FP 37 vs 40）；对 9 个 Instant Messenger 异常检出 6 个（GRU 仅 4 个），并额外捕获 GRU 漏检的 Issue Tracker Anomaly 3。
3. **claim C（辅助，评分策略互补）**：不同评分策略揭示不同异常（如 GRU 的 LF 检出 [6,7,8,17] 而 MD 检出 [6,8,14,17]）；ClouDens 在 LF 下 NAB 也高于 GRU（11.38 vs 6.58；18.11 vs 13.16）。

可证伪表述：基于冻结数据，(a) "上下文感知图建模使 5xx count 子集 MD 评分的 NAB 显著高于无图 GRU 基线" 是否成立；(b) "ClouDens 检测质量（TP 更多/FP 更少/异常覆盖更广）优于 GRU" 是否成立；(c) 论文报告的 LF/MD 互补模式是否在你的结果中复现。

## 方向提示（非方法步骤）

- **数据与子集**：冻结数据 = IBM Cloud Telemetry（Zenodo 10.5281/zenodo.14062900）`pivoted_data_all.parquet`（39,365 时点 x 117,448 特征，5 分钟间隔，约 4.5 个月）+ `anomaly_windows.csv`（25 个标注异常窗，`anomaly_source`：1=Issue Tracker、2=Instant Messenger、3=Test Log）。**5xx count 子集** = 列名同时含 5xx 状态码（500-599）与 count 聚合的特征，共 2,406 个（稀疏度 99.02%）；特征名模板如 `count_datacenter4_CLIENT_component15_GET_500_endpoint643`（<聚合>_<位置>_<角色>_<组件>_<方法>_<状态码>_<端点>）。
- **数据划分（论文 §V-B 官方协议）**：训练 = 2024-01-26 ~ 2024-02-29（5 周，剔除含标注异常的窗口，即 anomaly_windows 中 a1-a6）；验证 = 训练段后 30%；测试 = 2024-03-01 ~ 2024-05-31（26,488 时点，19 个测试期异常窗 a7-a25 覆盖 967 时点约 3.65%）。标签只用于评估。
- **预处理**：5xx count 子集用 **zero 插补**（论文 Table III）；min-max 归一化只由训练段拟合；滑窗 w=6、单步预测。
- **模型方向**：预测式异常检测——GRU 基线（32 隐层）vs ClouDens（上下文感知图 + A3T-GCN，32 隐层；图节点 = API 活动，边权重 = 共享上下文属性的强度，self-loop=1，可参考论文 Fig. 3 的 0.8/0.2 权重示例）；Adam lr=1e-3、MSE、batch 32；两模型除图外设置一致。
- **异常评分**：预测误差 -> 评分 -> 阈值。MD 评分阈值 ϵ=99.8（主）；LF 评分 W=30、W'=2、Lt=0.99975（辅助）。NAB 评分用 Standard 与 LowFN（Reward Low FN）两个 profile。
- **指标口径**：NAB 分数（主指标）+ 逐点混淆矩阵 TP/TN/FP/FN（总和 = 26,488）+ 每个 ground-truth 异常窗是否被检出（窗内至少一个 TP 即检出；窗内额外警报忽略）。19 个测试期异常窗的 ID 映射：a7->0 ... a25->18（按时间顺序）。
- **复现包**：论文复现包已公开（GitHub `doanthihoaithu/cloudens`，含预处理/训练/评分/NAB 全管线与实验 CSV），可复用或对照实现。**禁止**把复现包 CSV 或论文数字直接当作"本实验实测"。
- **防泄漏**：异常标签只用于评估；min-max 统计量只由训练段拟合；训练剔除标注异常窗；滑窗只用历史 w 步；测试段（含正常时点）不得参与训练/验证/阈值选择。

## 数据说明

- 数据包（冻结，来源/许可/checksum 见 `data/SOURCE.md` 与 `data/source_manifest.json`）：
  - `$PAPER_BENCH_DATA_DIR/pivoted_data_all.parquet`（约 2.6GB，39,365 x 117,449，含 1 个时间列）
  - `$PAPER_BENCH_DATA_DIR/data/labels/anomaly_windows.csv`（25 个异常窗：`number/anomaly_start/anomaly_end/anomaly_source`，时区 -0500/-0400）
  - `$PAPER_BENCH_DATA_DIR/data/labels/location_downtime.csv`（数据中心停机时间段，辅助上下文）
- 来源：Islam, Rakha, Pourmajidi, Sivaloganathan, Steinbacher & Miranskyy (2024), "Anomaly Detection in Large-Scale Cloud Systems: An Industry Case and Dataset"（arXiv:2411.09047，ICSE-SEIP 2025），Zenodo 10.5281/zenodo.14062900（CC BY 4.0）。
- 读取：`pandas.read_parquet(...)`（需 pyarrow/fastparquet）；列名即特征名（含上下文属性编码）。
- 许可：CC BY 4.0（注明出处即可，允许学术研究使用）。
- 禁止下载其他版本数据或使用合成/模拟数据替代。

## 输出要求（提交物）

1. **结论**：对 claim A/B/C 分别给出 `supported / partially_supported / contradicted / inconclusive`，并说明数据支持的强度。
2. **证据表**：`results/evidence_table.csv`（或等价表格），至少含列：`scoring_strategy`（likelihood/mahalanobis）、`model`（GRU/ClouDens）、`fill_nan`（zero）、`TP/TN/FP/FN`、`nab_standard`、`nab_lowfn`、`detected_issue_tracker`、`detected_instant_messenger`、`detected_test_log`（检出 ID 列表）；MD 策略两模型必填，LF 建议填。
3. **代码**：完整可复现的训练/评估脚本（固定随机种子，报告种子值），从冻结 parquet 读取数据并给出 5xx count 特征筛选逻辑。
4. **报告**：`report.md`：方法（子集筛选、插补、图构建、模型、评分、NAB 计算）、防泄漏说明、与论文复现包的差异（版本/种子/资源）、局限性（GPU 依赖、运行时长）。

## 数据铁律提醒

- 只用本包冻结数据；禁止合成/模拟数据替代。
- 训练只允许用 2024-01-26 ~ 2024-02-29 且剔除异常窗的时点；测试段（含正常时点）禁止参与训练、验证或阈值校准。
- anomaly 标签只用于评估；min-max/插补统计量只能由训练段拟合。
- 禁止把论文或复现包 CSV 中的数字当作"本实验实测"；所有指标必须由你的代码从冻结数据算出。
