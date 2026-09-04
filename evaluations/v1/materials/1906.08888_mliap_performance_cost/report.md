# EVAL REPORT: 1906.08888_mliap_performance_cost

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判（qwen3.7-max）
- 评测时间: 2026-08-19

## 总分: 98.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 58.0 | 60 | A1: agent报告六元素train 194-263, test 23-31，与冻结数据精确一致，协议合理，得20分。A2: 实现了linear/quad/kernel/mlp四类代理模型，同划分对照，得20分。A3: 能量MAE 1.4-9.8 meV/atom，力MAE 0.06-0.30 eV/Å，量级复现；train/test ratio 0.70证明无过拟合；模型排序方向与论文一致（GAP类最优）。化学趋势部分成立，扣2分，得18分。 |
| B 证据真实性 | 25 | 25 | 提交物齐全。抽查字段1：Mo train=194/test=23，Cu train=262/test=31，与冻结数据精确匹配。抽查字段2：evidence_table中最佳模型能量MAE在1.4-9.8 meV/atom，力MAE在0.05-0.3 eV/Å，符合量级；linear代理在部分元素上MAE偏高（285-858 meV），但agent如实记录并分析原因，非抄数。独立重算未执行。得25分。 |
| C 方法与报告 | 15 | 15 | C1: 自写BP描述符+解析梯度+4类代理模型，方法合理（5分）。C2: 固定seed=0，80/20验证集调参，防泄漏严谨（5分）。C3: 报告包含方法、结果、局限分析及明确的结论标签（5分）。得15分。 |

## A 核心结果达成度（58.0/60）

A1: agent报告六元素train 194-263, test 23-31，与冻结数据精确一致，协议合理，得20分。A2: 实现了linear/quad/kernel/mlp四类代理模型，同划分对照，得20分。A3: 能量MAE 1.4-9.8 meV/atom，力MAE 0.06-0.30 eV/Å，量级复现；train/test ratio 0.70证明无过拟合；模型排序方向与论文一致（GAP类最优）。化学趋势部分成立，扣2分，得18分。

## B 证据真实性（25/25）

提交物齐全。抽查字段1：Mo train=194/test=23，Cu train=262/test=31，与冻结数据精确匹配。抽查字段2：evidence_table中最佳模型能量MAE在1.4-9.8 meV/atom，力MAE在0.05-0.3 eV/Å，符合量级；linear代理在部分元素上MAE偏高（285-858 meV），但agent如实记录并分析原因，非抄数。独立重算未执行。得25分。

## C 方法与报告（15/15）

C1: 自写BP描述符+解析梯度+4类代理模型，方法合理（5分）。C2: 固定seed=0，80/20验证集调参，防泄漏严谨（5分）。C3: 报告包含方法、结果、局限分析及明确的结论标签（5分）。得15分。

## 证据与重算说明

独立重算未执行。关键实测数：Mo train=194/test=23，Cu train=262/test=31；最佳模型能量MAE均值5.1 meV/atom，力MAE均值0.174 eV/Å；train/test ratio均值0.70；模型排序kernel/quad < mlp < linear。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 数据统计精确，四类代理模型实现完整且防泄漏协议严谨，对线性代理在部分元素上表现异常的局限性分析非常客观深入。
- 不足: 受限于代理模型表达能力，化学趋势（bcc与金刚石结构的严格排序）未能完全复现，且quad/kernel未做力匹配导致力MAE系统性偏高。