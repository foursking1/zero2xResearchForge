# EVAL REPORT v3: 2003.07333_rsvqa

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 62.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 42.0 | 60 | 锚值OA=79.08%，Agent报告并落盘metrics.json的OA=68.10%（0.68095），相对偏差d=13.88%。根据梯度化规则，偏差10%-20%对应A=42分。Agent完成了问题类型分解和消融实验，但核心指标偏差明显，严格限制在该梯度区间。 |
| B 证据真实性/实际复现 | 20.0 | 40 | 磁盘扫描显示metrics.json存在且数值自洽，但evidence_table.csv中的prediction和correct列完全为空，属于关键证据缺失，导致裁判无法逐行核对和重算OA。依据规则落入部分证据区间[11,29]，给20分。 |

## A 核心结果达成度（42.0/60）

锚值OA=79.08%，Agent报告并落盘metrics.json的OA=68.10%（0.68095），相对偏差d=13.88%。根据梯度化规则，偏差10%-20%对应A=42分。Agent完成了问题类型分解和消融实验，但核心指标偏差明显，严格限制在该梯度区间。

## B 证据真实性/实际复现（20.0/40）

磁盘扫描显示metrics.json存在且数值自洽，但evidence_table.csv中的prediction和correct列完全为空，属于关键证据缺失，导致裁判无法逐行核对和重算OA。依据规则落入部分证据区间[11,29]，给20分。

## 证据与重算说明

独立重算未执行。关键实测数提取自metrics.json：OA=0.68095，presence=0.879，comparison=0.867，count=0.269，rural_urban=1.0，随机换图消融=0.321。evidence_table.csv缺失prediction和correct列实际数据。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 防泄漏设计严谨（image-level split），对count子任务性能瓶颈及语言先验的消融分析深入且诚实，代码结构完整。
- 不足: evidence_table.csv的prediction和correct列为空，破坏了证据链的完整性，导致无法直接基于表格进行结果抽查与重算。