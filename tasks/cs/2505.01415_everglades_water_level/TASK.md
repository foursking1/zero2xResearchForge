# 科研任务：Everglades 水文水位预测模型评估（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id: `2505.01415_everglades_water_level`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：How Effective are Large Time Series Models in Hydrology? A Study on Water Level Forecasting in Everglades（arXiv:2505.01415）
- 领域：CS / 时序预测 / 水文应用

## 问题（可证伪）

在冻结的 Everglades 真实水文时序数据（5 个目标站点水位 + 30+ 协变量，日频）上，验证论文的三个核心结论（锚值见 Table 1，Overall MAE）：

1. **任务特定模型架构差异 claim**：28 天前预测的 Overall MAE 随架构显著变化——MLP（NBEATS 0.176）与 Transformer（PatchTST 0.193）显著优于线性模型（DLinear 0.392）；即\"MLP/Transformer 类 < 线性类\"的排序是否成立。
2. **线性模型长 horizon 退化 claim**：线性模型短 horizon（7 天）尚可（NLinear 0.108 / DLinear 0.095），随 horizon 增至 28 天大幅退化（NLinear 0.185 / DLinear 0.392），而 NBEATS 退化更缓（0.076 → 0.176）。
3. **零样本基础模型 claim**（如可运行 Chronos）：时序基础模型 Chronos 显著优于所有任务特定模型（28 天 Overall MAE 0.088 vs 最佳任务特定 NBEATS 0.176；7 天 0.049 vs 0.076）。

可证伪表述：基于冻结数据，(a) \"28 天 horizon 下 MLP/Transformer 类任务特定模型 Overall MAE 显著低于线性类\" 是否成立；(b) \"线性模型 7 天 → 28 天 Overall MAE 显著增长（相对增幅 ≥50%）\" 是否成立；(c) \"零样本 Chronos 的 28 天 Overall MAE 显著低于所有任务特定模型（差距 ≥0.05）\" 是否成立。

## 方向提示（非方法步骤）

- 指标：MAE 与 RMSE（论文 §3.1 主指标）；按 5 站点 × 4 lead time（7/14/21/28 天）分别计算，Overall = 5 站点 MAE 均值（论文 Table 1 口径）。
- 数据划分（论文 §3.1 官方协议）：训练 = 前 1,200 天（2020-10-16 → 2023-07-01）；验证 ≈ 211 天；测试 = 最后 211 天（2024-01-29 → 2024-08-26）。测试段禁止参与训练/验证/早停。
- 任务设定（论文 §3.1）：输入 = 前 100 天全部变量（37 列），预测 5 个目标站点（NP205_stage、P33_stage、G620_water_level、NESRS1、NESRS2）未来 7/14/21/28 天；测试期按日滚动评估（每个测试日用其前 100 天作输入）。
- 模型方向：至少实现 1 个线性类（NLinear/DLinear，neuralforecast 或自实现均可）与 1 个 MLP/深度类（NBEATS 或等价）；可选实现零样本基础模型 Chronos（pip `chronos-forecasting` 或 `autogluon.timeseries`，官方权重，零样本不微调）。
- 防泄漏：特征标准化/归一化统计量只能由训练段拟合；测试期与验证期禁止用于训练；滚动窗口只能使用目标日之前的观测。

## 数据说明

- 数据包（冻结，来源/许可/checksum 见 `data/SOURCE.md` 与 `data/source_manifest.json`）：
  - `$PAPER_BENCH_DATA_DIR/final_concatenated_data.csv`（261,603 字节，sha256 见 manifest）
  - schema：1,411 行 × 39 列（含 `Unnamed: 0` 行索引与 `date`）；37 个变量列：目标站点 `NP205_stage`/`P33_stage`/`G620_water_level`/`NESRS1`/`NESRS2` + 协变量（S199/S200/S332B/.../NP205_rain/P33_rain/NP205_PET/P33_PET/SWEVER4_stage/TSH_stage/NP62_stage 等，含流量、雨量、蒸散、其它站点水位）；日期 2020-10-16 → 2024-08-26，日频，无缺失。
  - 读取：`pandas.read_csv(...)`；日期解析后按论文协议切分。
- 来源：Everglades-Benchmark 官方仓库 https://github.com/rahuul2992000/Everglades-Benchmark （`data/final_concatenated_data.csv`）；原始数据来自 DBHYDRO（South Florida Water Management District）与 Everglades National Park（NPS）公开环境监测数据。
- 许可：论文附录声明数据公开、允许研究用途免费使用；DBHYDRO 环境监测数据为公开数据。本包仅用于学术研究评测。
- 禁止下载其他版本数据；禁止合成/模拟数据替代；禁止把官方仓库的 Results-28days-final.xlsx（模型预测结果）当冻结数据使用（那是论文模型输出，不是原始数据；本包未冻结）。

## 输出要求（提交物）

1. **结论**：对 claim (a)(b)(c) 分别给出 `supported / partially_supported / contradicted / inconclusive`，并说明数据支持的强度。
2. **证据表**：`results/evidence_table.csv`（或等价表格），至少含列：`model`、`lead_time`（7/14/21/28）、`overall_mae`、`overall_rmse`，以及每站点 MAE 或 NP205 站 MAE 列；另报告相对排序与退化幅度。
3. **代码**：完整可复现的训练/评估脚本（含固定随机种子），从冻结 CSV 读取数据。
4. **报告**：`report.md`：方法（模型、预处理、超参、训练设置）、防泄漏说明、局限性（与论文 neuralforecast 管线的差异、是否运行 Chronos、资源）。

## 数据铁律提醒

- 只用本包冻结数据；禁止合成/模拟数据替代。
- 测试段（最后 211 天）禁止参与训练、验证、早停或任何校准。
- 标准化统计量只能由训练段拟合；滚动窗口只能用目标日之前的观测（无未来信息）。
- 禁止把任何论文数字当作\"本实验实测\"；所有指标必须由你的代码从冻结数据算出。
