# solution.md — 任务 2112.10074 QU-BraTS 不确定性评分与排名解耦（L1）

## 一句话结论

在冻结的 BraTS 2021 mini 数据（10 例，FLAIR 单模态）上实现了论文 QU-BraTS 的不确定性
评估评分（Eq.1：score=(AUC1+(1−AUC2)+(1−AUC3))/3），训练了 MC-Dropout / Deep Ensemble /
确定型三类共 6 个 2D U-Net 分割模型，验证两大核心论断 —— **(1) 不确定性阈值过滤能清除
错误预测、提升剩余体素决策可靠性； (2) 不确定性排名 ≠ 分割精度排名** —— 结论标签：
**supported**。

## 关键数字（3 个 held-out 测试患者均值，`results/evidence_table.csv` 中最优行）

```
model , 实体 , AUC1(DSC) , AUC2(FTP) , AUC3(FTN) , score , dice(τ=100)
det_s2, WT   ,  0.8619   ,  0.1085   ,  0.1322   , 0.8737, 0.7456   ← score 最高
det_s4, WT   ,  0.8403   ,  0.1408   ,  0.1263   , 0.8577, 0.7757
mcd_s0, WT   ,  0.9013   ,  0.2021   ,  0.2056   , 0.8312, 0.8007
```

- **过滤有效**（mcd_s0 WT）：τ 100→25 时 DSC 0.80→0.95 单调上升，FTP/FTN 分别仅 0→0.25。
- **排名解耦**：WT 上 score 第 1 的 det_s2 恰是 DSC 第 5；DSC 第 1 的 ensemble_det 分数第 4；
  各实体 6 模型中 5–6 个排名错位。与论文 Table 2（SCAN：#1/#4，Alpaca：#7/#1）方向一致。
- **分数有效性**：同一分割配“随机不确定性”score 掉 0.23–0.29（WT），证明 score 度量的是
  不确定性信息而非分割精度。

## 做什么 / 怎么做

1. **数据**（`code/01_prepare_data.py`）：解析 parquet 中 gzip NIFTI → 10 例 FLAIR
   + 标注 {1,2,4}；实体掩码 WT/TC/ET；患者级固定划分 train 6 / val 1 / test 3（seed 0）；
   轴向 160² 切片。
2. **模型**（`code/model.py`, `code/train.py`）：2D U-Net（3 头=ET/TC/WT，BCE+soft-Dice），
   MC-Dropout（p=0.3，T=15）与确定型、Deep Ensemble。
3. **不确定性**（`code/evaluate.py`）：预测熵 ×100 ∈ [0,100]；逐测试病例整卷重建。
4. **评分**（`code/qub_metrics.py`）：移植官方评估代码，41 点 τ 网格
   （含 100/75/50/25），`DSC(τ)` 仅在未滤体素上计算，`FTP/FTN` 限脑掩码，
   `AUC1/2/3 = auc(τ,curve)/100`，`score=(AUC1+(1−AUC2)+(1−AUC3))/3`。
5. **汇总**（`code/aggregate.py`, `code/plots.py`, `code/verify.py`）：evidence_table、
   metrics.json、阈值趋势表、图、独立复核。

## 产物

- `claim.md` —— 三问判定 + 结论标签（supported）与关键数字。
- `report.md` —— 完整报告（方法/结果/局限/结论）。
- `code/` —— 全部可复现脚本 + `code/README.md` + `code/verify.py`（审计）。
- `results/` —— `evidence_table.csv`、`metrics.json`、`threshold_means.csv`、
  `threshold_trends.csv`、`random_unc_sanity.csv`、`per_case_results.json`、`figures/`。
- `evidence/` —— 关键证据导出（表 + 图）。
- `models/`、`data_cache/` —— 训练好的 5 个 checkpoint 与解析缓存（可再生成）。

## 复现

```bash
cd agent_solution
bash code/run_all.sh cuda:0     # 端到端：prepare → train → evaluate → aggregate → plots → verify
# 或分部执行各脚本（见 code/README.md）；仅复算表格不重训：python3 code/aggregate.py && code/verify.py
```

环境：Python 3.12 + numpy/pandas/scipy/sklearn/torch/nibabel/matplotlib（离线可用）；
训练默认 cuda:0（峰值 ~1.1GB 显存），CPU 亦可运行但较慢。

## 局限（详见 report.md §7）

BraTS 2021 mini（10 例）单模态 2D 替代口径，绝对精度低于论文 78 队水平（ET/TC 尤弱）；
排名解耦与过滤趋势为稳健的方向性结论，NRS/置换检验等挑战级统计未复现。