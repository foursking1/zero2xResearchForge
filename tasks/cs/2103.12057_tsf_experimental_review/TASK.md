# 科研任务：时间序列预测中序列深度模型 vs MLP 基线（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id: `2103.12057_tsf_experimental_review`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：An Experimental Review on Deep Learning Architectures for Time Series Forecasting（arXiv:2103.12057；IJNS 31(03) 2130001, 2021）
- 领域：CS / 时间序列预测 / 深度学习实验研究

## 问题（可证伪）

在论文使用的真实时间序列数据集 **M3 月度**（1,428 条序列，预测长度 18 个月）上，验证论文的核心结论之一：

**序列感知深度模型显著优于前馈 MLP 基线 claim**：在相同的滑窗/固定起点协议下，递归/卷积深度架构（GRU、LSTM、CNN、TCN）的最佳 WAPE 显著低于 MLP。论文报告（Table 11，M3 列）：**GRU = 15.18、LSTM = 15.28、TCN = 15.59、CNN = 15.61、ERNN = 15.62、ESN = 17.18、MLP = 21.11**——MLP 是 7 种架构中最差。

可证伪表述：基于冻结数据，(a) "序列感知模型（GRU/LSTM/CNN/TCN 任一）的 WAPE 显著低于 MLP（方向性）" 是否成立；(b) "GRU/LSTM 最佳 WAPE 落在 15.2 ± 2 附近" 是否成立；(c) "MLP 最佳 WAPE 落在 21.1 ± 3 附近且为最差架构" 是否成立。

## 方向提示（非方法步骤）

- 指标：WAPE（加权绝对百分比误差），越低越好。定义：`WAPE(y, o) = mean(|y − o|) / mean(y)`，逐序列计算，再对 1,428 条测试序列取平均（论文 §3.3.1 / 官方仓库 metrics.py）。
- 划分：固定起点（fixed origin）——每条序列最后 18 个观测 = test，其余 = train（论文 §3.3 Evaluation procedure）。
- 预处理：逐序列归一化（min-max 或 z-score），归一化统计量只能由该序列 train 段拟合；test 段用同一统计量变换（论文 §3.3 / 仓库 preprocessing.py）。
- 数据组织（MIMO）：滑窗构造 (input, output) 实例，input = 最近 `past_history` 个值，output = 未来 18 个值（一步输出完整预测向量）。论文用 `past_history = int(18 × 1.25) = 22`（仓库 generate_data.py），也可试 36/54（×2/×3）。
- 模型：GRU/LSTM（1-2 层，32-128 单元 + 18 神经元 Dense 输出）对比 MLP（如 [32,64,128] 隐层 + 18 输出）；Adam，lr 0.001，batch 32 或 64，epochs 5-20（论文官方用 5 epochs + max_steps_per_epoch=10,000；可适当加长）。
- 聚合口径：每条序列一个 WAPE，全部测试序列取均值（跳过 test 全零或近似常量的序列，见仓库 metrics.py）。
- 防泄漏：归一化统计量仅 train 拟合；test 最后 18 个观测不得进入任何窗口/训练；模型选择可用小验证集或少量配置网格，但不得用 test 调参。

## 数据说明

- 数据包：`$PAPER_BENCH_DATA_DIR/tsf`（M3 月度官方单变量序列，Monash Time Series Forecasting Repository 公开发布，研究用途）
  - `m3_monthly_dataset.tsf`：960,208 字节，原始 .tsf 格式（头部含 `@frequency monthly`、`@horizon 18`；1,428 条完整序列，长度 66-144）
  - `m3_monthly_series.csv`：2,712,020 字节，解析后的整洁格式，列 = `series_id`（0000-1427）/ `pos`（0 起）/ `value`
- 协议拆分：每条序列取最后 18 个观测为 test，其余为 train（对应论文固定起点方案；train 段长度 48-126，与论文 Table 8 的 M=126/m=48 一致）。
- 来源：Monash Time Series Forecasting Repository（forecastingdata.org，Zenodo 4656298，.tsf 版）；数据本体为 M3 Competition（Makridakis & Hibon 2000）官方单变量月度序列。
- checksum（sha256）：
  - `m3_monthly_dataset.tsf` = `962E5E217D3C98780EF240416DAA4773A8E65961EA47E0A769178BE58622D9C5`
  - `m3_monthly_series.csv` = `423BE54C3CB45A9641B259EC36B4653A0F153172B1FD386103529E67432B33F3`
- 逐文件 SHA-256 登记：`$PAPER_BENCH_DATA_ROOT/checksums.sha256`。

## 输出要求（提交物）

1. **结论**：对上述三个 claim 分别给出 `supported / partially_supported / contradicted / inconclusive`，并说明数据支持的强度。
2. **证据表**：`results/evidence_table.csv`（或等价表格），至少含列：`model`（gru / lstm / cnn / tcn / mlp 等）、`past_history`、`n_series`（参与平均的序列数）、`wape`（平均 WAPE）、`mae_mean`、`target_mean_mean`；另报告 `wape_gap_mlp`（MLP − 最佳序列模型）。
3. **代码**：完整可复现的训练/评估脚本（含固定随机种子），从冻结文件读取数据。
4. **报告**：`report.md`：方法（拆分、归一化、滑窗、模型与超参）、防泄漏说明、局限性（单/少配置 vs 论文全网格 6,432 配置、5 epochs vs 更长训练）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成/模拟数据替代。
- test 段（每条序列最后 18 个观测）只用于最终评估；禁止进入训练窗口或用于归一化统计量拟合。
- 报告中必须说明与论文全量实验（6432 配置 × 7 架构、best-over-grid）的差异。
