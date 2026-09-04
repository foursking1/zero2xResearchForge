# PAPER_ANCHOR（私有，仅裁判/编译者可见）：2509.16616_risky_investors_ranking

> 用途：LLM judge 判分基准。本卡为 L1（critical claim，论文公开，但锚值仅本文件可见）。数值从 arXiv:2509.16616v1（ACM TOIS 2025, DOI 10.1145/3768623）附录 D 抽出（Table 8 / Table 9 / 附录 D.1-D.2），禁止臆造。

## 目标论文

- Li, W. W., Ma, T. (2025), "Learn to Rank Risky Investors: A Case Study of Predicting Retail Traders' Behaviour and Profitability"（arXiv:2509.16616；ACM TOIS 44(1), Article 15）。
- 核心论断：PA-RiskRanker（PA-BCE 损失 + transformer + self-cross-trader attention）把风险交易者识别重构为排序任务后，在盈利相关风险排序上显著优于分类/异常检测/既有 LETOR 方法。
- 主数据集为专有券商交易数据（13,607,120 条记录 / 20,514 交易者，论文 §3："this dataset is not made publicly available"）→ 本卡锚点全部取**附录 D 的两个公开数据集复现实验**（Table 8/9）。
- 摘要口径声明：摘要中 "8.4% F1 increase vs Rankformer" 与 "10%-17% increase in average profit" 基于**专有交易数据集**，本卡无法复现，仅作背景。

## 锚 A1 — 信用卡欺诈（creditcard fraud）with-prior 结果（Table 8，判 A1/A2 维度）

| 项 | 值 |
|---|---|
| 指标名 | 3-fold CV 平均 F1（主）；Financial Loss（对每个误分类样本按其 Amount 计罚求和）；AUC / Precision / Sensitivity / Specificity |
| 论文数值（with prior） | **PA-RiskRanker：F1=0.9870、Loss=31,368.39、AUC=0.9998、Precision=0.9743、Sensitivity=0.9743、Specificity=0.9998**；Rankformer：F1=0.9820、Loss=43,821.78；λMART：F1=0.9694、Loss=72,817.16；XGB：0.9755/58,149.26；LGBM：0.9729/63,659.04；FT-Transformer：0.9593/88,705.93；Random Forest：0.9682/74,770.60；DeepSAD：0.9767/52,499.95；FeaWAD：0.7072/486,894.08；SLAD：0.5960/745,006.85；DIF：0.5988/725,901.98；SOUR：0.4949/1,070,615.77；PA-λMART：0.9667/83,895.95；LambdaLoss：0.9540/104,886.57 |
| 出处 | 附录 D.1，Table 8（with prior 块） |
| 判分口径 | agent 用本包 creditcard 冻结数据实现 PA-RiskRanker + 基线，with-prior 设置、3-fold CV，报 F1/loss 对比 |

## 锚 A2 — 岗位盈利（job profit）with-prior 结果（Table 9，判 A1/A2 维度）

| 项 | 值 |
|---|---|
| 指标名 | 同上 |
| 论文数值（with prior） | **PA-RiskRanker：F1=0.9491、Loss=19,363.32、AUC=0.9996、Precision=0.8571、Sensitivity=0.9506、Specificity=0.9986**；Rankformer：F1=0.8539、Loss=59,177.19；λMART：F1=0.9247、Loss=28,665.63；XGB：0.9247/28,348.70；LGBM：0.9244/27,838.33；FT-Transformer：0.8285/72,724.86；Random Forest：0.8980/37,132.58；DeepSAD：0.4953/171,425.37；FeaWAD：0.7724/77,227.59；SLAD：0.6435/112,685.96；DIF：0.5971/162,701.42；SOUR：0.4953/171,425.37；PA-λMART：0.8799/51,606.02；LambdaLoss：0.8342/69,817.75 |
| 出处 | 附录 D.2，Table 9（with prior 块） |
| 判分口径 | 同上（jobprofit 冻结数据） |

## 锚 A3 — 无 prior 设置（辅助方向校验，Table 8/9 without prior 块）

| 项 | 值 |
|---|---|
| creditcard（without prior） | PA-RiskRanker：F1=0.9856、Loss=35,332.36；Rankformer：F1=0.9811、Loss=45,342.84（PA-RiskRanker 仍最优） |
| jobprofit（without prior） | PA-RiskRanker：F1=0.9359、Loss=28,266.70（第 2 优）；LGBM：F1=0.9369、Loss=21,695.83（第 1）；XGB：0.9263/27,530.39；Rankformer：0.8190/83,849.98 |
| 出处 | Table 8/9（without prior 块）；附录 D.2 正文："in the without prior setting, prediction models such as LGBM and XGB outperform most ranking methods, with PA-RiskRanker ranking as the second-best overall" |
| 判分口径 | 若 agent 报告 without-prior，检查方向（creditcard 上 PA-RiskRanker 最优；jobprofit 上分类器反超、PA-RiskRanker 第 2） |

## 辅助数据事实（裁判 B 维度抽查基准；从冻结数据直接核验）

| 字段 | 冻结参考值 | 备注 |
|---|---|---|
| creditcard.csv 规模 | 284,807 行 × 31 列（30 特征 + Class；Kaggle 官方） | 冻结数据含作者预处理版与 folds |
| job_profitability.csv 规模 | ~9,998 行 × 13 列（Kaggle 官方，CC BY 4.0） | 冻结数据含作者预处理版与 folds |
| 正类比例 | 1%（top-1% 按 Amount/profitability 排序） | 作者预处理后每 fold 保持 1%/99% |
| fold 结构 | 本包冻结原始 CSV；fold（70/10/20、1%/99%）由 agent 按附录 D 协议自建 | 以固定随机种子可复算 |

## 判分对照速查（judge 用）

- A1/A2 满分：with-prior、3-fold 平均下，PA-RiskRanker 在**两个数据集**上均为 F1 最高且 loss 最低；且相对 Rankformer 的 F1 提升方向与论文一致（creditcard 与 jobprofit 均提升）。
- 若仅 1 个数据集成立 → 半满带（方向部分一致）。
- A3 校验：若 agent 报告 without-prior，jobprofit 上 LGBM/XGB 反超排名方法、PA-RiskRanker 第 2 → 与论文一致，加分/给满分参考；若 agent 声称 PA-RiskRanker 在所有设置全胜（与论文矛盾）且无解释 → C 维度扣分。
- B 抽查两数：(1) 冻结数据 fold 结构/正类比例（1%、3 fold）；(2) 重跑 agent 代码核对某数据集 with-prior 的 F1/loss 与 evidence_table 一致。
- 容差说明：模型训练细节由 agent 决定（可参考官方仓库），且本包冻结**原始 CSV**（划分由 agent 自建）→ 绝对 F1/loss 与论文必然存在划分方差，不强求逐值复现；判分以**方向 + 排序**为主。F1 方向带 ±0.01（相对 Rankformer 的提升方向必须一致），loss 方向带 ±10%；若 agent 复现方向与排序一致但数值偏离大，B 维度检查其计算口径（如 loss 是否按 Amount 计罚、Sensitivity/Specificity 阈值口径、划分种子）。with-prior 口径必须声明。