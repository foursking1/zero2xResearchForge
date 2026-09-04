# EVAL REPORT: 2507.05730_had_survey

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判（qwen3.7-max）
- 评测时间: 2026-08-19

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1: agent报告匹配数11/14（evidence_table中match_le_0_01为True的数量），rubric区间[≥10]→30分；3个版本差异行（San Diego, Gulfport, Bay Champagne）在note和报告4.2节中被正确识别并说明原因，无扣分。A2: min_auc=0.8221，全部14行≥0.80，rubric条件[min_auc≥0.80]→15分；mean_runtime=1.2953s，rubric条件[≤5s]→10分；报告4.4节正确表述了「深度方法最准、RX最快且有竞争力但非最高平均精度」的权衡关系→5分。A维度总计60分。 |
| B 证据真实性 | 25 | 25 | 提交物齐全，包含可运行代码（run_rx.py等）、完整的14行+汇总证据表（evidence_table.csv）及详细报告。证据表中auc_rx与auc_paper_rx严格分离，未将论文数字当作实测。抽查关键实测数值：abu-airport-1 auc_rx=0.8221，aviris_1 auc_rx=0.8866，hydice_urban auc_rx=0.9857，均与PAPER_ANCHOR自检锚值精确一致（|Δ|=0）。代码包含SHA-256校验与规范的伪逆马氏距离实现。独立重算未执行，但基于提交物内部一致性与锚值比对，证据真实可信。 |
| C 方法与报告 | 15 | 15 | 方法合理性（5/5）：代码使用全局均值/协方差及np.linalg.pinv计算马氏距离，San Diego正确执行[:100,:100,:]裁剪，AUC计算规范。防泄漏（5/5）：GT仅用于最终的roc_auc_score评估，未参与RX背景统计拟合。局限性与口径（5/5）：报告第6节明确说明了14行冻结子集与论文17行的差异（缺Cri/Salinas/Pavia），第4.2节详述了3个版本差异行的原因，第7节充分讨论了RX全图统计对异常污染的敏感性以及未运行深度方法的边界限制。 |

## A 核心结果达成度（60/60）

A1: agent报告匹配数11/14（evidence_table中match_le_0_01为True的数量），rubric区间[≥10]→30分；3个版本差异行（San Diego, Gulfport, Bay Champagne）在note和报告4.2节中被正确识别并说明原因，无扣分。A2: min_auc=0.8221，全部14行≥0.80，rubric条件[min_auc≥0.80]→15分；mean_runtime=1.2953s，rubric条件[≤5s]→10分；报告4.4节正确表述了「深度方法最准、RX最快且有竞争力但非最高平均精度」的权衡关系→5分。A维度总计60分。

## B 证据真实性（25/25）

提交物齐全，包含可运行代码（run_rx.py等）、完整的14行+汇总证据表（evidence_table.csv）及详细报告。证据表中auc_rx与auc_paper_rx严格分离，未将论文数字当作实测。抽查关键实测数值：abu-airport-1 auc_rx=0.8221，aviris_1 auc_rx=0.8866，hydice_urban auc_rx=0.9857，均与PAPER_ANCHOR自检锚值精确一致（|Δ|=0）。代码包含SHA-256校验与规范的伪逆马氏距离实现。独立重算未执行，但基于提交物内部一致性与锚值比对，证据真实可信。

## C 方法与报告（15/15）

方法合理性（5/5）：代码使用全局均值/协方差及np.linalg.pinv计算马氏距离，San Diego正确执行[:100,:100,:]裁剪，AUC计算规范。防泄漏（5/5）：GT仅用于最终的roc_auc_score评估，未参与RX背景统计拟合。局限性与口径（5/5）：报告第6节明确说明了14行冻结子集与论文17行的差异（缺Cri/Salinas/Pavia），第4.2节详述了3个版本差异行的原因，第7节充分讨论了RX全图统计对异常污染的敏感性以及未运行深度方法的边界限制。

## 证据与重算说明

独立重算未执行。抽查关键实测数值：abu-airport-1 auc_rx=0.8221（锚值0.8221），aviris_1 auc_rx=0.8866（锚值0.8866），hydice_urban auc_rx=0.9857（锚值0.9857），sandiego auc_rx=0.9219（锚值0.9219），与证据表及锚值完全一致。证据表包含所有必需列及汇总行。

## 结论

- **科学结论**: `supported`
- 亮点: 复现工作极其严谨，不仅完美复现了11个精确一致的数据集，还额外实现了CRD算法以验证方法族排序方向，代码包含SHA-256完整性校验，报告对版本差异和局限性的分析非常透彻。
- 不足: 无明显弱点，运行时间受环境负载影响略高于论文标称的0.40s（实测均值约1.3s），但仍在rubric允许的5s范围内，且agent在报告中对此进行了合理的解释。