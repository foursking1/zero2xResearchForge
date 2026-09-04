# solution.md — 复现方案与结果速览

问题：Baloch et al.（PRM 5, 043804, 2021）用 GPR 把 Shannon 离子半径表从约 475 个离子
扩到 987 个，宣称 7 折 CV 下 RMSE=0.0332 Å、R²=99.3%。需用冻结数据核验。

## 结论：supported

GPR 在冻结数据（476 个 Shannon 标签）上 7 折 CV 得到 **RMSE≈0.045 Å、R²≈98.6%**
（镜像论文特征）/ **RMSE≈0.039 Å、R²≈99.0%**（增强特征：加入 Z−OS 电子数），
与论文 0.0332 Å / 99.3% 同量级、同方向。扩展表 1005 行 / 476 Shannon / 988 ML /
512 新预测与论文锚核验一致；预测半径随 OS↑ 减小、CN↑ 增大的物理趋势 100% 成立；
独立 GPR 可高保真复现 512 个 ML-only 半径（Pearson r=0.989）。

## 关键数字

| 项 | 值 | 出处 |
|---|---|---|
| 数据行数 / 元素 | 1005 / 93 | `01_parse_data.py` |
| Shannon 有值 | 476（456 数值 + 20 自旋均值） | 同左 |
| ML 有值 / ML-only 新预测 | 988 / 512 | 同左 |
| Updated Anions | 33 | 同左 |
| GPR RMSE (Å)，F2_paper_full，7 折 | 0.0447 | `02_train_evaluate.py` |
| GPR R²，F2_paper_full | 98.6% | 同左 |
| GPR RMSE (Å)，F4_enhanced_eion | 0.0392 | 同左 |
| GPR GroupKFold RMSE（按元素） | 0.0676（F2） | 同左 |
| Ridge / MLP RMSE | 0.152 / 0.073 Å | 同左 |
| ML-only 重建 Pearson | 0.9885 | `03_extension_validation.py` |
| ML-only 重建中位 |Δ| | 1.34 pm（≈0.013 Å） | 同左 |
| CN 趋势 / OS 趋势符合率 | 273/273、142/142（100%） | 同左 |

## 方法一句话

监督标签=Shannon 半径（pm/100）；特征=周期/族/价电子数/块/OS/CN/电离势（镜像论文，
+Z−OS 增强）；模型=GPR(Matérn 3/2)、Ridge、MLP，同一 7 折 slice（seed=42）公平对比
+ 按元素 GroupKFold 防泄漏；所有指标代码重算、固定种子。

## 产物清单（agent_solution/）

- `claim.md` —— 四档判定与关键数字
- `report.md` —— 完整报告（方法/结果/局限）
- `code/` —— 4 个脚本 + periodic_table.py（完整可复现，见 `code/README.md`）
- `results/` —— dataset_clean.csv、dataset_summary.json、evidence_table.csv、
  metrics.json、extension_analysis.csv、extension_summary.json、figures/
- `evidence/` —— 关键证据导出（见下）

## 运行

```bash
cd agent_solution
python3 code/01_parse_data.py
python3 code/02_train_evaluate.py
python3 code/03_extension_validation.py
python3 code/04_report_figures.py
```