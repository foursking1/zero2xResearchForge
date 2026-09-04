# agent_solution — 2211.15895_bertos_oxidation_state

冻结官方模型对官方测试集的 BERTOS 氧化态预测声明独立复现。**未重新训练、未改动任何权重/标签**。

## 快速导航

| 文件 | 内容 |
|---|---|
| `solution.md` | 结论摘要、协议、一键运行说明（短）
| `report.md` | 完整报告：口径、结果、逐格对照、差异归因、局限性（长）
| `scripts/evaluate.py` | 主评估脚本（4 模型 × 4 测试集 PS/PC/金属-非金属，CPU 推理）
| `scripts/per_element.py` | 每元素精度表
| `scripts/compute_extra.py` | PCASA / 每类精度 / 位置剖面
| `scripts/make_tables.py` | 由 `results/evaluation_results.json` 渲染 evidence 各表
| `scripts/pymatgen_baseline.py` | pymatgen 启发式确定性猜测诊断（可选）
| `results/evaluation_results.json` | 全部实测数值（唯一真源，报告数字取自此处）
| `evidence/*` | Table 1 对照、PC 矩阵、金属/非金属、锚值对照、数据集规模、checkCN 演示

## 直接复现

```bash
cd scripts
python3 evaluate.py --data ../../data --max_length 200 --site_cap 199 --jobs 4 --outdir ../results
python3 per_element.py --data ../../data
python3 compute_extra.py
python3 make_tables.py
```

依赖：python3、torch、transformers（requirements：`data/code/requirements.txt`）。

## 关键数值（与论文/样例验证一致）

- PS(ICSD×ICSD)=96.78%（论文 96.82）；PS(ICSD_oxide×ICSD_oxide)=97.50%（论文 97.61）；PS(ICSD_CN×ICSD_CN)=96.34%（论文 96.27）
- PC(ICSD_CN self)=86.63%（论文 87.76）；金属/非金属=97.17/96.13%（论文 97.12/96.05）；PCASA=97.17%（论文 97.16）
- Table 1 全部 16 格 |Δ|≤0.14 pp
- 数据集规模：ICSD_CN train=31,827/test=3,724；ICSD test=5,215

> 注：`EVAL_REPORT.md` 为本工作目录中早前一次评测的记录文件（同一任务历史评估），非本 agent 产物，供对照参考。