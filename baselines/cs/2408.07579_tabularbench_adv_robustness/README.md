# Agent Solution — TabularBench URL C1/C2 论断验证

任务：`2408.07579_tabularbench_adv_robustness` · CS/表格深度学习/对抗鲁棒性 · L1 critical claim

## 目标
在冻结的 URL 网络钓鱼检测数据集上，用一组自行训练的深度模型验证论文（arXiv:2408.07579 Table 3）的两个关键论断：
- **C1**：标准训练下 ID 干净精度接近，但约束攻击下鲁棒精度悬殊（"ID 接近 ≠ 鲁棒接近"）。
- **C2**：对抗训练（AT）显著提升鲁棒精度，而干净精度基本保持。

## 交付物
| 文件 | 说明 |
|---|---|
| `claim.md` | C1/C2 四档判定 + 失败条件 + 关键数字 |
| `code/run_experiment.py` | 可复现主脚本（划分/缩放/训练/AT/PGD 评估，固定 seed） |
| `code/analysis_plots.py` | 结果图表生成脚本 |
| `results/evidence_table.csv` | 每模型×每训练的 clean/robust 精度 |
| `results/metrics.json` | 汇总指标（均值/跨度/提升/相关/结论标签） |
| `results/figures/` | 证据图表 |
| `report.md` | 完整方法/结果/结论/局限报告 |
| `README.md` | 本文档（运行说明） |

## 执行摘要（实测）
- 划分：train 7,315 / val 1,829 / test 2,286（官方 DefaultSplitter, stratify, random_state=42 双层 80/20）；正类率 50.0%；63 数值特征。
- 标准化：train-only 拟合的逐特征 min-max → [0,1]，clip 到 [0,1]。
- 模型（4 个 MLP，单 logit 输出）：`mlp64` / `mlp128_64` / `mlp256_128_64` / `mlp128_64_drop(0.3)`。
- 训练：Adam(lr=1e-3, weight_decay=1e-4)、batch 256、12 epochs、BCEWithLogits；标准训练 + FGSM-AT（ε=0.1, α=0.1, 1 步）。
- 评估攻击：无目标 PGD-L2，40 步，ε=0.25，步长 ε/4，每步 L2 球投影 + [0,1] clip。

| 指标 | 标准训练 (std) | 对抗训练 (AT) |
|---|---|---|
| clean 范围 | 91.91–94.09% | 89.90–93.44% |
| clean 跨度 | **2.19pp** | 3.54pp |
| robust 范围（PGD-L2 ε=0.25） | 17.45–50.83% | 76.51–78.13% |
| robust 跨度 | **33.38pp** | 1.62pp |
| robust 均值 | 27.85% | 77.53% |

AT 相对 std：平均鲁棒提升 **+49.67pp**；平均干净精度变化 **−1.37pp**。

## 结论标签
- **C1：`supported`** —— clean 跨度 2.19pp ≤ 5pp **且** robust 跨度 33.38pp ≥ 15pp。
- **C2：`supported`** —— 平均鲁棒提升 +49.67pp ≥ 20pp **且** 平均干净下降 1.37pp ≤ 5pp。

## 复现
```bash
# 需 numpy/pandas/scikit-learn/torch/matplotlib（见 code/requirements.txt）
cd agent_solution
python3 code/run_experiment.py --data ../data/url.csv --out results
python3 code/analysis_plots.py          # 从 results/metrics.json 生成图表
```
说明：
- `run_experiment.py` 固定 seed=0、全部 CPU（`--device cpu`），每次运行从 `data/url.csv` 重新计算所有指标并覆写 `results/`。不传 `--data/--out` 时默认定位到 `agent_solution/code/` 上两级目录中的 `data/url.csv` 与 `results/`。
- 运行时长约 15–35 分钟（取决于 CPU 负载；本机 20 核但评测期多任务并行）。
- 我们在同一环境连续两次运行得到完全一致的 `metrics.json` 与 `evidence_table.csv`（证据见 `evidence/rerun_compare.txt`）。