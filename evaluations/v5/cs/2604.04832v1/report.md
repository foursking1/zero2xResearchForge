# EVAL REPORT v5: 2604.04832v1

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 70.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 15.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **42.0** | 60 | A1: 完整交付了代码、报告、evidence表和metrics.json，核心产物无缺失(12)。A2: C01和C02的效应与数值基本复现，C03准确发现S6/S7并非一致冗余，得出partially_supported的诚实结论；受限于结论硬上限，给至该档满分(15)。A3: 采用GroupKFold防泄漏，特征冻结校验，多种子稳健性，方法严谨sound(15)。 |
| B 证据真实性/实际复现 | 28.0 | 40 | 证据等级为2，提交了详尽的metrics.json、90项指标的evidence_table及多个中间JSON，证据链完整自洽。受限于partially_supported结论的硬上限，B给至最高档28分。 |

## A 核心结果达成度（42.0/60 = A1 12.0 + A2 15.0 + A3 15.0）

A1: 完整交付了代码、报告、evidence表和metrics.json，核心产物无缺失(12)。A2: C01和C02的效应与数值基本复现，C03准确发现S6/S7并非一致冗余，得出partially_supported的诚实结论；受限于结论硬上限，给至该档满分(15)。A3: 采用GroupKFold防泄漏，特征冻结校验，多种子稳健性，方法严谨sound(15)。

## B 证据真实性/实际复现（28.0/40）

证据等级为2，提交了详尽的metrics.json、90项指标的evidence_table及多个中间JSON，证据链完整自洽。受限于partially_supported结论的硬上限，B给至最高档28分。

## 证据与重算说明

独立重算未执行。关键实测数：mlp_mcc_mean_paper_vs_scissors=0.8989，fdr_difficulty_ratio_rock_vs_paper=20.43，ablationA_normShiftFDR_paper_S2=0.8588。所有数值均有对应JSON/CSV落盘支撑。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 方法学极其严谨，防泄漏和特征校验做得很完善；对C03的批判性验证非常诚实，没有为了迎合论文而篡改数据。
- 不足: C01的FDR归一化绝对值与论文存在一定偏差；受限于部分结论未完全支持，总分触及硬上限。