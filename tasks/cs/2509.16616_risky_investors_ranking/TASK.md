# 科研任务：风险交易者排序预测（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id: `2509.16616_risky_investors_ranking`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Learn to Rank Risky Investors: A Case Study of Predicting Retail Traders' Behaviour and Profitability（arXiv:2509.16616；ACM TOIS 2025, DOI 10.1145/3768623）
- 领域：CS / 金融行为预测 / Learning-to-Rank

## 问题（可证伪）

论文提出 PA-RiskRanker，把"识别高风险交易者"重构为排序任务（profit-aware BCE 损失 + transformer + self-cross-trader attention），并报告核心结论：**相比既有分类/异常检测方法与 LETOR 排序模型（如 Rankformer、λMART），PA-RiskRanker 在盈利相关的风险排序上显著更优**（主数据集为专有券商交易数据，未公开）。论文附录 D 用两个公开数据集（信用卡欺诈检测、岗位盈利预测）做了可复现实验，在 **with-prior 设置**（评估时使用"1% 交易者为风险"先验）下报告 3-fold 交叉验证平均值：PA-RiskRanker 在**两个数据集上均为最高 F1 且最低财务损失**——信用卡欺诈：F1=0.9870、财务损失=31,368.39（对照 Rankformer F1=0.9820、损失=43,821.78）；岗位盈利：F1=0.9491、财务损失=19,363.32（对照 Rankformer F1=0.8539、损失=59,177.19）。

可证伪表述（基于本包冻结数据，with-prior 设置、3-fold CV）：

- (a) 「PA-RiskRanker 的平均 F1 为所有基准中最高」在信用卡欺诈数据集上是否成立；
- (b) 同上在岗位盈利数据集上是否成立；
- (c) 「PA-RiskRanker 的财务损失（对每个误分类样本按其金额/利润计罚）为所有基准中最低」在两个数据集上是否成立；
- (d) PA-RiskRanker 相对最强排序基线（Rankformer）的 F1 提升方向是否与论文一致（两个数据集均提升）。

## 方向提示（非方法步骤）

- 指标：F1（主要）、Financial Loss、AUC、Precision、Sensitivity、Specificity；以 3-fold 平均报告（与论文 Table 8/9 口径一致）。财务损失 = 每个误分类样本按其金额（creditcard 的 Amount）/利润（jobprofit）计罚后求和。
- 标签构造（论文附录 D）：creditcard 以 `Amount` 列作为财务损失代理，按 Amount 降序标记 top 1% 为正类；jobprofit 按 profitability 排序标记 top 1% 为正类，且**删除含未来信息的列**（`Job_Number`、`Jobs_Subtotal`、`Labor`、`Jobs_Total`、`Lead_Generated_From_Source`、`Pricebook_Price`、`Jobs_Gross_Margin`）。
- 划分：70% / 10% / 20%（train / val / test），保持 1%/99% 类别不平衡；ranking group 分配按论文 §3.2；本包冻结**原始 CSV**，标签/划分/分组由你按上述协议构造（固定随机种子，报告中声明）。
- 模型：实现 PA-RiskRanker（PA-BCE + transformer + self-cross-trader attention），并实现 ≥1 个排序基线（Rankformer 或 λMART；建议两者都做）与可选分类/异常检测基线；**以 Rankformer 为最强排序对照**。参考官方仓库 https://github.com/waylonli/PARiskRanker（MIT）——可参考其实现，但本包不随附代码。
- with-prior 设置：按论文定义（评估使用 1% 风险先验）；报告时必须声明实现口径。
- 防泄漏：训练只用 train 划分；val 仅用于早停/超参；test 只用于最终评估；冻结 folds 不得重新划分或从外部下载其他版本数据。

## 数据说明

- 数据包：`data/`（冻结真实数据；来源/许可/checksum 见 `data/SOURCE.md` 与 `data/source_manifest.json`）
  - `creditcard/creditcard.csv`：信用卡欺诈检测原始数据（Kaggle 官方，284,807 行 × 31 列，30 特征 + Class）；标签由你按附录 D 协议构造（Amount 降序 top 1% 为正类）
  - `jobprofit/job_profitability.csv`：岗位盈利原始数据（Kaggle 官方，9,998 行 × 31 列）；使用时删除含未来信息的列（`Job_Number`、`Jobs_Subtotal`、`Labor`、`Jobs_Total`、`Lead_Generated_From_Source`、`Pricebook_Price`、`Jobs_Gross_Margin`），并按 profitability 排序标记 top 1% 为正类
- 来源：Kaggle 官方数据集（creditcardfraud：mlg-ulb/creditcardfraud；job-profitability：ulrikthygepedersen/job-profitability），经 Kaggle 公开 API 下载。
- 许可：creditcardfraud（ODbL 1.0，Kaggle 官方页标注 "Database: Open Database, Contents: Database Contents"）；job-profitability（CC BY 4.0）；本包仅用于学术研究评测。作者官方实现（GitHub waylonli/PARiskRanker，MIT）可作参考，但不随附数据。
- checksum（sha256）：见 `data/source_manifest.json`。

## 输出要求（提交物）

1. **结论**：对 claim (a)–(d) 分别给出 `supported / partially_supported / contradicted / inconclusive`，并说明数据支持的强度与局限。
2. **证据表**：`results/evidence_table.csv`，至少含列：`dataset`、`setting`（with_prior / without_prior）、`model`、`fold`（或 mean）、`f1`、`financial_loss`、`auc`、`precision`、`sensitivity`、`specificity`。
3. **代码**：完整可复现的预处理（从冻结 csv 构造标签/划分/分组）、模型训练（PA-RiskRanker + 基线）、3-fold 评估脚本（固定随机种子），从 `data/` 读取冻结数据。
4. **报告**：`report.md`：标签/划分/分组构造细节、模型架构与训练细节、with-prior 口径、财务损失计算口径、与论文 Table 8/9 的对照（方向与量级）、防泄漏说明、局限性。

## 数据铁律提醒

- 只使用本包冻结数据；禁止合成/模拟数据替代；禁止从网络下载其他版本的数据或重新采样。
- 冻结 folds 固定；test 划分只用于最终评估；模型训练不得使用 test 样本。
- 财务损失必须按论文口径（误分类样本按其金额/利润计罚）计算并报告。
- 禁止把论文数值当作"本实验实测"；所有指标必须由你的代码从本包数据算出。