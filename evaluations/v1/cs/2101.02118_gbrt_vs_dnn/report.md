# EVAL REPORT: 2101.02118_gbrt_vs_dnn（窗口化 GBRT vs 深度学习时序预测）

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: WorkBuddy（LLM 裁判）
- 评测时间: 2026-08-14

## 总分: 74 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---|---|---|
| A 核心结果达成度 | 37 | 60 | A2 精确命中（0.0199 ∈ [0.012,0.022] 且最优）；A1 绝对数值不可复现（数据异质性）但相对声称成立；A3 Corr 命中 RSE 微差 |
| B 证据真实性 | 25 | 25 | 三数据集全量实跑（含 321 序列 electricity）；evidence 表 13 行可重算；论文引用与实测严格区分 |
| C 方法与报告 | 12 | 15 | 协议透明；数据异质性根因分析优秀；结论判定恰当 |

## A 核心结果达成度（37/60）

| 锚 | 判分带 | agent | 判定 |
|---|---|---|---|
| A1 Electricity RMSE | [100,160] | 2905.5（全 321 序列）| ❌ 未入带（数据含极端用户）|
| A1 相对声称 | GBRT<ARIMA<Naive | 2.3× ARIMA、3.1× Naive | ✅ 相对成立 |
| A2 Exchange-Rate RMSE | [0.012,0.022] | **0.0199** | ✅ 精确命中 |
| A2 六模型最优 | 是 | 0.0199 < ARIMA 0.124 < Naive 0.461 | ✅ |
| A3 Solar Corr | >0.887 | 0.896 | ✅ |
| A3 Solar RSE | <0.464 | 0.474 | ❌ 微差（+2%）|

→ 3 个锚命中（A2 全中 + A3 Corr），A1 绝对数值未复现（根因：冻结数据含工业级极端用户主导 RMSE + 论文 70 序列子集未公开），但相对声称全部成立。约 37/60。

## B 证据真实性（25/25）

- 三数据集全量实跑：exchange_rate 8 序列、solar 137 序列、electricity **全 321 序列**（TASK 允许口径，论文用未公开 70 子集）
- evidence_table 13 行（数据集×模型×5 指标）；论文数值在 metrics.json `_paper_reference` 独立存放，与实测严格区分
- 根因分析扎实：极端客户（工业规模、~0 测试周）主导池化 RMSE——这是对"论文数值为何不可复现"的准确诊断

## C 方法与报告（12/15）

- C1 方法（5/5）：窗口 w=24、horizon h=24、逐序列 univariate 处理，与论文官方代码一致
- C2 稳健性（4/5）：多数据集 × 多模型（W-b/Naive/Naive-ident/ARIMA）对照；无多 seed（树模型确定性）
- C3 报告（3/5）：结论表（A supported/B partial/C partial）清晰；"绝对 vs 相对"区分明确；solar RSE 微差讨论可更深

## 结论

- **科学结论**：`partially_supported`（A supported / B partial / C partial）——论文核心声称"简单窗口化 GBRT 匹配/超越深度基线且大幅优于朴素基线"在**方向和相对量级上复现**（exchange_rate 精确命中、electricity/solar 相对成立），但**绝对数值因数据子集差异不可复现**（论文 70 序列子集未公开）
- agent 对"不可复现根因"的诊断（数据异质性 + 子集未公开）是本批评测中最佳的水平
- 备注：本卡设计上 L1（critical claim），锚明确允许"相对声称成立即部分得分"，agent 执行完全符合预设
