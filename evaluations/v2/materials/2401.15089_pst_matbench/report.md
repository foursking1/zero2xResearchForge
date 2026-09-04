# EVAL REPORT v2: 2401.15089_pst_matbench

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 91.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 53.0 | 60 | A1(数据与协议,18/20): Agent报告了fold0样本数(mp_gap train 76401/val 8489/test 21223等)及5折CV协议(固定seed=42, 验证集early stopping)，数据统计正确且协议清晰，但仅详细列出fold0而非全量5折统计，扣2分。A2(模型与回归,25/25): Agent完成了mp_gap, mp_e_form, log_gvrh三个属性的5折CV，并包含Band Gap消融对照，使用了任务允许的LightGBM简化代理模型，满足满分条件。A3(主论断验证,10/15): 实测MAE为mp_gap 0.5037 eV, mp_e_form 0.1671 eV/atom, log_gvrh 0.1084 log10(GPa)。与论文锚值(0.210/0.032/0.074)相比，绝对精度有差距(特别是Formation差约5倍)，但消融方向(PDD-only 0.8142 > Comp-only 0.5275 > 组合 0.5156)与论文(PDD 0.596 > Comp 0.273 > PST 0.212)完全一致。属于“部分”满足，落入8-11分带，给10分。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘扫描显示metrics.json、evidence_table.csv、代码及日志文件均存在。evidence_table.csv中的逐折MAE(如mp_gap fold0 0.5026)及消融结果(Comp-only 0.5275等)与metrics.json、report.md及run_task5.log中的数值严格一致，证据链完整且可核对。符合“有证据文件且数值与报告严格一致”的[30,40]区间，给38分。 |

## A 核心结果达成度（53.0/60）

A1(数据与协议,18/20): Agent报告了fold0样本数(mp_gap train 76401/val 8489/test 21223等)及5折CV协议(固定seed=42, 验证集early stopping)，数据统计正确且协议清晰，但仅详细列出fold0而非全量5折统计，扣2分。A2(模型与回归,25/25): Agent完成了mp_gap, mp_e_form, log_gvrh三个属性的5折CV，并包含Band Gap消融对照，使用了任务允许的LightGBM简化代理模型，满足满分条件。A3(主论断验证,10/15): 实测MAE为mp_gap 0.5037 eV, mp_e_form 0.1671 eV/atom, log_gvrh 0.1084 log10(GPa)。与论文锚值(0.210/0.032/0.074)相比，绝对精度有差距(特别是Formation差约5倍)，但消融方向(PDD-only 0.8142 > Comp-only 0.5275 > 组合 0.5156)与论文(PDD 0.596 > Comp 0.273 > PST 0.212)完全一致。属于“部分”满足，落入8-11分带，给10分。

## B 证据真实性/实际复现（38.0/40）

磁盘扫描显示metrics.json、evidence_table.csv、代码及日志文件均存在。evidence_table.csv中的逐折MAE(如mp_gap fold0 0.5026)及消融结果(Comp-only 0.5275等)与metrics.json、report.md及run_task5.log中的数值严格一致，证据链完整且可核对。符合“有证据文件且数值与报告严格一致”的[30,40]区间，给38分。

## 证据与重算说明

独立重算未执行。关键实测数：mp_gap MAE 0.5037，mp_e_form MAE 0.1671，log_gvrh MAE 0.1084；消融：Comp-only 0.5275，PDD-only 0.8142，PST-ish 0.5156。所有数值在evidence_table.csv、metrics.json和运行日志中严格对齐，无抄写论文数字嫌疑。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 严格遵循了任务允许的简化代理模型方案，完整执行了5折CV协议，消融实验方向与论文完全一致，且所有实测数据在多份证据文件中严格对齐。
- 不足: Formation Energy的预测精度与论文锚值差距较大（约5倍），未能完全复现PST在全部属性上的绝对精度优势；数据统计仅详细展示了fold0而非全量5折。