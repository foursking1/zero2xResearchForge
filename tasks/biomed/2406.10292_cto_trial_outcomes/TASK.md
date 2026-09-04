# 科研任务：CTO「LLM+时序链接自动标注临床试验结局」关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2406.10292_cto_trial_outcomes`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Automatically Labeling Clinical Trial Outcomes: A Large-Scale Benchmark for Drug Development（arXiv:2406.10292）
- 领域：biomed / 临床试验结局标注 / 药物开发

## 问题（可证伪）

论文提出 CTO（Clinical Trial Outcome）框架：用「试验阶段链接 + 论文摘要 LLM 解读 + 监管事件（FDA 批准等）」自动聚合临床试验结局标签，替代昂贵且不可及的人工标注。核心论断是：

1. **自动标注与人工标注高度一致**：CTORF（随机森林聚合）在全部试验阶段上的 F1 达 0.909、Cohen's κ 0.729；分阶段 F1 为 Phase I 0.913 / Phase II 0.878 / Phase III 0.941（论文 Table 1，对照人工标注的 TOP 测试集）。
2. **人工标签训练可迁移**：用 CTO 自动标签训练的模型，性能接近用人工标签训练的模型（论文 Figure 3 与相关章节），说明自动标签可作为廉价替代。

请基于冻结数据回答：

- (a) 在冻结的 CTO 预测数据（`phase*/CTORF pred_proba`）上，复现 CTORF 各阶段/全体的 F1 与 κ，与论文 Table 1 对照（注意：冻结文件是 CTORF 模型的预测概率，请说明你如何用阈值/决策规则得到标签并计算指标）。
- (b) 用 `human_labels_2020_2024.csv`（人工标签）与 `labels_and_tickers.csv`（自动标签）统计两类标签的一致性（F1/κ/精确率/召回率），验证"自动标注与人工标注高度一致"论断。
- (c) 说明自动标注可能失效的场景（如无监管事件、摘要缺失、阶段链接断裂），给出证据。

- 结论标签（四档之一）：`supported` / `partially_supported` / `contradicted` / `inconclusive`（可对 (a)/(b) 分别给标签）。

## 数据说明

- 数据包：`data/`（冻结，来源/许可/checksum 见 `data/README.md`）
  - `human_labels_2020_2024.csv`：2020-2024 年人工标注的试验结局（11,012 行；含试验标识、年份、人工标签等）
  - `labels_and_tickers.csv`：自动标签与试验代码对照（含 ticker/试验标识/自动标签概率或类别）
  - `phase1_CTO_rf.csv` / `phase2_CTO_rf.csv` / `phase3_CTO_rf.csv`：各阶段 CTORF 模型对试验的预测概率（`pred_proba` 等列），用于复现论文 CTORF 指标
- 来源：HuggingFace 数据集 `chufangao/CTO`（论文配套发布）
- 许可：HF 仓库公开数据集（论文发布用于科研）；具体许可声明见 `data/README.md`
- SHA-256（固定）：
  - `human_labels_2020_2024.csv` = `C51B9C455DE8C0BEFC07BC3EC58BA4B09DA35767FD7F0D9F2ECB048CDB51FC47`
  - `labels_and_tickers.csv` = `83C20DC302B981B33EB3686288080D1D4B9848A7846485636E5D902024C5B058`
  - `phase1_CTO_rf.csv` = `81963ED27F7FE0F1A87095222F97A9AE774C902CE54BCE8D9C7CC0E38681679F`
  - `phase2_CTO_rf.csv` = `968850AC8C622A218F658E6505F332867C52580B1F9D15E0EA6076CBEE563BFA`
  - `phase3_CTO_rf.csv` = `3061A2CF41051787EACA0324EF2CA80BEB90975E20BF740A4A5D4BF9DF6B3FBC`

## 方向提示（协议建议）

1. **指标口径**：F1 为二分类（成功/失败）宏 F1 或全体 F1；κ 为 Cohen's kappa。与论文 Table 1 对齐时请说明正类定义与阈值。
2. **CTORF 复现**：冻结的 phase 文件含 CTORF 预测概率；可用 0.5 阈值或按论文口径优化阈值得到标签后计算 F1/κ；如文件已含标签列则直接核对。
3. **一致性分析**：人工标签与自动标签按试验标识 join；只统计两边都有标注的样本；报告样本量（论文约 3,239 / 5,060 / 2,823 分阶段匹配量级，以实际数据为准）。
4. **失效场景**：结合 `labels_and_tickers.csv` 中缺失概率/缺失标签的行分析覆盖率。

## 输出要求（提交物）

1. **`claim.md`**：(a)/(b)/(c) 的判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本，从 `data/` 读取并重算 F1/κ/一致性/覆盖率。
3. **`results/evidence_table.csv`**：至少含列 `phase,source,metric,value`（CTORF 复现 + 人工-自动一致性）。
4. **`results/metrics.json`**：各阶段与全体的 F1/κ；人工-自动匹配样本量；论文锚对照（相对差 %）；结论标签。
5. **`report.md`**：方法、结果、局限（标签口径差异、匹配样本量、失效场景分析）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成/模拟数据替代。
- 禁止手工抄写论文数字作为"实测结果"；所有指标必须运行代码得到。
- 论文 Table 1 数值（F1 0.909 / κ 0.729 等）只能用于对照讨论。
- 时间与泄漏：如果做模型训练（可选），只允许用 2020 年前已完成试验做训练、之后做测试（对齐论文时序设计），禁止用未来信息。