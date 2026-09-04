# Agent Solution（typical 水平执行）

## 任务
验证 TabularBench（arXiv:2408.07579）URL 数据集两个关键论断：
- C1：标准训练下 ID 精度相近但鲁棒精度悬殊。
- C2：对抗训练大幅提升鲁棒精度且干净精度基本保持。

## 完成内容
- 代码：`code/run_experiment.py`（完整可复现，固定 seed=0，从冻结数据 `data/url.csv` 重算全部指标）
- 结果：`results/evidence_table.csv`、`results/metrics.json`
- 结论：`claim.md`（四档标签 + 关键数字 + 失败条件）、`report.md`（方法/结果/结论/局限）
- 本文档：执行摘要

## 执行摘要

| 指标 | 标准训练 | 对抗训练 (FGSM-AT) |
|---|---|---|
| clean 精度范围 | 91.64–94.44% | 89.90–92.83% |
| clean 跨度 | 2.80pp | 2.93pp |
| robust 精度范围 (PGD-L2 ε=0.25) | 12.42–50.87% | 76.95–77.78% |
| robust 跨度 | **38.45pp** | 0.83pp |
| robust 均值 | 25.59% | 77.56% |

- 平均鲁棒提升：**+51.97pp**；平均干净精度变化：**−1.53pp**。
- 划分：train 7,315 / val 1,829 / test 2,286（DefaultSplitter, seed 42）；正类率 50.0%。
- 方法：train-only min-max 缩放 clip [0,1]；4 个 MLP（[64]/[128,64]/[256,128,64]/[128,64]+dropout0.3）；Adam(lr=1e-3, wd=1e-4)、batch 256、12 epochs；标准 + FGSM-AT(ε=0.1)；评估 PGD-L2 40 步 ε=0.25（L2 球投影 + [0,1] clip）。

## 结论标签
- **C1：`supported`** —— clean 跨度 2.80pp ≤ 5pp 且 robust 跨度 38.45pp ≥ 15pp。
- **C2：`supported`** —— 平均鲁棒提升 +51.97pp ≥ 20pp 且平均干净下降 1.53pp ≤ 5pp。

## 复现
```bash
python code/run_experiment.py
```
环境：Python 3.13, numpy 2.5.2, pandas 3.0.5, torch 2.13.0+cpu, scikit-learn。
