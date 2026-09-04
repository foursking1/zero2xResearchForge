# EVAL REPORT v7: 2211.03400_fermi_4fgl_jetted_agn

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 70.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 15.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **42.0** | 60 | A1：核心交付物完整，包含 metrics.json、evidence_table.csv 等机器可读结果，给 12 分。A2：Agent 完美复现了冻结数据的各项锚值，并对占比差异进行了深刻的归因与敏感度分析，科学上实质支持了论文趋势。但由于 Agent 最终给出的结论标签为 partially_supported，触发系统级结论硬上限规则，A2 最高不得超过 15 分，故给 15 分。A3：方法严谨，采用 ReadMe 字节级定宽解析，大小写敏感处理正确，提供独立校验脚本，无数据泄漏，完全可复现，给 15 分。 |
| B 真值一致性/可验证性 | 28.0 | 40 | truth_check=matched | Agent 数 5065 vs 锚点 5065 (Records) → 吻合；Agent 数 1336 vs 锚点 1336 (全空天无对应体) → 吻合；Agent 数 2866 vs 锚点 2866 (重建样本) → 吻合；Agent 数 1067 vs 锚点 1067 (BLL) → 吻合；Agent 数 658 vs 锚点 658 (FSRQ) → 吻合；Agent 数 1074 vs 锚点 1074 (|b|>10° bcu) → 吻合。真值比对完全 matched，原本应给 35-40 分，但受 partially_supported 结论的硬上限约束（B≤28），故给 28 分。 |

## A 核心结果达成度（42.0/60 = A1 12.0 + A2 15.0 + A3 15.0）

A1：核心交付物完整，包含 metrics.json、evidence_table.csv 等机器可读结果，给 12 分。A2：Agent 完美复现了冻结数据的各项锚值，并对占比差异进行了深刻的归因与敏感度分析，科学上实质支持了论文趋势。但由于 Agent 最终给出的结论标签为 partially_supported，触发系统级结论硬上限规则，A2 最高不得超过 15 分，故给 15 分。A3：方法严谨，采用 ReadMe 字节级定宽解析，大小写敏感处理正确，提供独立校验脚本，无数据泄漏，完全可复现，给 15 分。

## B 真值一致性/可验证性（28.0/40）[truth_check=matched]

Agent 数 5065 vs 锚点 5065 (Records) → 吻合；Agent 数 1336 vs 锚点 1336 (全空天无对应体) → 吻合；Agent 数 2866 vs 锚点 2866 (重建样本) → 吻合；Agent 数 1067 vs 锚点 1067 (BLL) → 吻合；Agent 数 658 vs 锚点 658 (FSRQ) → 吻合；Agent 数 1074 vs 锚点 1074 (|b|>10° bcu) → 吻合。真值比对完全 matched，原本应给 35-40 分，但受 partially_supported 结论的硬上限约束（B≤28），故给 28 分。

## 证据与重算说明

独立重算未执行。落盘证据包含 verify_checks.json（all_passed=true），关键实测数（总行数5065、全空天CLASS1空1336、|b|>10°无对应体657、bcu合计1074、重建样本2866）在多个CSV与JSON中相互自洽，并与编译器探针完全吻合。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `matched`
- 亮点: 定宽解析极其严谨，完美处理了VizieR文件的字节对齐与大小写语义；对版本差异与重分类缺失的归因深刻，多口径敏感度分析透彻，证据链完备且高度自洽。
- 不足: Agent 在完美复现冻结数据预期值并合理解释偏差的情况下，保守地选择了 partially_supported 标签，导致触发了评分系统的结论级硬上限，未能突破 70 分天花板。