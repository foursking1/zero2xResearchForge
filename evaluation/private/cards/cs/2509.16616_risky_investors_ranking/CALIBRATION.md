# CALIBRATION（私有）：2509.16616_risky_investors_ranking

> **自测执行：待评测阶段执行（本批次跳过）**。本卡不包含实测分数；以下仅为设计目标与校准杠杆。

## 1. 设计目标区间

- 层级：L1（critical claim）→ 目标区间 **40–50（±10）**。
- 预期强 agent 画像：用冻结预训练数据实现 PA-RiskRanker + Rankformer/λMART 基线，按附录 D 协议（top-1% 正类、70/10/20、ranking groups、with-prior、3-fold CV）复现 Table 8/9 的排序结论，回答 claim (a)–(d)。
- 给方向提示（指标/标签构造/划分/模型参考/with-prior 口径）但不给逐步代码；可参考官方仓库（MIT）→ 中等难度。

## 2. 校准杠杆（如评测阶段偏差时使用）

- **A1/A2 满分带**是主要杠杆：
  - 若强 agent 得分 > 55（偏易）：收紧 A1/A2 为"F1 与 loss 同时最优 且 相对 Rankformer 提升 ≥ 论文幅度的一半"；或要求实现 ≥2 个排序基线 + 1 个分类基线。
  - 若强 agent 得分 < 30（偏难）：放宽为"F1 最高 或 loss 最低（其一）即满分带"；或允许只用 1 个数据集（creditcard）作为主锚、jobprofit 降为加分项；或允许用官方仓库代码直接复现（仍须从冻结数据自证）。
- **锚容差**：Table 8/9 数值真实有出处（附录 D.1/D.2，3-fold 平均）；模型训练细节由 agent 决定 → 判分以**方向 + 排序**为主（F1 ±0.01、loss ±10% 带），不要求逐值复现；with-prior 口径必须声明。
- **数据口径**：冻结原始源 CSV（Kaggle 官方 creditcardfraud + job-profitability），folds 由 agent 按附录 D 协议自建（固定种子）；专有券商交易数据（主数据集）不冻结、不可复现 → TASK.md 已明确锚点全部取附录 D；作者预训练数据（Google Drive 1.05GB）因网络下载不可靠未冻结，SOURCE.md 记录。
- **边界处理**：jobprofit 的 without-prior 设置下论文本身承认分类器（LGBM/XGB）反超、PA-RiskRanker 第 2——若 agent 如实报告此边界（而非声称全胜）→ A3/C 给满分参考；防止 agent 过度声称。

## 3. rubric 定稿说明

- A=60（A1 creditcard with-prior 30 + A2 jobprofit with-prior 20 + A3 跨数据集一致性/摘要声明边界 10）、B=25（fold 结构/正类比例 + 重跑 F1/loss）、C=15（实现与论文 §3.2/附录 D 对应/无泄漏/结论边界）。
- L1 给方向提示；财务损失必须按 Amount/profitability 计罚口径计算。
- 数据：冻结原始源（creditcardfraud ODbL 1.0 + job-profitability CC BY 4.0，Kaggle 官方下载），SHA-256 固定。