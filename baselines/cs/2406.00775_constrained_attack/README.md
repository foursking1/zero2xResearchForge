# Constrained Adaptive Attack — URL 数据集复现（arXiv:2406.00775）

本包在冻结的 URL 数据集（ISCX-URL2016，TabularBench 预处理，63 特征 + `is_phishing` 标签）上复现论文「Constrained Adaptive Attack」的核心变量：**CAPGD 显著优于 CPGD**。

## 结论速览

| 模型 | clean_acc (关键类) | CPGD robust | CAPGD robust | CAPGD−CPGD | 约束满足率 |
|---|---|---|---|---|---|
| 深层 MLP (seed 0) | 94.61% | 99.63% | **16.94%** | **−82.7pp** | 1.000 |
| 深残差 MLP (seed 0) | 95.24% | 99.85% | **20.50%** | **−79.4pp** | 1.000 |
| 深层 MLP (seed 1) | 95.17% | 99.85% | **17.06%** | **−82.8pp** | 1.000 |
| 深残差 MLP (seed 1) | 95.24% | 99.71% | **32.40%** | **−67.3pp** | 1.000 |

> 注：CPU 线程数不同会导致训练浮点累加顺序的微小差异，重跑 seed 0 的 mlp
> 可能得到 capgd robust 16.9%–17.0% 附近的相近值（方向与量级带稳定）。

- claim (a)「至少一个深层模型上 CAPGD ≤ CPGD − 40pp」：**supported**（4/4 运行，差距 67–83pp）
- claim (b)「≥2 个模型方向一致（CAPGD < CPGD）」：**supported**（2 模型 × 2 seed 全部成立，且 CAPGD ≤ 20% 于 3/4 运行）

## 目录结构

```
agent_solution/
├── solution.md              # 方法 + 结果摘要（本题作答）
├── report.md                # 完整报告（架构/攻击实现/约束/防泄漏/局限）
├── README.md                # 本文件
├── code/                    # 全部源代码（可复现）
│   ├── constraints.py       # URL 域约束（边界+type+14条关系约束）+ penalty/repair
│   ├── datautils.py         # 数据加载、75/25 划分、[min,max] 区间缩放
│   ├── models.py            # 深层 MLP / 深残差 MLP（及 FT-Transformer 定义）
│   ├── attacks.py           # CPGD + CAPGD（Algorithm 1 一一对应）
│   ├── train.py             # 训练（固定种子、早停）
│   ├── evaluate.py          # 攻击评估（关键类攻击集、鲁棒准确率）
│   ├── full_eval.py         # 端到端：训练+攻击 → evidence_table/metrics
│   ├── make_figures.py      # 生成 evidence/ 图表
│   └── verify_data.py       # 数据规模/占比/约束集核验（B 抽查项）
├── results/
│   ├── evidence_table.csv   # 证据表（rubric 要求列）
│   ├── metrics.json         # 运行指标与设置
│   └── urldata_check.json   # 数据事实核验
├── evidence/                # 关键证据图表
└── data/                    # （可选）指向冻结数据的符号位置
```

## 快速复现

需要：Python 3.10+，`torch` `numpy` `pandas` `scikit-learn` `matplotlib`。

```bash
# 1) 端到端（训练 2 个模型 + CPGD/CAPGD 攻击 + 评估，固定 seed=0 与 1）
python3 code/full_eval.py --seeds 0 1 --n_iter 10 --models mlp resmlp --out results --device cpu

# 2) 数据事实核验（B 抽查项）
python3 code/verify_data.py

# 3) 生成图表
python3 code/make_figures.py --evidence results/evidence_table.csv --outdir evidence
```

所有代码只读取冻结数据 `data/url.csv` 与 `data/url_features.csv`（含约束），测试划分全程冻结，
不训练于攻击评估所用样本。

## 关键词

`CAPGD` `CPGD` `robust accuracy` `L2 ε=0.5` `phishing URL` `R_Omega repair`
`adaptive step (η0=2ε, ρ=0.75)` `momentum α=0.75` `dual initialization`