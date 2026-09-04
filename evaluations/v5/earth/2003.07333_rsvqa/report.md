# EVAL REPORT v5: 2003.07333_rsvqa

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 54.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 8.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 10.0 | 15 | |
| **A 合计** | **32.0** | 60 | A1(8分)：产出了完整的代码、metrics.json和报告，但evidence_table.csv中prediction和correct列完全为空，核心交付物存在明显缺口。A2(14分)：报告OA=68.10%，与锚值79.08%相对差约13.9%，定性趋势与消融实验匹配，但受限于partially_supported结论的硬上限（A2≤15），给14分。A3(10分)：采用image-level split防泄漏，方法sound，但证据表缺失关键列导致无法直接核对，需重跑代码，存在轻微顾虑。 |
| B 证据真实性/实际复现 | 22.0 | 40 | 磁盘扫描显示metrics.json存在且数值自洽，但evidence_table.csv缺失prediction和correct列的实际数据，属于关键证据缺失，无法直接通过表格重算OA。依据规则落入部分证据区间[11,29]，且受partially_supported硬上限（B≤28）约束，给22分。 |

## A 核心结果达成度（32.0/60 = A1 8.0 + A2 14.0 + A3 10.0）

A1(8分)：产出了完整的代码、metrics.json和报告，但evidence_table.csv中prediction和correct列完全为空，核心交付物存在明显缺口。A2(14分)：报告OA=68.10%，与锚值79.08%相对差约13.9%，定性趋势与消融实验匹配，但受限于partially_supported结论的硬上限（A2≤15），给14分。A3(10分)：采用image-level split防泄漏，方法sound，但证据表缺失关键列导致无法直接核对，需重跑代码，存在轻微顾虑。

## B 证据真实性/实际复现（22.0/40）

磁盘扫描显示metrics.json存在且数值自洽，但evidence_table.csv缺失prediction和correct列的实际数据，属于关键证据缺失，无法直接通过表格重算OA。依据规则落入部分证据区间[11,29]，且受partially_supported硬上限（B≤28）约束，给22分。

## 证据与重算说明

独立重算未执行。关键实测数提取自metrics.json：OA=0.68095，presence=0.879，comparison=0.867，count=0.269，rural_urban=1.0，随机换图消融=0.321。evidence_table.csv缺失prediction和correct列数据，破坏了逐行核对的条件。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 防泄漏设计严谨（image-level split），对count子任务性能瓶颈及语言先验的消融分析深入且诚实，代码结构完整。
- 不足: evidence_table.csv的prediction和correct列为空，破坏了证据链的完整性，导致裁判无法直接基于表格进行结果抽查与重算。