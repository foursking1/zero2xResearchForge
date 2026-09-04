# EVAL REPORT: 2401.15089_pst_matbench

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判（qwen3.7-max）
- 评测时间: 2026-08-19

## 总分: 88.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 50.0 | 60 | A1: Agent统计了所做3个属性的fold0样本数并说明了5折协议，但未全面展开所有5折的统计，给15/20。A2: 完成了3个属性的5折CV及消融对照，符合任务允许的简化代理模型（LightGBM）要求，给25/25。A3: 实测MAE（Gap 0.504, Form 0.167, Shear 0.108）与论文锚值相比，Shear和Gap同量级，Formation差距较大（约5倍）；消融方向（PDD-only最差，组合最优）与论文一致，落入“部分”band，给10/15。 |
| B 证据真实性 | 23.0 | 25 | 提交物齐全，包含代码、evidence_table、metrics.json和详细报告。mp_gap fold0 train(76401)+val(8489)=84890符合MatBench标准80%划分逻辑，内部数值与日志一致。独立重算未执行，基于证据链完整性与逻辑自洽给23/25。 |
| C 方法与报告 | 15 | 15 | C1: 方法合理，清晰说明了PDD直方图特征与LightGBM代理模型的构建；C2: 防泄漏措施得当，使用验证集进行early stopping且固定种子；C3: 报告结构完整，诚实讨论了简化模型的局限性与结论标签。满分15/15。 |

## A 核心结果达成度（50.0/60）

A1: Agent统计了所做3个属性的fold0样本数并说明了5折协议，但未全面展开所有5折的统计，给15/20。A2: 完成了3个属性的5折CV及消融对照，符合任务允许的简化代理模型（LightGBM）要求，给25/25。A3: 实测MAE（Gap 0.504, Form 0.167, Shear 0.108）与论文锚值相比，Shear和Gap同量级，Formation差距较大（约5倍）；消融方向（PDD-only最差，组合最优）与论文一致，落入“部分”band，给10/15。

## B 证据真实性（23.0/25）

提交物齐全，包含代码、evidence_table、metrics.json和详细报告。mp_gap fold0 train(76401)+val(8489)=84890符合MatBench标准80%划分逻辑，内部数值与日志一致。独立重算未执行，基于证据链完整性与逻辑自洽给23/25。

## C 方法与报告（15/15）

C1: 方法合理，清晰说明了PDD直方图特征与LightGBM代理模型的构建；C2: 防泄漏措施得当，使用验证集进行early stopping且固定种子；C3: 报告结构完整，诚实讨论了简化模型的局限性与结论标签。满分15/15。

## 证据与重算说明

独立重算未执行。关键实测数值：mp_gap MAE 0.5037 eV，mp_e_form MAE 0.1671 eV/atom，log_gvrh MAE 0.1084 log10(GPa)。消融实验：Comp-only 0.5275，PDD-only 0.8142，PST-ish 0.5156。数据行数：mp_gap fold0 train 76401, val 8489, test 21223。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 严格遵循了任务允许的简化代理模型方案，完整执行了5折CV协议，消融实验方向与论文完全一致，报告对局限性的分析非常客观。
- 不足: Formation Energy的预测精度与论文锚值差距较大（约5倍），未能完全复现PST在全部属性上的绝对精度优势；数据统计仅展示了fold0而非全量5折。