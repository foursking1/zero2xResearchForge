# agent_solution — 2509.10151_benchecg_xecg

验证 BenchECG/xECG 论文「xECG 在 PTB-XL 分类上显著优于 ST-MEM」的再复现工作。

**结论标签：`inconclusive`**（冻结数据无诊断标签，诊断口径指标不可计算；详见 `claim.md`）。

## 目录结构

```
agent_solution/
├── claim.md                 # 三问判定 + 结论标签 + 关键数字（首要提交物）
├── solution.md              # 方法说明与结果（精简）
├── report.md                # 完整报告（方法/结果/局限/防泄漏）
├── README.md                # 本说明
├── code/                    # 可复现脚本（01 审计 → 05 汇总）+ code/README.md
├── results/                 # 全部中间与最终产物
│   ├── data_audit.json      # Q1：schema/样本/导联/标签结构；SHA-256
│   ├── preprocessing.json   # 预处理参数 + 归一化统计量（train-only 拟合）
│   ├── preprocessed.npz     # 预处理后的信号/标签缓存
│   ├── model_metrics.json   # 模型指标（3 seeds 均值±std）
│   ├── evidence_table.csv   # model,metric,value,std,n_runs
│   ├── metrics.json         # 样本/标签统计 + 模型指标 + 锚对照 + 结论标签
│   ├── predictions_for_figs.json
│   └── fig_*.png            # ECG 示例 / ROC / 模型对比
└── evidence/                # 关键证据副本（供评审判读）
```

## 关键事实与数字

- 冻结 PTB-XL-small：train 1000 / validation 1000；12 导联；5,000 采样/导联（10 s @ 500 Hz）；**schema 无诊断标签列**。
- 由于标签缺失，诊断任务（论文锚 AUROC 0.853/0.674、ST-MEM 0.702/0.436）**无法在冻结数据上重算** -> 结论 inconclusive。
- 流程自检（辅助目标 sex / age≥65，多标签 macro 口径，3 seeds CPU）：
  - Simple1DCNN：macro AUROC **0.8171±0.0029**，macro F1@0.5 **0.7104±0.0205**；
  - 手工特征逻辑回归：macro AUROC 0.7237，macro F1 0.6377；
  - 深度模型 > 浅层基线的差距格局与论文结构方向一致（但非同任务，不作支持证据）。

## 复现

```bash
cd code/
python3 01_audit_data.py && python3 02_preprocess.py && python3 03_train_models.py \
  && python3 04_figures.py && python3 05_export_evidence.py
```

纯 CPU，约 5 分钟；详见 `code/README.md`。