# EVAL REPORT v2: 2003.07333_rsvqa

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 67.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 45.0 | 60 | 锚值OA=79.08%，Agent报告OA=68.10%（metrics.json落盘证实），相对差d=13.88%，落入(10%, 30%]区间（对应30-47分）。Agent完成了问题类型分解、随机换图消融，并提供了详尽的语言偏差分析（+3分），基础分评定为42分，加分后得45分。 |
| B 证据真实性/实际复现 | 22.0 | 40 | 磁盘扫描显示存在metrics.json和evidence_table.csv，且metrics.json数值与报告一致。但evidence_table.csv中prediction和correct列完全为空（列不完整），导致无法直接通过表格重算OA和按类型准确率。根据强制规则「有证据文件但列不完整」，B落入[16,29]区间，给22分。 |

## A 核心结果达成度（45.0/60）

锚值OA=79.08%，Agent报告OA=68.10%（metrics.json落盘证实），相对差d=13.88%，落入(10%, 30%]区间（对应30-47分）。Agent完成了问题类型分解、随机换图消融，并提供了详尽的语言偏差分析（+3分），基础分评定为42分，加分后得45分。

## B 证据真实性/实际复现（22.0/40）

磁盘扫描显示存在metrics.json和evidence_table.csv，且metrics.json数值与报告一致。但evidence_table.csv中prediction和correct列完全为空（列不完整），导致无法直接通过表格重算OA和按类型准确率。根据强制规则「有证据文件但列不完整」，B落入[16,29]区间，给22分。

## 证据与重算说明

独立重算未执行。关键实测数提取自metrics.json：OA=68.10% (0.68095)，presence=87.93%，comparison=86.67%，count=26.87%，rural_urban=100%，随机换图消融=32.14%。evidence_table.csv缺失prediction和correct列实际数据，破坏了逐行核对的条件。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 防泄漏设计严谨（image-level split），对count子任务性能瓶颈及语言先验的消融分析深入且诚实，代码结构完整且可离线运行。
- 不足: evidence_table.csv的prediction和correct列为空，破坏了证据链的完整性，导致裁判无法直接基于表格进行结果抽查与重算。