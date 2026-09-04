# 论文锚：2005.00687_ogb_molhiv

> 用途：LLM judge 判分基准（私有）。数值来自 arXiv:2005.00687v2（NeurIPS 2020 Datasets & Benchmarks），禁止臆造。

## 锚清单

| # | 指标 | 论文数值 | 出处 | 定义口径 | 容差 |
|---|---|---|---|---|---|
| 1 | ogbg-molhiv 规模 | 41,127 个分子图；scaffold 划分 80/10/10（train 32,901 / valid 4,113 / test 4,113） | Table 2/3 | 图级二分类 | 精确（冻结文件核验） |
| 2 | GCN test ROC-AUC | 74.18±1.22% | Table 15 | 官方 scaffold 划分 | ±3pp 判接近 |
| 3 | GIN test ROC-AUC | 75.20±1.30% | Table 15 | 同上 | ±3pp |
| 4 | GIN+virtual node | 77.07±1.49% | Table 15 | 加虚拟节点 | 方向锚（+1pp 以上） |
| 5 | 主论断 | GNN（GIN/GCN）是强基准；scaffold 划分比随机划分难得多（随机划分 GIN 82.73±2.02 vs scaffold 77.07）；虚拟节点/额外特征有提升 | §6.1 / Table 15 | 方向性 | 方向 |

## 备注
- 主论断：GNN 在 scaffold 划分下 AUC≈75-77%（远高于 50% 随机），比非图基线强。
- 判分提示：以「GNN test AUC ≥ 非图基线 + 落在 70-80% 区间」方向为主判据；绝对数值受实现/种子影响。
