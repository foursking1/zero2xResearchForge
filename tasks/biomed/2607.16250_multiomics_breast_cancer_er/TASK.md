# 科研任务：TCGA-BRCA 多组学 ER 状态预测「RNA 最强 + 集成增益」关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2607.16250_multiomics_breast_cancer_er`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Benchmarking Machine Learning Models for Multi-Omics-Based Breast Cancer Prediction（arXiv:2607.16250）
- 领域：biomed / 癌症基因组学 / 多组学机器学习

## 问题（可证伪）

论文在 TCGA-BRCA 队列（数据清洗后 549 例，ER 阳性 75.4% / 阴性 24.6%）上，用 RNA 表达（604 特征）、CNV（860 特征）、RPPA 蛋白（223 特征）三组学评测 6 种经典 ML 模型（RF/XGBoost/LightGBM/CatBoost/SVM/LR），采用分层五折交叉验证 + 折内特征选择防泄漏。核心论断：

1. **RNA 表达提供最强预测信号**：RNA-only 下 Random Forest 达到最高分类准确率 92.35±1.07%、宏 F1 89.28±1.57%；XGBoost 最高 Balanced Accuracy 88.69±2.18% 与 ROC-AUC 95.61±1.50%。
2. **多组学集成带来小幅但一致的提升**：集成设置下 Random Forest 达到 Balanced Accuracy 90.3%、ROC-AUC 97.1%，为全部模型最优。
3. **防泄漏评估**：折内特征选择（fold-specific feature selection）+ 分层切分是结论可靠的前提；若在特征选择时泄漏（全数据集选择特征再切分），性能会被高估。

请基于冻结数据回答：

1. **数据装配**：读取冻结的 RNA/CNV/RPPA/临床数据，按患者对齐，构建 ER 状态二分类数据集；报告样本量与 ER+ 比例（论文：549 例、75.4%/24.6%）。
2. **单组学复现**：实现至少 2 个模型（建议 RF + XGBoost）在 RNA-only 上的分层五折 CV（折内特征选择），报告 Balanced Accuracy / Macro F1 / ROC-AUC，与论文对照。
3. **多组学对比**：实现集成（RNA+CNV+RPPA 或 RNA+CNV）并报告指标，验证"集成 ≥ 最佳单组学"；同时做一个**泄漏对照**（全数据特征选择后再切分）说明防泄漏的影响。

- 结论标签（四档之一）：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结，来源/许可/checksum 见 `data/README.md`）
  - `data_mrna_seq_v2_rsem.txt`：TCGA-BRCA RNA-seq（RSEM，基因×样本矩阵；约 154MB）
  - `data_cna.txt`：TCGA-BRCA GISTIC2.0 拷贝数（基因×样本，-2/-1/0/1/2）
  - `data_rppa.txt`：TCGA-BRCA RPPA 蛋白表达（蛋白×样本，log2）
  - `data_clinical_patient.txt`：临床患者数据（含 ER 状态等字段）
  - `LICENSE`：数据许可声明（GDAC TCGA Analysis Pipeline License）
- 来源：cBioPortal Datahub（`brca_tcga_pan_can_atlas_2018` 研究，GitHub cBioPortal/datahub）；论文使用 UCSC Xena 同源 TCGA-BRCA 数据
- 许可：TCGA 数据遵循 Broad Institute GDAC TCGA Analysis Pipeline License（公开研究用途）；cBioPortal 数据hub 附带 LICENSE 文件
- SHA-256（固定）：见 `data/README.md`（下载完成后核对）

## 方向提示（协议建议）

1. **对齐**：三组学与临床按样本 ID（TCGA barcode 前 12 位患者 ID）对齐；取三组学共有的患者。
2. **特征选择**：折内（fold-specific）选择——在每个 CV 折的训练部分内做方差/相关性筛选（如按方差 top-N 或单变量与标签相关），测试折不得参与；N 可参考论文量级（RNA 604、CNV 860、RPPA 223，按你的实现自定并说明）。
3. **模型**：RF/XGBoost 等 scikit-learn 可跑；类别不平衡用 class_weight 或评估 Balanced Accuracy/Macro F1/ROC-AUC。
4. **泄漏对照**：在"全数据特征选择后再分层切分"下重跑同一模型，报告指标差异，验证防泄漏重要性。

## 输出要求（提交物）

1. **`claim.md`**：三问判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从 `data/` 装配并训练/评估。
3. **`results/evidence_table.csv`**：至少含列 `model,omic_set,feature_selection,balanced_acc,macro_f1,roc_auc`。
4. **`results/metrics.json`**：样本量与 ER+ 比例；单组学与集成指标；泄漏对照；论文锚对照；结论标签。
5. **`report.md`**：方法（装配/特征选择/CV）、结果、局限（特征数与论文差异、未含 RPPA 时说明、barcode 对齐规则）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成/模拟数据替代。
- 禁止手工抄写论文数字作为"实测结果"；所有指标必须运行代码得到。
- 防泄漏：任何特征选择只允许在折内训练部分进行；测试折不得参与统计量估计。
- 论文数值（RF 集成 Balanced Acc 90.3% / AUC 97.1% 等）只能用于对照讨论。