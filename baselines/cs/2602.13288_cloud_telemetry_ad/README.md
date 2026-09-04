# Heterogeneous Cloud Telemetry Anomaly Detection — Reproduction

任务卡 `2602.13288_cloud_telemetry_ad`：在冻结的 **NAB** + **Microsoft Cloud
Monitoring** 数据上，按 70/30 时间切分 + 训练期似然校准 + NAB 归一化评分，
评测 **GRU / TCN / Transformer / TSMixer** 重建式自编码器与 **Isolation
Forest**，回答论文 (arXiv:2602.13288, Table III) 的两条 claim。

## 结论速览
- **claim (a)**（Microsoft 5 个含异常子组上 GRU 唯一全正）：**partially_supported**
  — GRU 全正稳健成立；但 TCN/TSMixer 亦全正，"唯一"不成立。
- **claim (b)**（NAB 6 个含异常子组无主导架构）：**supported**
  — 最高分归属架构数 seed0=3、seed7=4，均 ≥3。

## 目录结构
```
agent_solution/
  README.md
  solution.md            # 方法 + 结果概要
  report.md              # 完整报告（协议、防泄漏、对照、局限）
  run_all.sh             # 一键流程（数据自检 + 全管线 + 分析）
  requirements.txt
  code/
    common.py            # 数据加载、70/30 切分、窗口、异常窗口
    models.py            # GRU/TCN/Transformer/TSMixer 重建 AE (Gaussian NLL)
    isolation_forest.py  # IF 基线（同协议因果逐点分数）
    train.py             # 训练 + 逐点评分 + 仅训练期似然校准
    nab_scorer.py        # NAB 归一化评分（窗口内最早 TP、FP 距离惩罚）
    run_series.py        # 多进程运行器（固定种子，可重跑）
    analyze.py           # claim 判定 + 图表
    verify_data_facts.py # 冻结数据事实（B 维度自检）
  results/               # 主结果（evidence_table.csv、metrics.json、图、对照表）
  results_seed7/         # 种子灵敏度第二组（base seed 7）
  results_strict/        # 严格阈值 θ∈{3.5,…,5.0} 灵敏度（Microsoft）
  evidence/              # 数据事实 / 可复现性 / GRU 分数导出
```

## 复现运行
```bash
cd agent_solution
python3 code/verify_data_facts.py      # （可选）冻结事实核对
bash run_all.sh 8 0                    # workers=8, seed=0

# 或分步执行：
python3 code/run_series.py --datasets nab,microsoft --jobs 8 --seed 0
python3 code/analyze.py
```

参数：
- `--datasets nab,microsoft` 选择数据集；`--only-subgroups` 只跑特定子组；
- `--th-grid 3.5,4.0,4.5,5.0` 覆盖默认 θ 网格（灵敏度用）；
- `--outdir` 输出目录（默认 `results/`）。

环境：Python 3.10+，`numpy/pandas/scikit-learn/torch`（CPU 足够；见
`requirements.txt`）。全部随机源固定种子；多进程在 CPU 上运行（~24 分钟 /
40 核·分钟规模）。

## 关键产物
| 文件 | 说明 |
|---|---|
| `results/evidence_table.csv` | 必交表：`dataset,subgroup,model,nab_score,has_anomaly_in_test,calibration`（80 行）|
| `results/metrics.json` | 运行汇总（590 任务，0 失败，种子/耗时/校准说明）|
| `results/series_raw.csv` | 逐序列原始分（debug / 复算源）|
| `results/claim_summary.json` | 两条 claim 的判定数据 |
| `results/paper_comparison_table.csv` | 本复现 vs 论文 Table III |
| `results/fig_*.png` | 子组 NAB 热力图、按子组分模型柱状图、示例检测图 |
| `evidence/data_facts.txt` | 冻结数据事实 + 180/180 哈希核对 |
| `evidence/reproducibility_check.txt` | 重跑逐字节一致验证 |