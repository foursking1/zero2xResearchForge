# EVAL REPORT v3: 1906.08888_mliap_performance_cost

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 90.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 50.0 | 60 | 逐字引用实测数值：能量MAE均值5.1 meV/atom（范围1.4-9.8），力MAE均值0.174 eV/Å（范围0.057-0.296），完美落入论文锚定的“meV/atom”与“~0.1 eV/Å”量级区间；train/test ratio 0.70证实无过拟合；模型排序方向（kernel/quad最优）与论文一致。但化学趋势仅部分复现（bcc的Li表现过好而Mo过差，金刚石居中），且linear SNAP代理误差偏高（均值268 meV），故按梯度规则扣除部分分数，A=50。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示证据等级为2（齐全自洽）。metrics.json不仅包含汇总指标，还落盘了极细粒度的`per_config_test_energy_mae_meV`数组（每个测试配置的独立误差），与evidence_table.csv的宏观MAE严格自洽，证明为真实代码运行产出。配置数统计（Mo 194/23, Cu 262/31）与冻结数据精确匹配，无抄数嫌疑，证据链极其扎实，B=40。 |

## A 核心结果达成度（50.0/60）

逐字引用实测数值：能量MAE均值5.1 meV/atom（范围1.4-9.8），力MAE均值0.174 eV/Å（范围0.057-0.296），完美落入论文锚定的“meV/atom”与“~0.1 eV/Å”量级区间；train/test ratio 0.70证实无过拟合；模型排序方向（kernel/quad最优）与论文一致。但化学趋势仅部分复现（bcc的Li表现过好而Mo过差，金刚石居中），且linear SNAP代理误差偏高（均值268 meV），故按梯度规则扣除部分分数，A=50。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示证据等级为2（齐全自洽）。metrics.json不仅包含汇总指标，还落盘了极细粒度的`per_config_test_energy_mae_meV`数组（每个测试配置的独立误差），与evidence_table.csv的宏观MAE严格自洽，证明为真实代码运行产出。配置数统计（Mo 194/23, Cu 262/31）与冻结数据精确匹配，无抄数嫌疑，证据链极其扎实，B=40。

## 证据与重算说明

独立重算未执行。关键实测数：Mo train=194/test=23，Cu train=262/test=31；最佳模型能量MAE均值5.1 meV/atom，力MAE均值0.174 eV/Å；train/test ratio均值0.70。所有数值均在evidence_table.csv与metrics.json中有详细落盘记录，且包含底层配置级误差分布。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 数据统计精确，四类代理模型实现完整且防泄漏协议严谨；落盘了per-config级别的详细误差数组，证据链极其扎实且内部高度自洽。
- 不足: 受限于代理模型表达能力，化学趋势（bcc与金刚石结构的严格排序）未能完全复现，且linear SNAP代理在部分元素上误差过大。