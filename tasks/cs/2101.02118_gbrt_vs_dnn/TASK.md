# 科研任务：窗口化 GBRT 能否匹敌深度时序预测模型（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id: `2101.02118_gbrt_vs_dnn`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Do We Really Need Deep Learning Models for Time Series Forecasting?（arXiv:2101.02118v2，Elsayed, Thyssens, Rashed, Jomaa, Schmidt-Thieme，Universität Hildesheim）
- 领域：CS / 时序预测（窗口回归 vs 深度模型）

## 问题（可证伪）

论文将单变量时序预测重构为「窗口化多输出回归」（lookback w=24，预测 h=24，输入 = 展平的 w 个历史目标值，多输出 GBRT），并声称在多个公开数据集上这一简单 GBRT 能匹敌乃至超越 2016-2020 年顶会深度模型。基于冻结数据验证以下三个 claim：

1. **claim A（Exchange-Rate）**：在 8 条日度汇率序列（1990-2016）上，窗口化 GBRT 测试段 RMSE≈0.017、WAPE≈0.013，为论文表 2 六模型中最低，且显著优于朴素 GBRT（0.081/0.456）与 ARIMA（0.123/0.170）——RMSE 差距约 4.8-7.2 倍。
2. **claim B（Electricity）**：在 321 条小时级用电序列（2012-2014，论文子采样 n=70）上，窗口化 GBRT RMSE≈125.6，为表 2 六模型中最低，低于朴素 GBRT（523.8，约 4.2 倍）与 ARIMA（181.2）。
3. **claim C（辅助，Solar-Energy）**：窗口化 GBRT 在 Solar-Energy 上的 RSE≈0.455 < LSTNet 0.464、Corr≈0.896 > 0.887（表 4，h=24）。

可证伪表述：(a)「窗口化能显著提升 GBRT——RMSE 相对朴素 GBRT 降幅 ≥ 3 倍」是否成立；(b)「窗口化 GBRT 的 RMSE 不高于 ARIMA 与（论文报告的）DNN 基线」是否成立；(c) Solar-Energy 上窗口化 GBRT 的 RSE/Corr 是否优于 LSTNet。

## 方向提示（非方法步骤）

- 数据与划分（论文表 1 协议）：
  - `exchange_rate`：8 条序列，每条丢弃最前 52 行得 7,536 时点；训练 t′=6,048、测试 τ=1,488。
  - `solar_AL`：137 条，训练 42,048、测试 10,512（原始 52,560 恰好等于 t′+τ）。
  - `electricity`：321 条，每条丢弃最前 168 行得 26,136 时点；训练 25,968、测试 168。论文用 n=70 子采样；可用固定种子子采样 70 条，或使用全部 321 条（报告中说明口径）。
  - `traffic`（可选）：862 条，论文子采样 n=90、T=10,560（训练 10,392、测试 168）；原始 17,544 行需固定种子选 90 条并取最后 10,560 时点。
- 逐序列独立：把 n 条序列视为 n 个独立单变量预测问题（论文 §5.2）；指标在全部序列测试段的聚合上计算：RMSE=sqrt(mean((ŷ−y)²))、WAPE=Σ|ŷ−y|/Σ|y|、MAE=mean(|ŷ−y|)。
- 窗口化：滑窗构造样本，x = 展平 w=24 个历史目标值，y = 未来 h=24 个目标值；对每个 horizon 步训练一个回归器（论文 §4 单目标变换），或使用原生多输出 GBRT（如 `sklearn.MultiOutputRegressor` + `HistGradientBoostingRegressor`、XGBoost）。
- 基线：GBRT(Naive)——在完整训练段上拟合点对点回归（输入 t 时刻目标值、预测同一点，论文 §4 公式 2），再对测试段滚动预测；ARIMA——逐序列拟合（pmdarima/auto_arima 或 statsmodels），滚动预测。
- 时间协变量可选（表 3 显示加入简单时间协变量有额外增益）；claim A/B 对应表 2 的**无协变量**结果。
- 防泄漏：窗口构造与任何标准化/缩放统计量只由 t′ 训练段拟合；测试段 τ 禁止参与训练、验证或校准。

## 数据说明

- 冻结数据（来源/许可/checksum 见 `data/SOURCE.md` 与 `data/source_manifest.json`），共 4 个 gzip 文本文件：
  - `$PAPER_BENCH_DATA_DIR/data/exchange_rate.txt.gz`（7,588 时点 × 8 国日度汇率）
  - `$PAPER_BENCH_DATA_DIR/data/solar_AL.txt.gz`（52,560 × 137 PV 电站，10 分钟）
  - `$PAPER_BENCH_DATA_DIR/data/electricity.txt.gz`（26,304 × 321 客户，小时级）
  - `$PAPER_BENCH_DATA_DIR/data/traffic.txt.gz`（17,544 × 862 传感器，小时级）
- 格式：gzip 压缩的逗号分隔数值文本，无表头；每行 = 一个时点，每列 = 一条序列/传感器。
- 读取：`import gzip; rows = [ [float(v) for v in line.split(",")] for line in gzip.open(path, "rt") ]`；行序为时间顺序。
- 来源：Lai et al.（LSTNet, SIGIR 2018）官方数据仓库 `https://github.com/laiguokun/multivariate-time-series-data`（master 分支，2026-08-13 冻结）；原始数据为 UCI ElectricityLoadDiagrams20112014、Caltrans PEMS、NREL Solar Power、公开汇率数据。
- 禁止下载其他版本数据；禁止合成/模拟数据替代。

## 输出要求（提交物）

1. **结论**：对 claim A/B/C 分别给出 `supported / partially_supported / contradicted / inconclusive`，并说明证据强度。
2. **证据表** `results/evidence_table.csv`：至少含列 `dataset / model / rmse / wape / mae`；覆盖 GBRT(W-b)、GBRT(Naive)、ARIMA 三模型 × exchange_rate/solar_AL/electricity 三数据集；若复现 DNN（LSTNet/TRMF/DARNN）或引用论文数值，须在报告中注明。
3. **代码**：完整可复现的训练/评估脚本（含固定随机种子），从冻结 gz 读取数据、构造窗口、训练与评估。
4. **报告** `report.md`：方法（模型、窗口构造、训练设置与超参）、子采样与聚合口径、防泄漏说明、局限性（与论文 XGBoost 实现及子采样的差异、算力）。

## 数据铁律提醒

- 只用本包冻结数据；禁止合成/模拟数据替代。
- 训练只用 t′ 段；测试段 τ（所有序列的测试时点）禁止参与训练、验证或校准。
- 禁止把论文数值当作「本实验实测」；所有指标必须由你的代码从冻结数据算出。
