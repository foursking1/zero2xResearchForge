# 科研任务：ICU COVID-19 EHR「结局预测基准」关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2209.07805_covid_ehr_bench`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：A Comprehensive Benchmark for COVID-19 Predictive Modeling Using Electronic Health Records in Intensive Care（arXiv:2209.07805）
- 领域：biomed / EHR / ICU 结局预测

## 问题（可证伪）

论文提出两个 ICU 临床任务（结局特异性住院时长预测、早期死亡预测），用 18 个模型（临床评分/传统 ML/基础与高级 DL）在两家真实 COVID-19 EHR 队列（TJH 同济医院 485 例；CDSL HM Hospitales 4,479 例）上评测。核心论断（TJH 队列，论文 Table 5）：

1. **早期死亡预测可达很高判别力**：最优模型（GRU-TA）AUPRC 96.50±3.04 / AUROC 97.70±2.06；临床基线 4C 评分 AUROC 94.16±2.57。
2. **时间感知损失（time-aware loss, TA）显著提升**：TA 变体在多项指标上显著优于原模型（论文 Table 5，带 * 标注，p<0.05）。

请基于冻结数据回答：

1. **数据装配**：解析冻结的 TJH 数据集（同济医院 COVID-19，训练 375 例 + 测试 110 例的时序 EHR：74 项实验室/生命体征 + 年龄/性别），统计样本数、时间步、缺失率，说明与论文 Table 1/2 口径的关系。
2. **早期死亡预测复现**：实现至少 2 个模型（建议一个 ML 基线如 RF + 一个时序模型如 GRU/RNN，可选 TA 损失变体），在冻结测试集上报告 AUROC / AUPRC，与论文对照（GRU-TA 97.70/96.50；4C 94.16）。
3. **TA 损失验证（可选加分）**：对比原模型与 TA 变体，验证"时间感知损失提升指标"。

- 结论标签（四档之一）：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结，来源/许可/checksum 见 `data/README.md`）
  - `time_series_375_prerpocess.xlsx`（及 `_en` 英文版）：TJH 训练集（375 例）
  - `time_series_test_110_preprocess.xlsx`（及 `_en`）：TJH 测试集（110 例）
  - 说明：数据为去标识化 COVID-19 患者时序 EHR（论文 Dataset 1：485 例 = 375+110；74 项实验室/生命体征数值特征 + 2 个人口学特征）
- 来源：GitHub `HAIRLAB/Pre_Surv_COVID_19`（论文引用的公开 TJH 数据集）；论文代码仓库 `yhzhu99/pyehr`
- 许可：TJH 数据随仓库公开发布（仓库 LICENSE：MIT；数据本身为去标识化公开研究数据，使用需遵守原始数据条款与论文引用要求）；CDSL（HM Hospitales）需申请，未包含在本包
- SHA-256（固定）：见 `data/README.md`（下载完成后核对）

## 方向提示（协议建议）

1. **任务定义**：早期死亡预测——在入院/ICU 早期时间窗内预测死亡结局（论文 Problem 2 口径；以数据实际字段定义，如结局列与时间步）。
2. **模型**：RF/GBDT（聚合最后时间步特征或统计量）与 GRU/RNN（序列输入）；TA 损失为对死亡/生存不同时间步加权的损失（论文 §方法），可实现或近似。
3. **评估**：AUROC / AUPRC（论文 Table 5 口径，×100 表示）；固定种子；可报告 mean±std（多次重复）。
4. **缺失处理**：TJH 数据已预处理（论文开放管线），缺失值用前向填充/插补并说明。

## 输出要求（提交物）

1. **`claim.md`**：三问判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从 `data/` 读取并训练/评估。
3. **`results/evidence_table.csv`**：至少含列 `model,ta,auroc,auprc`。
4. **`results/metrics.json`**：样本统计（训练/测试、时间步、缺失率）；各模型 AUROC/AUPRC；论文锚对照；结论标签。
5. **`report.md`**：方法（任务定义/预处理/模型）、结果、局限（仅 TJH 单中心、子集口径、与 pyehr 管线差异）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成/模拟数据替代。
- 禁止手工抄写论文数字作为"实测结果"；所有指标必须运行代码得到。
- 论文数值（GRU-TA AUROC 97.70 / AUPRC 96.50；4C 94.16 等）只能用于对照讨论。
- 测试集（110 例）不得参与训练或超参选择；缺失插补统计量只由训练集拟合。