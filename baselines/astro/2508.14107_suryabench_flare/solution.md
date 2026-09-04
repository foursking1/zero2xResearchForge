# Solution（完整执行记录）

本文件记录 `2508.14107_suryabench_flare` 任务的完整执行过程、方法、代码、结果与科学结论。所有数字均由 `code/run.py` 从 `data/` 冻结数据重算，未手工抄写任何数值。

## 0. 环境与运行方式

- 环境：Windows 11 / Python 3.13（`numpy 2.5.2, pandas 3.0.5, scikit-learn 1.9.0, matplotlib 3.11.1`）。
- 运行：`python agent_solution/code/run.py`（工作目录任意；脚本经 `__file__` 自动定位 `data/` 与 `results/`）。
- 输出：`agent_solution/results/evidence_table.csv`、`metrics.json`、`figure.svg`、`figure.png`。
- 数据完整性：5 个冻结文件与 `data/SOURCE.md` 记录一致；脚本第 1 步校验标签自洽与拼接一致性。

## 1. 数据与口径（任务问题 1）

加载 `train/validation/test/leaky_validation/data` 5 个文件并校验（脚本第 1/8 步）：

- 行数：train 74,760；validation 3,672；test 43,848；leaky_validation 6,048；全量 128,328 = 四分裂之和。
- `label_max`（⟺ `max_goes_class` ≥ M1.0）与 `label_cum`（⟺ `cumulative_index` ≥ 10）与原始两列在全部行 100% 自洽；`data.csv` 与四分裂按时间逐行一致（`concat_equals_data=True`）。
- label_max 正类率：train 0.1211（9,051/74,760）、validation 0.1089（400/3,672）、**test 0.2943（12,903/43,848）**、leaky 0.1490（901/6,048）、全量 0.1812（23,255/128,328）。
- **漂移**：test − train = +0.1732。test 分年 base rate：2020 0.0055、2021 0.0613、2022 0.2638、2023 0.4435、2024 0.6969。

## 2. 特征工程（严格滞后，任务问题 4）

行 ts 的 `label_max` 描述窗口 [ts, ts+24h)。预测时刻 t 时，只有起点 ≤ t−24h 的窗口**已完全结束**、其标签可知。因此主特征全部基于 `shift(24)+` 的已结束窗口，绝不触碰 shift(1)..shift(23) 的未结束窗口信息。

- **主特征（`FEATS_HIST`，20 维）**：`lag24_lm`/`lag24_cum`/`lag24_flux`（最近已完成窗口 [t−24,t) 状态）；历史 M+ 窗口滚动计数 `nM_prev_{1,3,7,14,30}d`（滚动 24/72/168/336/720h，`min_periods=窗口长`，区间 [t−48,t)、[t−96,t)、[t−192,t)、[t−360,t)、[t−744,t)）；`cum_prev_{3,7,30}d`、`fluxmax_prev_{3,7}d`、`nFQ_prev_7d`（无 ≥C 静止计数）、活动度梯度 `nM_trend`（近3天 − 再前4天）；日历相位 `hour/doy sin/cos`、`year_c`。
- **泄漏参照（`FEATS_LEAKY`，仅量化）**：`shift(1)` 系窗口与目标窗口重叠 23h，含未来信息，**不用于主结果**。
- **绝不泄漏**：被预测窗口自身的 `max_goes_class`/`cumulative_index`/`label_max`/`label_cum` 从不进入特征。
- **Warm-up**：最长滚动窗口 720h（30 天）要求完整历史，显式丢弃最早 743 行（2010-05-13 00:00 起约 31 天），全部落在 train 期（train 有效样本 74,017；validation/test/leaky 无丢弃）。记录于 `metrics.json["warmup"]`。

## 3. 模型与阈值

- 主模型 `LogisticRegression(class_weight='balanced', C=1.0)` + `StandardScaler`（fit 仅用 train）；RandomForest（300 树，balanced）作稳健性对照；另有 `lr_snapshot`（仅最近已完成窗口，类比影像单状态口径）、`lr_hist_noyear`（去年份）、`lr_cal`（仅日历）、`lr_leaky`（泄漏参照）。
- 阈值：在官方 validation 上最大化 TSS，网格 0.01–0.99 步长 0.01 → 主模型 **thr=0.380**。
- 指标定义：TSS=TPR−FPR；HSS=2(TP·TN−FP·FN)/[(TP+FN)(FN+TN)+(TP+FP)(FP+TN)]；F1、CSS(CSI)=TP/(TP+FP+FN)；ROC-AUC。

## 4. 结果（任务问题 2、3）

### 4.1 证据表（主模型 lr_hist，threshold=0.380）

`results/evidence_table.csv`（TSS/HSS 可由 TP/FP/TN/FN 精确重算）：

| period | n | base_rate | tp | fp | tn | fn | tss | hss |
|---|---|---|---|---|---|---|---|---|
| train | 74,017 | 0.1217 | 8084 | 21502 | 43505 | 926 | 0.5665 | 0.2856 |
| validation | 3,672 | 0.1089 | 353 | 826 | 2446 | 47 | 0.6301 | 0.3397 |
| **test** | **43,848** | **0.2943** | 11880 | 10932 | 20013 | 1023 | **0.5674** | **0.4636** |
| leaky_validation | 6,048 | 0.1490 | 760 | 1325 | 3822 | 141 | 0.5861 | 0.3801 |
| test_2020 | 8,784 | 0.0055 | 0 | 50 | 8686 | 48 | −0.0057 | −0.0056 |
| test_2021 | 8,760 | 0.0613 | 257 | 679 | 7544 | 280 | 0.3960 | 0.2939 |
| test_2022 | 8,760 | 0.2638 | 1941 | 3771 | 2678 | 370 | 0.2552 | 0.1733 |
| test_2023 | 8,760 | 0.4435 | 3710 | 4228 | 647 | 175 | 0.0877 | 0.0793 |
| test_2024 | 8,784 | 0.6969 | 5972 | 2204 | 458 | 150 | 0.1475 | 0.1887 |

### 4.2 不确定性与阈值敏感性

- **test TSS 95% CI（Bootstrap，1000 次重采样 test 行）**：[0.5601, 0.5741]，远不含 0 → 正技能统计显著。
- 阈值扫描（0.01–0.99）TSS 包络 **[0.1608, 0.6172]** 恒正；base-rate 阈值处 TSS=0.5006。

### 4.3 泛化归因（真信号 vs 漂移假象）

- **聚合 vs 年内**：聚合 test TSS=0.5674，逐年内 TSS 均值=0.1761（加权 0.1760），差值 ≈0.39 → 聚合技能约 2/3 来自跨年活动水平判别（漂移捕获）。
- **年内阈值无关技能**：分年 test ROC-AUC = 2020 0.750 / 2021 0.788 / 2022 0.755 / 2023 0.733 / 2024 0.792（均值 0.763）——即使太阳极小期也存在真实可分信号；低年内 TSS 主要来自固定阈值未随年基率校准。
- **漂移剔除检验**：`lr_hist_noyear` test TSS=0.523（仍显著），漂移捕获主要通过近期历史活动特征而非年份变量实现（活动自相关的合理物理信号）。
- **仅日历模型**：test TSS=0.000、AUC≈0.159（反预测）——纯日历/相位漂移在 validation 阈值下无迁移技能。
- **泄漏参照**：`lr_leaky`（shift(1) 重叠特征）test TSS=0.968、AUC=0.995，量化"相邻窗口标签"含大量未来信息，故主结果一律排除该口径。
- **稳健性**：`rf_hist` test TSS=0.539（AUC 0.837）、`lr_snapshot` test TSS=0.533（AUC 0.858），与主模型同量级。

## 5. 科学结论

**标签：`partially_supported`。** 详见 `claim.md`。要点：

1. **成立**：严格滞后 GOES 特征 + LR 在未见 test 期（2020–2024，活动周 25 上升期）获得统计显著正 TSS（0.567，CI [0.560, 0.574]）；阈值包络 [0.161, 0.617] 恒正；分年 ROC-AUC 稳定 0.73–0.79（含 2020 极小期）——"正技能跨周期保持"成立，三条失败条件（无正技能 / 漂移假象 / persistence 伪影）均未触发。
2. **限定**：(i) 聚合技能约 2/3 来自 base-rate 漂移捕获（0.567 vs 年内均值 0.176），固定阈值下 2020 极小期 TSS≈0；(ii) 冻结数据无 SDO 影像，本技能为 **GOES 历史 persistence 型**，与论文影像 CNN 口径**不同源**，不可视为论文结果（TSS 0.26–0.36）的数值复现。

## 6. 适用边界与不宣称

- 适用时段 2010-05-13 → 2024-12-31；输入仅 GOES 派生标签序列的严格滞后值 + 日历相位，无影像、无原始通量；类别不平衡经 balanced 权重 + validation 阈值调优处理，报告同时给出阈值扫描包络与 Bootstrap 区间。
- 不宣称：物理因果；影像口径可比性；太阳极小期（2020）可用预报技能；"无漂移的纯泛化"。
