# 科研任务：检验「MALA 局域电子结构模型跨尺度外推保持化学精度」关键论断（L2）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2210.11343_mala_size_transfer`
- 层级：L2（卡标 L2→L2 题：方法复现 + 跨尺度外推验证）
- 论文：Pineda Flores et al., "Predicting electronic structures at any length scale with machine learning", arXiv:2210.11343（npj Comput. Mater. 9, 115 (2023)）
- 领域：materials / 机器学习电子结构（MALA）/ 跨尺度外推

## 问题（可证伪）

论文提出 MALA（Machine Learning of Atomic-scale Local Descriptors）方法：在局域轨道基上学习 DFT 电子密度/局域态密度，并演示了**跨尺度外推**——用 256 个 Be 原子训练的模型直接预测 512 / 1,024 / 2,048 原子体系，误差不随体系增大而发散。核心论断：
1. **跨尺度外推**：模型在 256 原子（平衡密度 1.896 g/cc）训练；对 256/512/1,024/2,048 原子体系，总能绝对误差与电子密度 MAPE 基本不随尺寸增长，**总能误差保持在化学精度（<43 meV/atom）以内，且通常 <10 meV/atom**；电子密度误差 <1%。
2. **大体系演示**：用 131,072 个 Be 原子（含堆垛层错）演示 DFT 无法触及的尺度，能量差异可分辨。
3. **速度提升**：相比 DFT，MALA 推理可带来最高三个数量级（up to three orders of magnitude）的速度提升。
4. **工作流**：模型含 3 个组件——LDS（局部描述符）/LDOS 预测网络、能量回归器、密度回归器；标定器（iscaler/oscaler）用于能量/密度尺度。

请基于冻结数据回答：

1. **数据与模型**：解析冻结包（rodare 1851 `size_transfer_cleaned`）：`trained_models/beryllium/`（`beryllium.network.pth`、`beryllium.iscaler.pkl`、`beryllium.oscaler.pkl`、`beryllium.params.json`）+ `model_training/training.py` + `model_inference/run_inference.py` + `data_analysis/calculate_rdf.py`。核对模型参数（params.json：结构/超参/体系信息）。
2. **推理复现（核心）**：按 `run_inference.py` 对 256/512/1,024/2,048 原子 Be 体系执行推理（或与论文公开结果对照），报告总能（eV/atom）与电子密度 MAPE 随体系尺寸的变化；验证「误差不随尺寸发散、总能 <43 meV/atom（化学精度）且 <10 meV/atom（金标准）、密度 <1%」的方向性。
3. **RDF 验证（可选）**：用 `calculate_rdf.py` 对比 256 与 2,048 原子体系的径向分布函数（论文 Figure 5）。
4. **验证论文论断**：结合自身结果给出四档结论。

- 结论标签：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结）→ 物理位置 `$PAPER_BENCH_DATA_DIR`（来源/许可/逐文件 SHA-256 见 `data/SOURCE.md` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 文件：`README.md`；`trained_models/beryllium/`（4 文件：网络权重 `.pth`、输入/输出标定器 `.pkl`、参数 `params.json`）；`model_training/training.py`；`model_inference/run_inference.py`；`data_analysis/calculate_rdf.py`。
- 来源：PSI（Paul Scherrer Institute）rodare 开放库记录 1851（`size_transfer_cleaned`），论文 Data Availability 指定。
- 规模：~6.3MB；推理需 PyTorch + MALA 依赖（`pip install mala` 或按 `run_inference.py` 环境），CPU 可跑（256–2,048 原子分钟级）。

## 方向提示（协议建议）

1. **依赖**：`pip install mala`（MALA 包，含数据/模型 IO）；权重为 PyTorch 格式。
2. **输入结构**：`run_inference.py` 默认加载论文同源 Be 结构；若网络访问受限，可用 ASE/pymatgen 构造 256/512/1,024/2,048 原子 Be 晶胞并说明差异。
3. **指标**：总能 MAE（meV/atom）、电子密度 MAPE（%）；256 为基准，报告 512/1,024/2,048 的相对漂移。
4. **对照**：论文 Figure 4（误差随尺寸）与正文（<43 / <10 meV/atom、<1%）数值仅用于对照讨论，禁止抄作实测。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从冻结数据读取并完成推理/评估。
3. **`results/evidence_table.csv`**：至少含列 `system_size,metric,value`（能量误差、密度 MAPE）。
4. **`results/metrics.json`**：模型参数摘要、各尺寸指标、论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（依赖/输入结构差异 vs 论文）。

## 数据铁律提醒

- 只使用本包冻结数据与论文官方权重；禁止合成/模拟数据。
- 禁止手工抄写论文数字作为「实测结果」；所有指标必须运行代码得到。
- 论文数值只能用于对照讨论。
