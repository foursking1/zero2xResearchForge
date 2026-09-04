# agent_solution — README

本目录实现了对 arXiv:2308.13068《Multivariate Time Series Anomaly Detection: Fancy
Algorithms and Flawed Evaluation Methodology》所提问题的端到端复现实验：
**以冻结的 SWaT / PSM 实测数据回答「评估协议（point-adjust）是否扭曲了我们对
MVTAD 算法的认知」。**

## 目录结构

```
agent_solution/
├── method/                    # 检测方法
│   ├── pca_baseline.py        #   简单基线：PCA 重建误差(+逐通道残差标准化)、Mahalanobis
│   └── gru_autoencoder.py     #   深度方法：GRU 自编码器（含逐通道标准化变体）
├── protocols/                 # 评估协议
│   └── eval_protocols.py      #   逐点 F1 / point-adjust F1 / 事件级 F1E(含FAR惩罚)
├── baselines/                 # 随机猜测基线
│   └── random_guess.py        #   α 随机点 → 两协议 F1，50 次重复取均值±std
├── scripts/
│   ├── common.py              #   数据加载/NaN填充/z-score/滑窗/阈值(oracle与训练固定)
│   ├── run_pipeline.py        #   全流程（方法+协议+随机猜测 → results/）
│   ├── make_figures.py        #   生成图表 → figures/
│   └── verify_frozen_facts.py #   冻结事实+随机猜测 F1pw 独立复核
├── results/
│   ├── evidence_table.csv     #   数据集×方法×阈值×协议 F1 全表（主交付）
│   ├── metrics.json           #   关键指标（含随机猜测 mean±std、冻结事实）
│   └── predictions/*.npz      #   各方法分数与标签
├── figures/                   # 报告用图（4 张）
├── evidence/                  # data_facts.json、run_pipeline.log
├── solution.md                # 方法说明与核心结果（速读）
└── report.md                  # 完整科研报告（Q1–Q4 + 局限 + 复现）
```

## 快速复现（数据路径不变的前提下）

```bash
cd agent_solution
python scripts/run_pipeline.py          # ~2 分钟（CPU），写 results/
python scripts/make_figures.py          # 写 figures/
python scripts/verify_frozen_facts.py   # 复核 PSM 27.76% 与随机猜测逐点 F1
```

`scripts/common.py` 中 `DATA_ROOT` 指向冻结数据目录（本机：
`/mnt/f/dataset/cs/2308.13068_mvts_flawed_eval/`，见 `data/DATA_LOCATION.md`）。
若迁移路径变化，仅需修改该常量。

## 关键结论（一句话）

**随机猜测在 point-adjust 下 F1≈0.95（SWaT）/≈0.97（PSM），在逐点下仅≈0.004/0.022，
且超过了训练好的深度方法在 point-adjust 协议下的得分（0.848/0.592）；而逐点口径下
简单 PCA（0.796/0.613）在两数据集均不低于深度 GRU-AE（0.789/0.526）。结论标签：
`supported`。**

## 环境

Python 3.13，numpy / pandas / scipy / scikit-learn / torch（CPU 训练，
`torch.set_num_threads(4)`）。运行日志见 `evidence/run_pipeline.log`。