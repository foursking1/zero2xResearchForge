# MedMNIST v2 L1 复现（task `2110.14795_medmnist_v2`）

本目录是论文复现任务的完整交付物。

## 结论

`supported` —— 冻结数据上 ResNet-18@28 在 5 个 MedMNIST2D 数据集上的 test AUC
（0.998/0.900/0.930/0.970/0.701）全部落在论文量级，难度排序与论文完全一致
（Blood > Pneumonia > Derma ≈ Breast > Retina）。

关键文件速览：

- `claim.md` —— 四档结论 + 关键数字
- `solution.md` —— 方法说明与结果摘要
- `report.md` —— 完整报告（方法/结果/局限/结论）
- `run_all.sh` —— 一键复现
- `code/config.py | data_stats.py | train.py` —— 可复现代码（固定 seed=0，防泄漏）
- `results/evidence_table.csv` —— 每数据集 AUC/ACC/规模
- `results/metrics.json` —— 类别计数、对照、排序、结论
- `results/checkpoints/` —— 每数据集 best-val 权重

## 复现

```bash
cd agent_solution
MEDMNIST_DATA_DIR=/path/to/frozen/npz bash run_all.sh --device cpu --epochs 45
# 或 GPU（本机 RTX 4080 约 17 分钟）：
MEDMNIST_DATA_DIR=/path/to/frozen/npz bash run_all.sh --device cuda --epochs 45
```

未设 `MEDMNIST_DATA_DIR` 时自动探测本机冻结路径
`F:\dataset\biomed\2110.14795_medmnist_v2\`（Linux 侧 `/mnt/f/...`）。