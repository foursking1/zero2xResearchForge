# EVAL REPORT v7: 2604.04832v1

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 64.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 15.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **42.0** | 60 | A1: 完整交付了代码、metrics.json、evidence_table等核心产物，机器可读结果完整(12)。A2: C01绝对值偏离但相对趋势对，C02数值吻合，C03诚实指出论文部分结论不成立，总体判定partially_supported；受结论硬上限限制，A2给至该档上限15。A3: 采用GroupKFold防泄漏，特征冻结校验，多种子稳健性测试，方法严谨sound(15)。 |
| B 真值一致性/可验证性 | 22.0 | 40 | truth_check=diverged | 真值比对：R01(FDR p-vs-s) agent 0.0349 vs 锚点 0.073 → 偏离(误差0.038>容差0.02)；R02(FDR r-vs-p) agent 0.712 vs 锚点 0.842 → 偏离(误差0.13>容差0.02)；R03(FDR r-vs-s) agent 1.0 vs 锚点 1.0 → 吻合；R05(MCC p-vs-s) agent 0.899 vs 锚点 0.872 → 吻合(误差0.027<容差0.05)；R06(MCC r-vs-p) agent 0.993 vs 锚点 0.99 → 吻合；R07(MCC r-vs-s) agent 0.997 vs 锚点 1.0 → 吻合。因C01的FDR归一化绝对值超出容差带，truth_check判定为diverged，B给22分。 |

## A 核心结果达成度（42.0/60 = A1 12.0 + A2 15.0 + A3 15.0）

A1: 完整交付了代码、metrics.json、evidence_table等核心产物，机器可读结果完整(12)。A2: C01绝对值偏离但相对趋势对，C02数值吻合，C03诚实指出论文部分结论不成立，总体判定partially_supported；受结论硬上限限制，A2给至该档上限15。A3: 采用GroupKFold防泄漏，特征冻结校验，多种子稳健性测试，方法严谨sound(15)。

## B 真值一致性/可验证性（22.0/40）[truth_check=diverged]

真值比对：R01(FDR p-vs-s) agent 0.0349 vs 锚点 0.073 → 偏离(误差0.038>容差0.02)；R02(FDR r-vs-p) agent 0.712 vs 锚点 0.842 → 偏离(误差0.13>容差0.02)；R03(FDR r-vs-s) agent 1.0 vs 锚点 1.0 → 吻合；R05(MCC p-vs-s) agent 0.899 vs 锚点 0.872 → 吻合(误差0.027<容差0.05)；R06(MCC r-vs-p) agent 0.993 vs 锚点 0.99 → 吻合；R07(MCC r-vs-s) agent 0.997 vs 锚点 1.0 → 吻合。因C01的FDR归一化绝对值超出容差带，truth_check判定为diverged，B给22分。

## 证据与重算说明

独立重算未执行。关键实测数均有落盘支撑：mlp_mcc_mean_paper_vs_scissors=0.8989，fdr_norm_divide_max_paper_vs_scissors=0.0349，ablationA_normShiftFDR_paper_S2=0.8588。证据链完整，但未提供claim.md真值对照文件。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 方法学极其严谨，防泄漏和特征校验完善；对C03的批判性验证非常诚实，没有为了迎合论文而篡改数据，准确发现了S6/S7并非一致冗余。
- 不足: C01的FDR归一化绝对值与论文真值存在明显偏差（0.035 vs 0.073），未能完全复现论文的具体数值，仅复现了相对难度趋势。