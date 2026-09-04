# 科研任务（L2 端到端科研再发现）：多变量时序异常检测的评估协议问题

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2308.13068_mvts_flawed_eval`
- 层级：L2（RCBench 对齐：input/output/scientific goal 三段式；目标论文隐藏，仅给原始数据）
- 领域：CS / 多变量时间序列异常检测 / 评估方法学

## 任务描述（三段式）

### Input（给定）

- `data/SWaT_SWaT_train.npy`：SWaT 数据集训练段（N=473,399 × 51 维传感器读数，float32，正常段）
- `data/SWaT_SWaT_test.npy`：SWaT 测试段（N=449,919 × 51 维）
- `data/SWaT_SWaT_test_label.npy`：SWaT 测试标签（0=正常，1=异常）
- `data/PSM_train.csv`：PSM 数据集训练段（132,481 × 26 列，含 NaN 需处理）
- `data/PSM_test.csv`：PSM 测试段（87,841 × 26 列）
- `data/PSM_test_label.csv`：PSM 测试标签（第 1 列 `timestamp_(min)`，第 2 列 0/1 标签）

两个数据集都是**真实工业/服务器系统传感器时序**：SWaT（水处理厂，51 通道）、PSM（eBay 服务器性能指标，26 通道）。测试段按时间连续，异常以连续事件段出现（可用标签连续性恢复事件）。

### Output（必须产出）

1. **`method/`**：实现并训练**至少 2 个可运行的异常检测器**：
   - 一个**简单无监督基线**（如 PCA 重建误差、协方差马氏距离等，自选并说明）；
   - 一个**深度学习/复杂方法**（如自编码器重建误差、LSTM/GRU 预测误差、Transformer 类自选，框架不限但必须可离线训练）。
2. **`protocols/`**：实现**两种评估协议**的 F1 计算：
   - 逐点（point-wise）F1：逐点比较预测/标签；
   - point-adjust F1：只要一个异常事件段内至少检出 1 个点，就把该段全部计为检出（TP 扩展到整段）。
3. **`baselines/`**：实现**随机猜测基线**——从测试段随机选取固定比例（如 α=1000 点，或按测试段 ~1%）标为异常，计算其在两种协议下的 F1（建议多次随机重复取均值）。
4. **`results/`**：每数据集 × 每方法 × 每协议的 F1 表（`evidence_table.csv`）、关键指标（`metrics.json`）。
5. **`report.md`**：完整科研报告（见 Scientific Goal 的四个问题）。

### Scientific Goal（要回答的科学问题）

针对「多变量时序异常检测的评估方式是否扭曲了我们对算法的认知」这一主题，回答：

1. **Q1 协议可操纵性**：随机猜测（无任何学习）在 point-adjust 协议下的 F1 有多高？与逐点协议下的 F1 差距多大？是否显著高于某些"复杂"方法的逐点 F1？
2. **Q2 简单 vs 复杂**：简单无监督基线（如 PCA）与你的深度方法在**逐点 F1** 上谁更高？差距多大？
3. **Q3 协议对结论的影响**：同一方法在 point-adjust 与逐点协议下的 F1 差异多大？若只用 point-adjust 比较方法，结论是否会被误导（排序/差距变化）？
4. **Q4 你的发现**：基于上述证据，你支持还是反对「评估协议是异常检测领域结论混乱的主要来源」这一论断？给出四档结论标签：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 冻结真实数据（来源与许可见 `data/SOURCE.md`，SHA-256 固定于 `data/source_manifest.json`）
- 禁止使用合成/模拟数据；禁止从网络下载其他版本数据
- 训练只用 `*_train` 段；测试/标签只用于最终评估，不得参与训练或阈值拟合（阈值选择方式须在报告中说明，允许在测试段上按最优逐点 F1 选阈值——但必须明确声明这是"oracle 阈值"口径，且另报固定阈值/训练段阈值结果）
- NaN 处理方式须说明（PSM 训练段含 NaN）

## 数据铁律提醒

- 只用本包冻结数据；禁止合成数据替代。
- 时间序列不得混洗乱序；训练/测试按给定顺序使用。
- 随机猜测基线必须使用真随机（固定种子可复现）。
- 禁止把任何论文数字当作"本实验实测"；所有指标必须由你的代码从本包数据算出。