# code/ — 复现源码说明

## 依赖
Python 3.10+，需要 `torch`、`torch_geometric`（>=2.5）、`numpy`、`scikit-learn`、`matplotlib`（可选建图）。
- 本环境：Python 3.12.3 / torch 2.11.0+cu128 / torch_geometric 2.8.0.post1 / sklearn 1.6.1。
- `rdkit` 非必需（冻结数据为原子/键特征，不解析 SMILES）。

## 数据
冻结 jsonl（`train.jsonl` 32,901 行 / `valid.jsonl` 4,113 / `test.jsonl` 4,113）由 `config.py` 自动定位：
1. 环境变量 `MOLHIV_DATA_DIR`（可覆盖）
2. `/mnt/f/dataset/biomed/2005.00687_ogb_molhiv`
3. `agent_solution/data`

## 标准运行（完整复现）
```bash
cd agent_solution/code

# 1) 解析冻结 jsonl -> PyG 对象 + 数据统计（写入 results/data_statistics.json）
python3 prepare_data.py

# 2) 训练全部模型（5 层 GIN/GCN ± 虚拟节点），5 个固定种子，每模型一行结果
#    单顺序 job；GPU(推荐) 用时 ~1.5h；CPU 可改用 --device cpu --hidden 128 --epochs 30
python3 run_experiments.py --device cuda --seeds 42,7,1 --models gin,gin-vn,gcn,gcn-vn
# 追加种子（幂等续跑，自动合并已完成的 run）：
python3 run_experiments.py --device cuda --seeds 3,99  --models gin,gin-vn,gcn,gcn-vn

# 3) 汇总指标 + 锚对照 + 四档结论（results/metrics.json）
python3 build_metrics.py

# 4) 图：原子数分布 / test ROC / 柱状对比（含论文红线） -> results/figs/
python3 make_figures.py

# 5) 证据独立重算：jsonl 行数 + 由保存预测重算 AUC（results/runs/ 与 predictions/*.npz）
python3 verify_results.py
```

## 快速运行（冒烟 / 低资源）
```bash
python3 run_experiments.py --device cpu --seeds 42 --models gin --hidden 64 \
    --epochs 20 --patience 5 --batch 128
```
或对全量配置降低 epochs：`--epochs 40 --patience 10`。

## 输出
| 文件 | 说明 |
|---|---|
| `results/evidence_table.csv` | `model,virtual_node,valid_roc_auc,test_roc_auc`（每模型一行；GNN 为种子均值） |
| `results/model_results.json` | 每个 (模型,种子) 的完整记录 |
| `results/metrics.json` | 图统计、各模型 AUC、vs 论文锚对照、结论标签 |
| `results/data_statistics.json` | 图级统计（train/valid/test + 全局） |
| `results/runs/*.json` | 单次运行明细（无预测数组） |
| `results/predictions/*.npz` | test 预测概率 `pred_test` + 真值 `y_test`（供无重训核验） |
| `results/figs/*.png` | 分析图表 |
| `results/checkpoints/*.pt` | 最优权重（由早期脚本生成，供追溯） |

## 防泄漏说明
- 划分完全由冻结文件决定；candidate 无在线下载（无 `ogb` 数据拉取）。
- 提前停止 / LR 调度 / 最优权重选择 **只看 valid**；test 仅在最终评估读取一次。
- 种子固定（模型初始化、DataLoader shuffle、sklearn）。