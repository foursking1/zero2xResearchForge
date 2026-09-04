# agent_solution — MALA 跨尺度外推复现（2210.11343_mala_size_transfer）

科研任务「检验 MALA 局域电子结构模型跨尺度外推保持化学精度」的完整复现产物。

## 目录结构

```
agent_solution/
├── claim.md        # 四档结论判定与关键数字
├── solution.md     # 简洁方案说明 + 结果
├── report.md       # 完整报告（方法/结果/局限/结论）
├── code/           # 全部可复现脚本（固定种子 42，CPU-only）
│   ├── model_check.py         # A1 模型/数据核对
│   ├── run_size_transfer.py   # A2 核心推理 256/512/1024/2048
│   ├── make_results.py        # 生成 evidence_table.csv + metrics.json
│   ├── make_figure.py         # 误差-尺寸图
│   ├── rdf_check.py           # 锚7 RDF 一致性
│   ├── grid_density_diag.py   # 网格密度敏感性诊断（漂移分解）
│   ├── batched_bispectrum.py  # SNAP 描述符引擎（与 MALA 核对至机器精度）
│   ├── numba_bispectrum.py    # numba-JIT 双谱内核
│   └── size_transfer_results.json   # 推理中间产物（checkpoint）
├── results/
│   ├── evidence_table.csv     # system_size, metric, value
│   ├── metrics.json           # 模型摘要 + 逐尺寸指标 + 锚对照 + 结论
│   ├── size_transfer_results.json
│   ├── size_transfer_figure.png
│   ├── rdf_results.json
│   └── grid_density_diagnostic.json
└── evidence/
    └── model_check.json       # A1 核对证据
```

## 关键结论

- 标签：**partially_supported**
- 实测漂移代理（vs 256 基准，meV/atom）：512 = -24.4，1024 = -50.4，
  2048 = **-38.9**（<43 meV/atom，化学精度窗口内；非单调、未发散）
- 网格密度校正后真实尺寸效应 ≈0（±3 meV/atom）→ 误差明确不随尺寸发散
- 电子数/原子自洽 2.000/1.997/1.998/1.997（<0.15%）
- RDF 256 vs 2048 相关 1.0
- 不可复算（冻结数据无 DFT 参考）：绝对总能误差（<43/<10 meV/atom）、
  密度 MAPE（<1%）、131,072 原子演示、DFT 速度比

## 复现

```bash
export MALA_MODEL_DIR=/path/to/frozen/trained_models/beryllium/  # 默认 F:/dataset/...
cd code
python model_check.py
python run_size_transfer.py     # 带滚动 checkpoint，可续跑
python make_results.py
python rdf_check.py
python grid_density_diag.py
python make_figure.py
```

依赖：`mala`（1.4.0）、`torch`、`ase`、`numpy`、`scipy`、`numba`、`matplotlib`。
详见 `report.md` §9。