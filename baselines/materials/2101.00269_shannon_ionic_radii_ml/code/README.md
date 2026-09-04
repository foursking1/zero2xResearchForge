# 代码与复现说明（code/README.md）

复用 `../results/` 作为输出目录（与报告引用路径一致）。

## 依赖

- Python ≥ 3.10
- numpy, pandas, scipy
- scikit-learn ≥ 1.0
- matplotlib（仅为 04 出图；03 也画图）

全部在 CPU 上运行（GPR 476 样本、7 折，分钟级）。

## 脚本

| 脚本 | 功能 | 输入（冻结 data/） | 输出（../results/） |
|---|---|---|---|
| `01_parse_data.py` | 解析官方 HTML 存档 → 清洁表；与两份 CSV 逐列 assert 核对 | `data/cmd-ml.github.io_index.html`, `data/ionic_radii_extended.csv`, `data/_html_parsed_full.csv` | `dataset_clean.csv`, `dataset_summary.json` |
| `02_train_evaluate.py` | GPR(Matérn)/Ridge/MLP 训练评估（7 折 shuffle + 按元素 GroupKFold） | `dataset_clean.csv` | `evidence_table.csv`, `metrics.json` |
| `03_extension_validation.py` | ML-only 复现、物理趋势、覆盖率 | `dataset_clean.csv` | `extension_analysis.csv`, `extension_summary.json`, `figures/` |
| `04_report_figures.py` | 报告用图 | `dataset_clean.csv`, `evidence_table.csv` | `figures/*.png` |
| `periodic_table.py` | 元素静态参考（原子序数/周期/族/块/价电子/第一电离势）——特征构建用 | — | — |
| `dev_explore_gpr*.py` | 开发期特征/核探索草稿（非正式产物，可忽略） | — | — |

## 运行顺序与种子

```bash
python3 01_parse_data.py
python3 02_train_evaluate.py     # 所有随机流程固定 random_state=42
python3 03_extension_validation.py
python3 04_report_figures.py
```

## 复现断言（脚本内置）

1. 解析后行数 == 1005，Element 数 == 93；
2. Shannon 标签行 == 476，与其各列与两份 CSV 逐单元格一致；
3. `evidence_table.csv` 含 `feature_set,model,split,metric,value` 列；
4. `metrics.json` 的 GPR paper-full RMSE(Å) ∈ [0.02, 0.06]（B 抽查项）。