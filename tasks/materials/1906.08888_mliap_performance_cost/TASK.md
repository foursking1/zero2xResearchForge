# 科研任务：检验「ML 原子间势在多种元素上的能量/力精度与代价权衡」关键论断（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`1906.08888_mliap_performance_cost`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Zuo et al., "A Performance and Cost Assessment of Machine Learning Interatomic Potentials", J. Phys. Chem. A 124 (2020) 731（arXiv:1906.08888）
- 领域：materials / 机器学习原子间势（ML-IAP）/ 能量与力预测

## 问题（可证伪）

论文对六种元素（Li, Mo, Cu, Ni, Si, Ge）系统评估了四类 ML-IAP（GAP、MTP、NNP、SNAP/qSNAP）的能量与力预测精度及其与计算代价的权衡。核心论断：
1. **ML-IAP 全部达到近 DFT 精度**：所有 ML-IAP 在六元素上的能量 MAE 达 meV/atom 量级、力 MAE 达 ~0.1 eV/Å 量级，远优于传统经验势（EAM/MEAM/Tersoff）；不同 ML-IAP 之间的能量差异已在 meV/atom 量级（接近 DFT 误差极限）。
2. **相对排序**：GAP 与 MTP 的能量/力 MAE 一般最低；SNAP 与 NNP 的能量 MAE 最高；qSNAP 介于 GAP 与 NNP 之间（略优于线性 SNAP，但参数显著更多）。
3. **无过拟合**：优化后的各 ML-IAP 训练误差与测试误差相近；测试集为与训练独立采样的 10% 结构。
4. **精度-代价权衡**：模型自由度（DOF）增加可降误差但提高计算代价；存在 Pareto 前沿（论文以 Mo 系统展示）。
5. **化学趋势**：fcc 元素（Cu/Ni）能量 MAE 最低、bcc（Li/Mo）次之、金刚石结构（Si/Ge）最高；力的 MAE 对 Mo 与金刚石半导体更高。

请基于冻结数据回答：

1. **数据统计**：解析冻结的 12 个 train/test JSON（6 元素 × train/test）+ `Mo930.json`（扩展训练集 930 结构），统计各元素训练/测试配置数（train 194–263，test 23–31）与结构类型（group 标签：如 Vacancy、Interstitial、Elastic 等）。
2. **能量/力回归**：实现 ≥2 类可训练的 ML-IAP 或代理模型（建议：线性/二次 SNAP 式双谱描述符 + Ridge/线性回归，或 SOAP/GAP 风格核回归，或用 mlearn 的 SNAP/qSNAP 实现；可自写描述符），在冻结 train/test 上报告能量 MAE（meV/atom）与力 MAE（eV/Å）。
3. **对照排序**：比较不同模型（或不同描述符阶数）在各元素上的能量/力 MAE，验证「GAP/MTP 类最优、SNAP/NNP 类较差」的方向性（若实现难度大，至少给出 2 个模型的排序）。
4. **验证论文论断**：报告训练 vs 测试误差（是否接近 = 无过拟合），并结合自身结果给出四档结论。

- 结论标签：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结）→ 物理位置 `$PAPER_BENCH_DATA_DIR`（来源/许可/逐文件 SHA-256 见 `data/SOURCE.md` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 文件：`data/{Cu,Ge,Li,Mo,Ni,Si}/{training,test}.json`（12 个）+ `data/Mo/extended/Mo930.json`（1 个）。JSON 为 pymatgen Structure + 标签列表：每条含 `structure`（pymatgen dict）、`num_atoms`、`element`、`group`、`outputs`（`energy` 单位 eV、`forces` eV/Å）、`tag`（train/test）、`description`。
- 来源：论文官方仓库 `materialsvirtuallab/mlearn`（MIT License）`data/` 目录。
- 规模：~34MB；CPU 可完成（SNAP 描述符 + 线性回归分钟级；核回归视规模 0.5–2 小时）。

## 方向提示（协议建议）

1. **描述符**：SNAP 双谱系数（可用 `mlearn` 的 `snap.py`、`pymatgen` 或 `LAMMPS` 生成；简化可用 SOAP 或自写近邻对称函数）。注意六元素的原子类型单一（纯元素体系），描述符只需单元素版本。
2. **模型**：线性/岭回归（SNAP/qSNAP）、GPR（GAP 代理）、NNP（轻量 MLP，输入为近邻环境向量）；固定随机种子。
3. **指标**：能量 MAE（meV/atom）、力 MAE（eV/Å）；逐元素报告；训练 vs 测试分开。
4. **对照**：论文 Figure 3（MAE 热图）与正文（meV/atom 与 0.1 eV/Å 量级、GAP/MTP 最优）仅用于对照讨论，禁止抄作实测。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从冻结数据读取并完成训练与评估。
3. **`results/evidence_table.csv`**：至少含列 `element,model,split,metric,value`（能量/力 MAE）。
4. **`results/metrics.json`**：样本统计、各模型指标、论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（描述符/实现差异 vs 论文）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止合成/模拟数据。
- 禁止手工抄写论文数字作为「实测结果」；所有指标必须运行代码得到。
- 论文数值只能用于对照讨论；不同方法必须在同一划分、同一评估协议下比较。
