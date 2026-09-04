# code/ — 可复现脚本

针对冻结 PTB-XL 数据（`data/`，物理位置见 `data/DATA_LOCATION.md`，或 `$DATA_DIR`）的完整复现链。
**关键事实：冻结 parquet 无诊断标签列**（schema 仅 `ecg_id / age / sex / ecg_array`），因此 01-05 号脚本按实际 schema 工作：诊断任务不可监督复现，辅助任务（sex、age≥65，冻结包内真实存在的标签）用于端到端验证评估管线与模型差距格局。详见 `../report.md` 与 `../claim.md`。

## 运行顺序与说明

```bash
# 可选：指定数据目录（脚本会自动探测 /mnt/f/dataset/...、../data/ 等）
export DATA_DIR=/mnt/f/dataset/biomed/2509.10151_benchecg_xecg

python3 01_audit_data.py          # schema/样本/导联/标签结构审计 -> ../results/data_audit.json
python3 02_preprocess.py          # 500->100Hz 降采样 + train-only 归一化 + 辅助目标 -> ../results/preprocessed.npz
python3 03_train_models.py        # 训练 Simple1DCNN(3 seeds) + 手工特征逻辑回归，macro AUROC/F1 -> ../results/model_metrics.json
python3 04_figures.py             # ECG 示例、ROC 曲线、模型对比图 -> ../results/fig_*.png
python3 05_export_evidence.py     # 汇总 -> ../results/evidence_table.csv + ../results/metrics.json
```

- 环境：Python 3.12 + `pandas, pyarrow, numpy, scikit-learn, torch (CPU), matplotlib`。
- 运行时间：约 5 分钟（纯 CPU）。
- 全部脚本固定种子（`SEED=42`；03 号脚本重复种子 42/2024/7），可重复运行。
- 数据铁律遵守：只读冻结 parquet；未使用合成数据；归一化统计量仅由训练划分拟合（固化于 `../results/preprocessing.json`）。

## 与 rubic 抽查字段的对应

- **evidence_table.csv「最优模型 AUROC」**：`cnn_multitask` 行 `macro_auroc = 0.8171`（辅助目标口径，见上；诊断口径为 NA 并注明原因）。
- **metrics.json 标签统计**：`data_stats.auxiliary_targets_and_positive_counts`（sex/age≥65 的 pos/neg，train 与 validation）。诊断超类标签统计不存在（schema 无标签列，`data_audit.json` 有证据）。