# 科研任务（L2 端到端科研再发现）：单变量时序预测的"多视角评估"方法

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2406.16590_beyond_avg_forecast`
- 层级：L2（RCBench 对齐：input/output/scientific goal 三段式；目标论文隐藏，仅给数据与协议）
- 领域：CS / 时序预测 / 评估方法学

## 任务描述（三段式）

### Input（给定）

- `data/tsf/m3_monthly_dataset.tsf`、`m3_quarterly_dataset.tsf`、`m3_yearly_dataset.tsf`：M3 竞赛数据（合计 3,003 条单变量序列）
- `data/tsf/tourism_monthly_dataset.tsf`、`tourism_quarterly_dataset.tsf`、`tourism_yearly_dataset.tsf`：Tourism 竞赛数据（合计 1,311 条单变量序列）
- 格式：`.tsf`（头部 `@frequency` / `@horizon`；数据行 `series_name,start_timestamp:value1,value2,...`）。月度 H=18、季度 H=8、年度 H=6（与头部 `@horizon` 一致）。
- 数据为真实竞赛观测（M3 / Tourism Forecasting Competition），完整序列；按协议把每条序列**最后 H 个观测**留作测试。

### Output（必须产出）

1. **`method/`**：实现并训练**至少 2 类可运行的预测器**：
   - 一个**深度全局模型**（用全部序列联合训练的神经网络，如 NHITS / N-BEATS / TFT / 任意深度全局模型，框架不限；若用 NHITS，可参考 nixtla 默认配置）；
   - 至少 2 个**经典局部方法**（如 SNaive、Theta、ARIMA、ETS、RWD、SES，自选并说明配置/调参方式）。
2. **`protocols/`**：实现**多视角评估协议**的 SMAPE 计算（SMAPE 定义：`100%/n Σ |ŷ-y| / ((|ŷ|+|y|)/2)`）：
   - **Overall**：全部样本的聚合 SMAPE（单指标口径）；
   - **按 horizon**：每条序列测试期的第一个预测步（one-step-ahead）与最后一个预测步（multi-step-ahead）分开计算；
   - **按采样频率**：monthly / quarterly / yearly 分开计算；
   - **按条件**（自选至少 2 项）：困难问题（如以 SNaive 的 SMAPE 分布 95% 分位定义）与异常观测（如超出 SNaive 99% 预测区间的点）；
   - **Win/Loss 比率**：以序列为单位统计深度模型相对各经典方法的胜率（SMAPE 更小即胜）。
3. **`baselines/`**：季节性朴素（SNaive）必须实现并作为基准（用于困难问题/异常定义与对比）。
4. **`results/`**：每数据集 × 每视角 × 每方法的 SMAPE 表（`evidence_table.csv`）、关键指标（`metrics.json`）。
5. **`report.md`**：完整科研报告（见 Scientific Goal 的四个问题）。

### Scientific Goal（要回答的科学问题）

针对「把预测性能聚合成单一平均指标（如 Overall SMAPE）是否会稀释/隐藏模型相对性能信息」这一主题，回答：

1. **Q1 整体排名**：深度全局模型在 Overall SMAPE 上是否优于所有经典方法？经典方法中哪个最好？
2. **Q2 视角依赖**：把评估按 horizon（首步 vs 末步）与采样频率分解后，深度模型的相对优势是否随视角变化？它是否只在多步预测（末步）明显占优，而在一步预测（首步）与经典方法接近甚至更差？
3. **Q3 条件依赖**：在困难问题与异常观测上，深度模型的相对表现是否反转（被 ETS/SES/Theta 等经典方法超越）？Win/Loss 比率是否接近 50%（即深度模型并非稳定全胜）？
4. **Q4 你的发现**：基于上述证据，你支持还是反对「单一聚合指标会误导预测方法评估、多视角评估才能揭示真实相对性能」这一论断？给出四档结论标签：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 冻结真实数据（来源/许可/checksum 见 `data/SOURCE.md` 与 `data/source_manifest.json`）。
- 测试 = 每条序列最后 H 个观测（H 见各文件 `@horizon`）；测试值已在冻结数据内，训练/验证只能用测试段之前的观测。
- 禁止使用合成/模拟数据；禁止从网络下载其他版本数据（含 M4——本包未冻结，理由见 SOURCE.md）。
- 深度模型为全局训练（联合所有序列）或按数据集-频率分组训练均可，但必须在报告中声明；经典方法按局部（逐序列）建模。

## 数据铁律提醒

- 只用本包冻结数据；禁止合成数据替代。
- 时间顺序不得打乱；测试段（最后 H 个观测）禁止参与训练、验证或任何校准。
- 深度模型与经典方法必须在**相同测试协议**下比较（同一测试段、同一 SMAPE 口径）。
- 禁止把任何论文数字当作"本实验实测"；所有指标必须由你的代码从本包数据算出。