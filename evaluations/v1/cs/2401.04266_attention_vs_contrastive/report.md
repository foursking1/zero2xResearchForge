# EVAL REPORT: 2401.04266_attention_vs_contrastive（表格数据注意力 vs 对比学习）

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: WorkBuddy（LLM 裁判）
- 评测时间: 2026-08-14

## 总分: 87 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---|---|---|
| A 核心结果达成度 | 50 | 60 | 3 条 claim 全 supported：难度划分 23/28 一致（hard 10/14 + easy 13/14）、传统方法 easy 占优 11/14、无全局最优成立 |
| B 证据真实性 | 25 | 25 | 5 seeds × 28 数据集 × 3 模型全量实跑（577.7s）；evidence 表 28 行；spot_check.py 供裁判重算 |
| C 方法与报告 | 12 | 15 | 协议严谨（train-only 拟合统计量、分层切分、macro-F1）；MLP 代理边界诚实标注 |

## A 核心结果达成度（50/60）

### claim (a) 难度划分可恢复（✅）
- 锚：hard≥10/14 & easy≥11/14（论文自身 12/14 + 14/14）
- agent：**hard 10/14 + easy 13/14 = 23/28**，方向稳健（hard 中位 gap +11.5pp vs easy −0.9pp）
- 边界集（cmc/pc4）与论文自身同样不达标——agent 发现这与论文一致 ✅

### claim (b) 传统方法 easy 占优（✅）
- 锚：easy 组 LR/GBT ≥ MLP 的数据集 ≥8/14
- agent：**11/14**，MLP 仅 3 个数据集小幅反超（+32pp 仅 1 个）✅

### claim (c) 无全局最优方法（✅ 带边界）
- MLP 代理在 hard 组仅胜 GBT 3/14（≤7/14 达标）
- **诚实标注**：论文的 hard 占优结论依赖 SAINT/NPT（attention/contrastive 模型），本任务未训练，MLP 代理"既不支撑也不证伪"——这是极高水平的边界声明

### A3 平均秩核对
- 论文 SAINT 3.58 最优 / LR 10.46 最差；agent 未训练 SAINT，仅用 LR/GBT/MLP——A3 部分适用（降为辅助）

## B 证据真实性（25/25）

- 主运行 `run_benchmark.py` 577.7s（5 seeds × 28 × 3），per_seed.csv 全明细
- 预处理严谨：统计量只从 train 拟合（median 插补 + StandardScaler + OneHotEncoder），无泄漏
- evidence_table 28 行；spot_check.py 供裁判独立重算（抽 4538_gesture：LR 34.46 / GBT 61.60 / MLP 53.16 自洽）

## C 方法与报告（12/15）

- C1 方法（5/5）：70/10/20 分层切分、5 seeds 取均值、macro-F1、gap≥4pp 难度定义——与论文 Table 6 协议一致
- C2 稳健性（5/5）：5 seeds 明细 + 中位数 gap 报告（hard +11.5 vs easy −0.9）
- C3 报告（3/5）：结论表 + 边界声明优秀；但"SAINT 未训练"对 A3 平均秩锚的适用性讨论可更充分

## 结论

- **科学结论**：`supported`（3 条 claim 全过）——难度划分可恢复、传统方法在 easy 组占优、无全局最优方法
- agent 的执行与论文 §5.1/§5.3 的方向性结论高度一致，且对 DNN 代理的边界声明是加分项（避免过度声明）
- 备注：本卡为 L1（critical claim）型，锚以方向/容差判分，agent 全部命中
