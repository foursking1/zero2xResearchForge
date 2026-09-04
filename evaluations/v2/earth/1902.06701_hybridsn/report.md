# EVAL REPORT v2: 1902.06701_hybridsn

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 98.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | 1. 核心指标 OA：Agent 报告 HybridSN 3 seeds mean OA = 99.85%（metrics.json 中为 0.998513）。锚值为 99.75%。相对差 d = |99.85 - 99.75| / 99.75 ≈ 0.1%，落入 d ≤ 10% 的满分带 (48-60)。2. 证据绑定：metrics.json 与 evidence_table.csv 均落盘且数值严格一致，授予满分带上限。3. 附加项：报告了 AA (99.74%) 和 Kappa (99.83%)，不扣分；与 SVM 和 2D-CNN 基线进行了对比，不扣分；明确了训练比例 (30%) 和窗口 (25)，不扣分；使用了 3 个随机种子并报告了 ±std，满足加分条件。综合评定 A = 60。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘证据扫描显示 metrics.json 和 evidence_table.csv 均存在，且包含完整的代码文件（66个文件）。evidence_table.csv 中详细列出了 3 个 seed 的逐类 accuracy 以及 OA/AA/Kappa，且 mean 行数值 (0.998513) 与 metrics.json 中的 overall_accuracy 严格一致。划分计数 n_train=3075, n_test=7174 符合 30% 协议。证据真实齐全，数值与报告严格一致、可核对，落入 [30, 40] 区间，给 38 分。 |

## A 核心结果达成度（60/60）

1. 核心指标 OA：Agent 报告 HybridSN 3 seeds mean OA = 99.85%（metrics.json 中为 0.998513）。锚值为 99.75%。相对差 d = |99.85 - 99.75| / 99.75 ≈ 0.1%，落入 d ≤ 10% 的满分带 (48-60)。2. 证据绑定：metrics.json 与 evidence_table.csv 均落盘且数值严格一致，授予满分带上限。3. 附加项：报告了 AA (99.74%) 和 Kappa (99.83%)，不扣分；与 SVM 和 2D-CNN 基线进行了对比，不扣分；明确了训练比例 (30%) 和窗口 (25)，不扣分；使用了 3 个随机种子并报告了 ±std，满足加分条件。综合评定 A = 60。

## B 证据真实性/实际复现（38.0/40）

磁盘证据扫描显示 metrics.json 和 evidence_table.csv 均存在，且包含完整的代码文件（66个文件）。evidence_table.csv 中详细列出了 3 个 seed 的逐类 accuracy 以及 OA/AA/Kappa，且 mean 行数值 (0.998513) 与 metrics.json 中的 overall_accuracy 严格一致。划分计数 n_train=3075, n_test=7174 符合 30% 协议。证据真实齐全，数值与报告严格一致、可核对，落入 [30, 40] 区间，给 38 分。

## 证据与重算说明

独立重算未执行。关键实测数：HybridSN OA=0.998513 (99.85%), AA=0.99737, Kappa=0.99830；2D-CNN OA=0.9967；SVM OA=0.7967。训练集 3075 样本，测试集 7174 样本。evidence_table.csv 与 metrics.json 数值严格对齐，无抄论文数字嫌疑。

## 结论

- **科学结论**: `supported`
- 亮点: 核心指标完美复现，相对误差仅 0.1%；代码结构清晰，防泄漏措施严格（PCA和归一化仅用训练集），多指标与多基线对比详实，证据文件极其完整。
- 不足: SVM 基线复现结果 (79.67%) 与论文锚值 (91.70%) 存在一定差距，虽在报告中给出了合理解释（核参数调优与预处理差异），但基线复现精度略有欠缺。