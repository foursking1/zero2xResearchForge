# 科研任务：表格数据 Attention vs Contrastive 基准中的难度划分与传统方法竞争力（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id: `2401.04266_attention_vs_contrastive`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Attention versus Contrastive Learning of Tabular Data — A Data-centric Benchmarking（arXiv:2401.04266，2024）
- 领域：CS / 表格数据 / 表示学习基准

## 问题（可证伪）

论文在 28 个 OpenML 公开表格数据集（14 hard + 14 easy，论文 Table 2）上系统比较了 LR/GBT/DNN/Attention/Contrastive 等 13 种方法，核心结论是「表格数据上不存在对所有数据集都最优的学习方法；传统 ML 在 easy-to-classify 数据集上经常优于深度方法，attention/contrastive 深度方法在 hard 数据集上更占优（SAINT 平均秩 hard=1.69 / easy=5.46，Table 4/5）」。

本任务用可负担的方法子集（LR、GBT、MLP 作为 DNN 代理）在冻结的 28 个数据集上验证三个子 claim：

- **(a) 难度划分可恢复性**：论文定义 hard ⇔ GBT 的 F1 比 LR 高 ≥4 个百分点（Table 2 表注）。按此定义，用你自己的 LR/GBT 实现重算，hard 组多数数据集（≥10/14）应满足 gap ≥4pp，easy 组多数（≥11/14）应满足 gap <4pp。论文自身 Table 6 数值下为 12/14 hard 与 14/14 easy。
- **(b) 传统方法在 easy 数据集上占优**：easy 组中，LR 或 GBT 的 F1 不低于 MLP 的数据集占比 ≥ 8/14（支撑论文「traditional methods are frequently superior on easy-to-classify datasets」）。
- **(c) 不存在全局最优方法**：hard 组中 MLP（深度代理）并不会系统性超过 GBT（胜出 ≤7/14），与「no best learning method exists for all tabular data sets」一致；「深度方法在 hard 占优」的完整表述依赖 SAINT/NPT 等 attention/contrastive 模型（论文 SAINT AvgRank 1.69），本任务不要求训练这些模型，仅在报告中讨论。

## 方向提示（非方法步骤）

- 指标：**macro-F1**（论文因类别不平衡选用 F1；其表值更接近 sklearn weighted-F1 口径，任务统一用 macro-F1，报告中须讨论口径差异与 ±5pp 以内偏差）。
- 划分：论文 §4.1 为 30 次随机 70% train / 10% val / 20% test，固定种子。建议 ≥5 个固定种子（如 0–4）做分层划分取平均；只用 train 拟合预处理与模型。
- 预处理：类别列 one-hot（handle_unknown='ignore'）、数值列标准化、缺失值插补（类别 most_frequent / 数值 median）；所有统计量只从 train 拟合（sklearn Pipeline 天然满足）。
- 模型：LR（sklearn `LogisticRegression(max_iter≥2000)`）、GBT（sklearn `HistGradientBoostingClassifier` 或 `GradientBoostingClassifier`）、MLP（sklearn `MLPClassifier(hidden_layer_sizes=(256,128,64,32,32))`，对应论文 DNN 结构 input-256-128-64-32-32-output，早停）。
- 防泄漏：test 不得参与拟合/插补/标准化/调参/早停；28 个数据集的 target 只用于有监督训练与评估。

## 数据说明

- 数据包：`$PAPER_BENCH_DATA_DIR/datasets`（28 个 CSV + `dataset_manifest.json`，44MB）。
- 文件：`<openml_id>_<slug>.csv`；schema = OpenML 原始特征列（类型/缺失值保持原样）+ 末尾 `target` 列（OpenML 默认目标，字符串标签）。
- `dataset_manifest.json`：openml_id / slug / difficulty（论文 Table 2 标签）/ shape / classes / target 列名。
- 来源：OpenML 官方 API（https://www.openml.org ），公开数据集，无需注册/API key；逐文件 SHA-256 登记 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`。

## 输出要求（提交物）

1. **结论**：对 (a)(b)(c) 三个子 claim 分别给出 `supported / partially_supported / contradicted / inconclusive`，并说明数据支持的强度与论文 Table 4/5/6 的对照。
2. **证据表**：`results/evidence_table.csv`，至少含列：`openml_id`、`name`、`difficulty_paper`、`n`、`features`、`classes`、`f1_lr`、`f1_gbt`、`f1_mlp`、`gap_gbt_minus_lr_pp`、`predicted_difficulty`、`agree`；并汇总 `n_hard_agree`、`n_easy_agree`、`trad_better_on_easy`、`mlp_better_on_hard`。
3. **代码**：完整可复现脚本（含固定种子），从冻结 CSV 读取数据。
4. **报告**：`report.md`：方法（预处理/模型/种子）、F1 口径说明、与论文差异（论文 30 次划分 + 疑似 weighted-F1 + GBM 实现差异）、局限性（未训练 SAINT/NPT、MLP 仅作 DNN 代理）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成/模拟数据替代。
- test 只用于最终评估；禁止用于训练、验证、早停、调参或插补/标准化统计量拟合。
- 28 个 CSV 不得修改；报告中必须说明与论文全量实验（13 方法 × 30 次划分）的差异。
