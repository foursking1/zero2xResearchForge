# 科研任务：voraus-AD 机器人时序异常检测（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id: `2311.04765_voraus_ad`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：The voraus-AD Dataset for Anomaly Detection in Robot Applications（arXiv:2311.04765，IEEE T-RO）
- 领域：CS / 机器人时序异常检测

## 问题（可证伪）

在冻结的 voraus-AD 真实机器人时序数据（pick-and-place 应用，6 轴协作机械臂机器数据）上，验证论文的三个核心结论：

1. **可检测性 claim**：仅用正常样本训练的半监督异常检测方法，在 12 类异常上逐类评估的平均 AUROC 显著高于随机（50%），强方法可达 90 以上（论文最强基线 MVT-Flow 平均 AUROC = 93.6，Table VI）。
2. **相对优势 claim**：基于深度密度估计/重构的 AD 方法（正常流/自编码器类）平均 AUROC 明显优于简单基线（PCA、1-NN）——论文报告 MVT-Flow 平均 93.6，超最佳基线 HMM 87.4（+6.2pp）、超 PCA 80.0（+13.6pp）、超 1-NN 77.5（+16.1pp）。
3. **类别特异性 claim**（辅助）：不同异常类型的可检测性差异大；论文观察到简单方法（PCA/1-NN/CAE）在 miss_can（未抓取罐体）上 AUROC=100.0，而 MVT-Flow 在 entangled（机器人上缠绕线缆）/ invalid_position（异常抓取位置）上 AUROC=100.0——这些类别特异性模式是否在你的结果中复现？

可证伪表述：基于冻结数据，(a) \"半监督方法 12 类平均 AUROC ≥ 80\" 是否成立；(b) \"深度密度/重构方法平均 AUROC 显著优于 PCA/1-NN 基线\" 是否成立；(c) 论文报告的类别特异性模式（简单方法在 miss_can 上接近完美、entangled/invalid_position 对强深度方法接近完美）是否成立。

## 方向提示（非方法步骤）

- 指标：AUROC（论文主指标，§V-A）。逐异常类别计算（每类异常样本为正、全部测试正常样本为负），再对 12 类取平均；**禁止**用全体样本单条 ROC（论文明确不推荐：各类样本数不平衡会偏置指标）。
- 数据划分（论文 §III-C 官方协议）：训练 = `setting == 72`（PRE_A 阶段，948 条正常样本）；测试 = 其余全部（setting ≠ 72：419 条正常 + 755 条异常）。训练集只含正常样本（半监督 AD 设定）。
- 信号：130 个机器信号（6 轴 × 21 + 4 个通用电气信号 robot_voltage/robot_current/io_current/system_current），剔除元数据列（time/sample/anomaly/category/setting/action/active）；评估采样率 100 Hz；样本按最大长度零填充（论文 §V-B）。
- 模型方向：正常流密度估计（如论文 MVT-Flow，§V-B1 超参：4 coupling blocks、70 epochs、lr 8e-4、batch 32）或等价深度密度/重构方法（LSTM-VAE/AE/CAE）；建议同时实现 PCA 与 1-NN 简单基线以验证相对优势 claim。
- 防泄漏：标准化统计量只能由训练样本拟合；测试样本（含正常测试样本）不得参与训练、验证或任何校准；anomaly/category 标签只用于评估，不用于训练。

## 数据说明

- 数据包（冻结，来源/许可/checksum 见 `data/SOURCE.md` 与 `data/source_manifest.json`）：
  - `$PAPER_BENCH_DATA_DIR/voraus-ad-dataset-100hz.parquet`（1,115,942,833 字节，sha256 见 manifest）
  - 规模：2,321,690 行 × 137 列；2,122 条样本（sample 0-2121）= 948 训练正常 + 419 测试正常 + 755 异常
  - 12 类异常（`category` 列）：0 axis_friction / 1 axis_weight / 2 collision_foam / 3 collision_cable / 4 collision_carton / 5 miss_can / 6 lose_can / 7 can_weight / 8 entangled / 9 invalid_position / 10 motor_commutation / 11 wobbling_station；`category==12` 为正常
  - schema 关键列：`time`(秒)、`sample`(样本 ID)、`anomaly`(bool)、`category`(int)、`setting`(int)、`action`(int)、`active`(int)、130 个机器信号（`target_position_N`/`target_velocity_N`/`target_torque_N`/`motor_position_N`/`motor_velocity_N`/`joint_position_N`/`joint_velocity_N`/`motor_torque_N`/`torque_sensor_a_N`/`torque_sensor_b_N`/`motor_iq_N`/`motor_id_N`/`power_motor_el_N`/`power_motor_mech_N`/`power_load_mech_N`/`motor_voltage_N`/`supply_voltage_N`/`brake_voltage_N` 等，N=1..6 轴）
  - 读取：`pandas.read_parquet(...)`；按 `sample` 列分组即得逐样本时序
- 来源：voraus-AD 官方发布（voraus robotik GmbH / Leibniz Universität Hannover / Linköping University）；官方仓库 https://github.com/vorausrobotik/voraus-ad-dataset（仓库代码 MIT，数据集 CC BY-NC-SA 4.0）；100 Hz 版本官方直链 media.vorausrobotik.com。
- 许可：CC BY-NC-SA 4.0（署名、非商业、相同方式共享）；本包仅用于学术研究评测。
- 禁止下载其他版本数据（500 Hz 未冻结）；禁止合成/模拟数据替代。

## 输出要求（提交物）

1. **结论**：对 claim (a)(b)(c) 分别给出 `supported / partially_supported / contradicted / inconclusive`，并说明数据支持的强度。
2. **证据表**：`results/evidence_table.csv`（或等价表格），至少含列：`category_id`、`category_name`、`n_anomaly`、`auroc_main`（你的主方法）、`auroc_pca`、`auroc_1nn`（或等价基线列）；另报告 12 类平均 AUROC 与相对基线的差值。
3. **代码**：完整可复现的训练/评估脚本（含固定随机种子），从冻结 parquet 读取数据。
4. **报告**：`report.md`：方法（模型、预处理、训练设置、超参）、防泄漏说明、局限性（与论文 MVT-Flow 实现的差异、运行资源/GPU）。

## 数据铁律提醒

- 只用本包冻结数据；禁止合成/模拟数据替代。
- 训练只允许用 `setting==72` 的正常样本；测试样本（含正常测试样本）禁止参与训练、验证或校准。
- anomaly/category 标签只用于评估；标准化/归一化统计量只能由训练样本拟合。
- 禁止把任何论文数字当作\"本实验实测\"；所有指标必须由你的代码从冻结数据算出。
