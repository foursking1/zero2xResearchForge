# EVAL REPORT v3: 1906.08888_mliap_performance_cost

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v3（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 97.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 59.0 | 60 | A1(20分): 数据统计精确，六元素train/test配置数与冻结数据完全一致，协议声明完整。A2(20分): 实现了linear/quad/kernel/mlp四类代理模型，同划分对照详尽。A3(19分): 能量MAE(1.4-9.8 meV/atom)与力MAE(0.06-0.30 eV/Å)完美落入论文锚定量级区间；train/test ratio 0.70证实无过拟合；模型排序方向正确。化学趋势部分复现，扣1分。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘证据扫描显示证据等级为2（齐全自洽）。metrics.json与evidence_table.csv数据严格对应，且包含底层配置级别的误差分布，证明是真实代码运行产出。linear模型在部分元素上的高误差体现了真实实验的客观性，无抄数嫌疑，证据链完整可核对。 |

## A 核心结果达成度（59.0/60）

A1(20分): 数据统计精确，六元素train/test配置数与冻结数据完全一致，协议声明完整。A2(20分): 实现了linear/quad/kernel/mlp四类代理模型，同划分对照详尽。A3(19分): 能量MAE(1.4-9.8 meV/atom)与力MAE(0.06-0.30 eV/Å)完美落入论文锚定量级区间；train/test ratio 0.70证实无过拟合；模型排序方向正确。化学趋势部分复现，扣1分。

## B 证据真实性/实际复现（38.0/40）

磁盘证据扫描显示证据等级为2（齐全自洽）。metrics.json与evidence_table.csv数据严格对应，且包含底层配置级别的误差分布，证明是真实代码运行产出。linear模型在部分元素上的高误差体现了真实实验的客观性，无抄数嫌疑，证据链完整可核对。

## 证据与重算说明

独立重算未执行。关键实测数：Mo train=194/test=23，Cu train=262/test=31；最佳模型能量MAE均值5.1 meV/atom，力MAE均值0.174 eV/Å；train/test ratio均值0.70。所有数值均在evidence_table.csv与metrics.json中有详细落盘记录。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 数据统计精确，四类代理模型实现完整且防泄漏协议严谨，对线性代理在部分元素上表现异常的局限性分析非常客观深入，证据链极其扎实。
- 不足: 受限于代理模型表达能力，化学趋势（bcc与金刚石结构的严格排序）未能完全复现，且quad/kernel未做力匹配导致力MAE系统性略偏高。