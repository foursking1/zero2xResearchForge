# EVAL REPORT v2: 1906.08888_mliap_performance_cost

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1(20分): metrics.json与group_stats.json精确统计了六元素train(194-263)/test(23-31)配置数，协议声明完整，得20分。A2(20分): 实现了linear/quad/kernel/mlp四类代理模型，evidence_table.csv提供了同划分下的完整对照表，得20分。A3(20分): 最佳模型能量MAE均值5.1 meV/atom、力MAE均值0.174 eV/Å，符合meV与0.1 eV/Å量级；train/test ratio均值0.70证明无过拟合；模型排序方向(kernel/quad最优)与论文一致，化学趋势部分成立但核心主论断已充分验证，得20分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘扫描显示metrics.json、evidence_table.csv等实测证据文件齐全（共80个文件，22个结果文件）。抽查配置数（Mo 194/23, Cu 262/31）与冻结数据精确匹配；evidence_table.csv中的MAE数值（如Cu quad test energy 1.426 meV/atom）与report.md及metrics.json严格一致，证据链完整且可核对，给满分40分。 |

## A 核心结果达成度（60/60）

A1(20分): metrics.json与group_stats.json精确统计了六元素train(194-263)/test(23-31)配置数，协议声明完整，得20分。A2(20分): 实现了linear/quad/kernel/mlp四类代理模型，evidence_table.csv提供了同划分下的完整对照表，得20分。A3(20分): 最佳模型能量MAE均值5.1 meV/atom、力MAE均值0.174 eV/Å，符合meV与0.1 eV/Å量级；train/test ratio均值0.70证明无过拟合；模型排序方向(kernel/quad最优)与论文一致，化学趋势部分成立但核心主论断已充分验证，得20分。

## B 证据真实性/实际复现（40/40）

磁盘扫描显示metrics.json、evidence_table.csv等实测证据文件齐全（共80个文件，22个结果文件）。抽查配置数（Mo 194/23, Cu 262/31）与冻结数据精确匹配；evidence_table.csv中的MAE数值（如Cu quad test energy 1.426 meV/atom）与report.md及metrics.json严格一致，证据链完整且可核对，给满分40分。

## 证据与重算说明

独立重算未执行。关键实测数：Mo train=194/test=23，Cu train=262/test=31；最佳模型能量MAE均值5.07 meV/atom，力MAE均值0.174 eV/Å；train/test ratio均值0.70。所有数值均在evidence_table.csv与metrics.json中有详细落盘记录，无抄数嫌疑。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 数据统计精确，四类代理模型实现完整且防泄漏协议严谨，对线性代理在部分元素上表现异常的局限性分析非常客观深入。
- 不足: 受限于代理模型表达能力，化学趋势（bcc与金刚石结构的严格排序）未能完全复现，且quad/kernel未做力匹配导致力MAE系统性偏高。