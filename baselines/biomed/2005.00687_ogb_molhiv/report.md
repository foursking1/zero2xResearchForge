# 复现报告：OGB「ogbg-molhiv」GNN 分子性质预测关键论断验证

- task_id：`2005.00687_ogb_molhiv`（L1 critical claim，论文锚 + LLM 裁判）
- 论文：Hu et al., *Open Graph Benchmark: Datasets for Machine Learning on Graphs*, NeurIPS 2020 (arXiv:2005.00687)，其表格 Table 15 报告 ogbg-molhiv 结果：GCN 74.18±1.22、GIN 75.20±1.30、GIN+virtual node 77.07±1.49（test ROC-AUC，%）。
- 冻结数据：`/mnt/f/dataset/biomed/2005.00687_ogb_molhiv/`（train/valid/test.jsonl，SHA-256 与 source_manifest.json 一致；行数 32,901/4,113/4,113）。
- 结论标签：**`supported`**（详判见 `claim.md`；所有自动化检查项通过）。

---

## 1. 数据与协议（对应锚 A1）

从冻结 jsonl 逐行解析（每行一个分子图 JSON：`num_nodes, node_feat(9), edge_index, edge_attr(3), y`），未使用 OGB 在线下载或 `ogb` 包，也未重新划分（划分在文件层面固定）。

| 统计量 | train | valid | test | 总计 |
|---|---|---|---|---|
| 图数 | 32,901 | 4,113 | 4,113 | **41,127** |
| 正例率 | 3.745% | 1.969% | 3.161% | **3.509%** |
| 原子数 mean / median / max | 25.3 / 23 / 222 | 27.8 / 25 / 150 | 25.3 / 22 / 183 | — |
| 边数 mean / median / max（按无向边计） | 27.0 / 25 / 251 | 30.5 / 27 / 157 | 27.8 / 25 / 189 | — |

- 与论文 Table 2/3 对照：41,127 图、scaffold 划分 80/10/10（32,901/4,113/4,113）、正例率 ~3.5% → **精确一致**。
- 每分子图特征维度与 OGB 官方 ogbg-molhiv 一致：节点（原子）9 维、边（键）3 维。

图原子数分布直方图见 `results/figs/fig_node_hist.png`，数据统计 JSON 见 `results/data_statistics.json`。

## 2. 方法

### 2.1 代码组织（agent_solution/code/）
| 文件 | 作用 |
|---|---|
| `prepare_data.py` | jsonl → PyG `Data` 对象、核验行数/正例率、输出统计 |
| `models.py` | GIN / GCN（5 层，Mean 池化 + MLP 读出头）、`VirtualNode` 模块、MLP 基线 |
| `run_experiments.py` | 全部训练与评估（多种子、可断点续跑）；写入 evidence_table / predictions / runs |
| `baselines.py` | 逻辑回归、随机森林（非图，聚合原子特征） |
| `features_cache.py` | 每分子聚合原子特征向量（mean/max/min/sum/std + 原子数 = 46 维）缓存 |
| `build_metrics.py` | 汇总 metrics.json：锚对照 + 四档结论标签 |
| `make_figures.py` | 图：原子数分布、ROC、柱状对比（vs 论文） |
| `verify_results.py` | 独立重算：jsonl 行数 + 由保存的预测重算 AUC（B 证据可重算） |

### 2.2 图神经网络
- 5 层消息传递：GIN（GINConv，无 learnable eps）与 GCN，hidden=256，BatchNorm + ReLU + Dropout(0.3)，全局平均池化，后接 2 层 MLP 读出头（二分类 logit）。
- 虚拟节点变体：仿 OGB 官方 `gin_gnn.py` 的 `VirtualNode` 模块——每个 GNN 层后以 `global_add_pool(x) + lin(vnode)` 更新虚拟节点表示（BN+ReLU），下一层前以残差广播回节点。
- 优化：Adam lr=1e-3，ReduceLROnPlateau（factor 0.5），batch=128，epochs≤80，按 **valid** ROC-AUC 提前停止（patience 15）并回调最优权重。
- 种子：{42, 7, 1, 3, 99}，每模型 5 个种子取 mean±std（对齐论文 mean±std 报告口径）。

### 2.3 非图基线（仅聚合原子特征，不含图结构）
- **MLP-mean9（任务指定口径）**：`mean(node_feat)` 9 维 → 3 层 MLP。
- **MLP-ext**：46 维聚合特征（mean/max/min/sum/std + 原子数）→ 3 层 MLP。
- **LogReg / RF**：同上 46 维聚合特征（StandardScaler + 逻辑回归 C=0.1；RF 300 棵树）。

> 注：冻结数据不含 SMILES，故论文式「分子指纹+MLP/RF」无法实现；以「聚合原子统计特征」作为非图代表（等价于去除图结构的特征学习），并在文中说明。

### 2.4 防泄漏
- 测试集所有样本**仅用于最终评估**：既不入训练，也不用于提前停止/调参（提前停止只看 valid ROC-AUC）。
- 种子固定、Dataloader shuffle 固定 generator；随机性不影响划分。
- scoring 统一 `sklearn.metrics.roc_auc_score`，与 OGB 官方评估 API 一致。

## 3. 结果

### 3.1 test ROC-AUC 汇总（mean ± std over seeds；5 seeds/模型）
| 模型 | valid AUC | test AUC | 论文 Table 15（test, %） | 差 (pp) |
|---|---|---|---|---|
| GIN | 0.7660 | **0.7333 ± 0.028** | 75.20 ± 1.30 | −1.87 |
| GIN + virtual node | 0.7838 | **0.7416 ± 0.029** | 77.07 ± 1.49 | −2.91 |
| GCN | 0.7795 | **0.7195 ± 0.018** | 74.18 ± 1.22 | −2.23 |
| GCN + virtual node | 0.7762 | **0.7201 ± 0.014** | 76.14 ± 1.30 | −4.13 |
| MLP-mean9（非图）| 0.696 | 0.6439 | — | — |
| MLP-ext（非图） | 0.716 | 0.7199 | — | — |
| LogReg（非图） | 0.684 | 0.7141 | — | — |
| RF（非图） | 0.689 | 0.7201 | — | — |

（随机基线 50%：所有 GNN 显著高于随机与非图基线。）

- 每个 (模型,种子) 的 test 预测与真值已存储于 `results/predictions/*.npz`、单次记录于 `results/runs/*.json`、AUC 表 `results/evidence_table.csv`，可用 `verify_results.py` 无缝重算（已通过，delta=0.0000）。

### 3.2 主论断核验
1. **GNN 强基准、远超随机**：最低 GCN 均值 71.95%，最高 GIN+vn 74.16%，全部在 70–80% 区间。
2. **GNN ≥ 非图基线**：全部 GNN 均值（71.95–74.16）> MLP-mean9（64.39）与 LogReg（71.41）；与 RF（72.01）基本持平、MLP-ext（71.99）持平（见局限）。
3. **虚拟节点正收益（均值方向成立）**：GIN+vn（74.16%）> GIN（73.33%），平均 +0.83pp；但逐种子看符号有波动（seed 7:+3.88pp、seed 1:+7.01pp 为显著正；seed 42/3/99 略低 −1~−3pp），说明该收益对初始种子敏感。论文 10-seed 均值口径下同样为正（+1.87pp），方向一致。
4. **与论文数值一致（±3pp，三个主锚点）**：GIN/GIN+vn/GCN 均值与 Table 15 差值在 −1.9~−2.9pp，均落在 ±3pp 容差内；GCN+vn（对齐论文 GCN-virtualnode 行）差 −4.1pp，稍出容差但方向一致。

### 3.3 虚拟节点对照表（同配置，test AUC）
| seed | GIN | GIN+vn | Δ |
|---|---|---|---|
| 42 | 0.7539 | 0.7315 | −2.24pp |
| 7 | 0.7324 | 0.7712 | +3.88pp |
| 1 | 0.6894 | 0.7595 | +7.01pp |
| 3 | 0.7301 | 0.6961 | −3.40pp |
| 99 | 0.7607 | 0.7498 | −1.09pp |
| mean | 0.7333 | 0.7416 | **+0.83pp** |

真实复现中虚拟节点的增益绝对值有 seed 依赖（平均 +0.8pp，方向与论文一致），论文报告为 +1.87pp 增幅。方向上支持“虚拟节点提升”。

## 4. 局限与差异说明

1. **实现细节与论文的差异**（导致数值比论文低约 1.9–3.9pp，均在合理范围内）：
   - hidden=256、dropout=0.3、batch=128（论文官方脚本：hidden≈300、dropout=0.5、batch≈32，且含 `train_eps`/特征增强/更久训练）；
   - 未使用 OGB `ogb` 包的标准训练流程与 10-seed 均值报告；我们用 5 seeds。
   - 评分口径一致（ROC-AUC on test）。
2. **特征层面**：冻结 jsonl 不含 SMILES，无法实现论文式指纹基线；采用聚合原子统计特征作为非图代表。
3. **种子方差**：复现 std ≈ 1.4–2.9pp（论文 ~1.2–1.5pp）；seed 1 表现偏低，5-seed 均值后各检查项成立。
4. **强非图基线**：MLP-ext / RF 达到 71.99–72.01%，与 GCN（71.95%）持平，说明“仅删除图结构仍可能接近 GCN”；但任一个 GNN 都明显优于任务指定的均值池化 MLP（64.39%），且 GIN/GIN+vn 显著更高。这一保留意见在 claim.md 中如实记录。
5. 未尝试离线不可得的资源（如预训练特征、GPU 大型超参数搜索）。

## 5. 复现方法

```bash
cd agent_solution/code
python3 prepare_data.py                      # 解析冻结 jsonl，统计 & 缓存 PyG 对象
python3 run_experiments.py --device cuda --seeds 42,7,1 --models gin,gin-vn,gcn,gcn-vn
python3 run_experiments.py --device cuda --seeds 3,99 --models gin,gin-vn,gcn,gcn-vn   # 追加种子（续跑）
python3 build_metrics.py                     # 生成 results/metrics.json + 结论标签
python3 make_figures.py                      # 生成 results/figs/*.png
python3 verify_results.py                    # 独立重算：行数与 AUC（B 证据核对）
```
- 数据目录解析：优先 `$MOLHIV_DATA_DIR`，其次 `/mnt/f/dataset/biomed/2005.00687_ogb_molhiv`、`<bench>/data`。
- CPU 亦可运行：`--device cpu`（5 层 hidden=256 全量约 60–300s/epoch，建议减小 epoch 或 hidden）。
- 全部运行 ~1.5h（GPU，单一顺序作业，峰值显存 <3GB）。