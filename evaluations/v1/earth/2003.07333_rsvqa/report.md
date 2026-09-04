# EVAL REPORT: 2003.07333_rsvqa

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判（qwen3.7-max）
- 评测时间: 2026-08-19

## 总分: 70.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 45.0 | 60 | agent 报告 OA=68.10%，锚值 79.08%，相对差 d=13.88%。rubric band 表：[d≤10%→48-60]，[10%<d≤30%→30-47]，[30%<d≤50%→12-29]。d 落入 (10%, 30%] 区间，基础分评定为 42 分。agent 完成了问题类型分解、随机换图消融，并提供了详尽的语言偏差分析（+3分），最终 A 维度得 45 分。 |
| B 证据真实性 | 10.0 | 25 | 提交物包含完整代码和 metrics.json，但 evidence_table.csv 中 prediction 和 correct 列完全为空，导致无法通过证据表直接重算 OA 和按类型准确率进行抽查。根据 rubric『任一抽查无法重建 → B ≤ 10』的规则，B 维度严格限制在 10 分。 |
| C 方法与报告 | 15 | 15 | 方法采用 ResNet+ViT 与 LSTM 融合，架构合理；防泄漏措施严谨，明确采用 image-level 划分避免同一图像跨集泄漏；报告对 count 任务瓶颈、训练规模限制及语言先验进行了深入的边界与局限性分析。C 维度满分 15 分。 |

## A 核心结果达成度（45.0/60）

agent 报告 OA=68.10%，锚值 79.08%，相对差 d=13.88%。rubric band 表：[d≤10%→48-60]，[10%<d≤30%→30-47]，[30%<d≤50%→12-29]。d 落入 (10%, 30%] 区间，基础分评定为 42 分。agent 完成了问题类型分解、随机换图消融，并提供了详尽的语言偏差分析（+3分），最终 A 维度得 45 分。

## B 证据真实性（10.0/25）

提交物包含完整代码和 metrics.json，但 evidence_table.csv 中 prediction 和 correct 列完全为空，导致无法通过证据表直接重算 OA 和按类型准确率进行抽查。根据 rubric『任一抽查无法重建 → B ≤ 10』的规则，B 维度严格限制在 10 分。

## C 方法与报告（15/15）

方法采用 ResNet+ViT 与 LSTM 融合，架构合理；防泄漏措施严谨，明确采用 image-level 划分避免同一图像跨集泄漏；报告对 count 任务瓶颈、训练规模限制及语言先验进行了深入的边界与局限性分析。C 维度满分 15 分。

## 证据与重算说明

独立重算未执行。关键实测数值提取自 metrics.json 与 report：OA=68.10% (0.68095)，presence=87.93%，comparison=86.67%，count=26.87%，rural_urban=100%，随机换图消融=32.14%。evidence_table.csv 缺失 prediction 和 correct 列实际数据。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 防泄漏设计严谨（image-level split），对 count 子任务性能瓶颈及语言先验的消融分析非常深入且诚实。
- 不足: evidence_table.csv 的 prediction 和 correct 列为空，破坏了证据链的完整性，导致裁判无法直接基于表格进行结果抽查与重算。