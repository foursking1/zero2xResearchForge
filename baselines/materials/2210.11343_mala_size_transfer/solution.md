# solution.md：MALA 跨尺度外推复现（arXiv:2210.11343，task 2210.11343_mala_size_transfer）

本目录为科研任务「检验 MALA 局域电子结构模型跨尺度外推保持化学精度」的完整复现
方案。所有数字均由本目录 `code/` 中的脚本在本机实际运行产生（固定种子 42、CPU），
未手工抄录论文数值。

## 1. 任务与方法概要

- 论文：Pineda Flores et al., "Predicting electronic structures at any length
  scale with machine learning", arXiv:2210.11343（npj Comput. Mater. 9, 115
  (2023)）。
- 论断：用 **256 个 Be 原子**（平衡密度 1.896 g/cm³）训练的 MALA 模型，直接外推到
  **512 / 1,024 / 2,048 原子** 体系，总能误差保持化学精度（<43 meV/atom，通常
  <10 meV/atom）、电子密度 MAPE <1%，误差不随体系尺寸发散。
- 冻结数据（rodare 1851 `size_transfer_cleaned`）：`trained_models/beryllium/`
  （`beryllium.params.json` / `.network.pth` / `.iscaler.pkl` / `.oscaler.pkl`）、
  `model_training/training.py`、`model_inference/run_inference.py`、
  `data_analysis/calculate_rdf.py`。
- 本复现流程：
  1. **模型核对（A1）**：`code/model_check.py` 核对 params.json 关键字段、网络
     state_dict 维度、标定器元数据，全部通过（`evidence/model_check.json`）。
  2. **跨尺度推理（A2，核心）**：`code/run_size_transfer.py` 加载冻结模型，对
     256/512/1,024/2,048 原子 Be hcp 超胞（1.896 g/cm³ + 高斯位移 RMS 0.1 Å，
     种子 42）计算 SNAP 描述符 → 神经网络 LDOS 前向 → 费米能求解 → 带能量/
     熵/电子数积分，输出逐尺寸结果与相对 256 基准的漂移。
  3. **RDF 结构一致性（A3/锚 7）**：`code/rdf_check.py` 对比 256 与 2,048 原子
     体系的径向分布函数。
  4. **网格密度敏感性诊断**：`code/grid_density_diag.py` 量化「跨尺寸带能量漂移」
     中网格取整伪影 vs 真实尺寸效应的占比。

## 2. 关键结果（实测，见 results/evidence_table.csv 与 metrics.json）

| 尺寸 | 带能量/原子 (eV) | 漂移 vs 256 (meV/atom) | 费米能 (eV) | 电子数/原子 |
|---|---|---|---|---|
| 256 | -3.94418442 | 0 | -1.09881020 | 2.0000 |
| 512 | -3.96859626 | -24.4118 | -1.12202472 | 1.9970 |
| 1024 | -3.99459088 | -50.4065 | -1.14221788 | 1.9985 |
| 2048 | -3.98309961 | **-38.9152** | -1.13364860 | 1.9974 |

（最终数值以 `results/*.json` 为准。）

## 3. 结论标签：partially_supported

详见 `claim.md`。核心要点：
- **方向性支持**：漂移代理（512/1024/2048 vs 256）非单调、未随尺寸发散；网格密度
  校正后真实尺寸效应 ≈0。
- **绝对精度不可复算**：冻结数据不含任何 DFT 参考输出（无 QE `.out`、无赝势、
  无参考密度/总能），因此「相对 DFT 的绝对总能误差 <43/<10 meV/atom」与
  「密度 MAPE <1%」在本数据包上**不可复算**，只能以 256 基准的相对漂移作为内部
  可验证代理（任务方向提示 #3 认可此口径）。

## 4. 复现

依赖（已在本机验证）：`python>=3.7`、`mala`（1.4.0，含网络/标定器 IO）、`torch`、
`ase`、`numpy`、`scipy`、`numba`、`matplotlib`。

```bash
export MALA_MODEL_DIR=/path/to/frozen/trained_models/beryllium/   # 默认 F:/dataset/...
cd code
python model_check.py        # A1 模型核对 -> evidence/model_check.json
python run_size_transfer.py  # A2 推理 -> size_transfer_results.json（滚动 checkpoint）
python make_results.py       # -> results/evidence_table.csv, results/metrics.json
python rdf_check.py          # 锚7 -> results/rdf_results.json
python grid_density_diag.py  # 漂移分解 -> results/grid_density_diagnostic.json
python make_figure.py        # -> results/size_transfer_figure.png
```

固定种子 42，全部 CPU-only（`params.use_gpu=False`）。运行时间受本机并发负载影响
（详见 report.md §7）。