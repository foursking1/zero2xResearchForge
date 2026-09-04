# agent_solution — 1906.08888_mliap_performance_cost

科研复现工作区。入口见 `solution.md`（方法+结果摘要）与 `report.md`（完整报告）；
最终判定见 `claim.md`（**partially_supported**）。

## 目录
- `claim.md` —— 四档结论与关键数字
- `solution.md` —— 方法说明与结果摘要
- `report.md` —— 完整报告（方法/结果/组别/权衡/局限/复现）
- `code/` —— 全部可复现源码（固定种子，CPU 可跑，离线）
- `results/` —— `evidence_table.csv`、`metrics.json`、`anchor_comparison.json`、
  `mo_pareto_scan.json`、`mo930_convergence.json`、`verify_*`、`figures/`、`models/`（已拟合模型快照）
- `evidence/` —— 关键证据导出的副本

## 快速复现
```bash
cd code
python3 verify_dataset.py     # 数据统计 + 抽查（~1 min）
python3 run_pipeline.py       # 六元素 4 类模型训练/评估（首次建特征 ~15-20 min）
python3 run_mo930.py          # Mo930 数据量收敛
python3 pareto_scan.py        # Mo 精度-代价扫描
python3 make_analysis.py      # 汇总 + 判定 + 图
python3 fig_extra.py          # Pareto/收敛图
```

## 数据来源
冻结数据：`data/{Cu,Ge,Li,Mo,Ni,Si}/{training,test}.json` +
`data/Mo/extended/Mo930.json`（官方仓库 materialsvirtuallab/mlearn，MIT）。
所有指标均由上述代码在冻结数据上计算，未抄写论文数值。