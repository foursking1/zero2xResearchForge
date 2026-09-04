# Solution — 执行方法与结果摘要

## 任务
验证 TabularBench（arXiv:2408.07579）URL 用例两个关键论断（L1）：
- C1：标准训练下 ID 精度接近但鲁棒精度悬殊。
- C2：对抗训练大幅提升鲁棒且干净精度基本保持。

## 方法（与 TASK.md 协议对齐）
1. **数据**：冻结 `data/url.csv`（11,430 × 63 特征 + 标签，正类 50.0%），SHA-256 核验。
2. **划分**：官方 DefaultSplitter（stratify, random_state=42, test=0.2 两次）→ train 7,315 / val 1,829 / test 2,286。
3. **缩放**：train-only 逐特征 min-max → [0,1] + clip（test 不参与统计）。
4. **模型**：4 个 MLP——[64]、[128,64]、[256,128,64]、[128,64]+dropout(0.3)；ReLU，单 logit。
5. **训练**：Adam(lr=1e-3, wd=1e-4)，batch 256，12 epochs，BCEWithLogits，seed=0。
   - 标准训练；AT = FGSM 单步（ε=0.1, α=0.1，L2 步 + L2 球投影 + [0,1] clip）。
6. **攻击评估**：无目标 PGD-L2，40 步，ε=0.25，α=ε/4，每步 L2 球投影 + [0,1] clip；报测试集 clean / robust 精度。

## 结果（实测，`results/evidence_table.csv` + `results/metrics.json`）
| 指标 | std | AT |
|---|---|---|
| clean 范围 / 跨度 | 91.91–94.09% / **2.19pp** | 89.90–93.44% / 3.54pp |
| robust 范围 / 跨度 | 17.45–50.83% / **33.38pp** | 76.51–78.13% / 1.62pp |
| mean robust | 27.85% | 77.53% |
| mean clean | 93.14% | 91.78% |

- 平均鲁棒提升：**+49.67pp**；平均干净变化：**−1.37pp**。
- 逐模型鲁棒提升：+26.9（mlp64，基准已最鲁棒）~ +60.7pp（mlp128_64）；干净代价均 ≤ 2.1pp。

## 结论标签
- **C1 = `supported`**：clean spread 2.19pp ≤ 5pp 且 robust spread 33.38pp ≥ 15pp。
- **C2 = `supported`**：平均鲁棒提升 +49.67pp ≥ 20pp 且干净下降 1.37pp ≤ 5pp。

> 口径说明：评估用 PGD-L2 ε=0.25（协议口径，破坏力量级 ≈ 论文 CAA ε=0.5）；论文数值仅用于对照，本报告所有数字均由代码实测。

## 交付物
- `code/run_experiment.py`：完整可复现（seed=0，CPU）。
- `code/analysis_plots.py`：证据图表。
- `results/evidence_table.csv`、`results/metrics.json`、`results/figures/`。
- `claim.md`：四档判定与失败条件；`report.md`：完整报告；`evidence/`：运行与对比证据。

## 复现
```bash
python3 code/run_experiment.py --data ../data/url.csv --out results
```
环境：Python 3.12，numpy 2.4.6，pandas 2.3.3，scikit-learn 1.6.1，torch 2.11.0（CPU），matplotlib 3.9.4。同一机器连续两轮运行逐字节一致。