# EVAL REPORT v2: 2406.12747_tsibench

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1: Agent 报告的 Linear 多种子均值为 0.2037，落入满分带 [0.185, 0.215]，且报告了 3 个种子及标准差，evidence_table.csv 与 metrics.json 证据齐全，得 30 分。A2: 每种子排序均严格满足 Linear < LOCF < Median 且 Linear < Mean；LOCF 均值 0.2961 落入 [0.20, 0.42]，Median/Mean 均值落入 [0.55, 1.05]，量级符合；报告中给出了详尽的跨种子稳健性说明，结论标签 supported 与证据一致，得 30 分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示 metrics.json 与 evidence_table.csv 等实测证据文件齐全，且内部数值与报告严格一致。seed=42 掩码点总数 2385 及 Linear test MAE 0.2033249300539183 与冻结协议参考值精确匹配（bit-for-bit）。未发现抄论文数字当实测的行为，深度方法数值均诚实标注为引用。证据真实且可核对，给满分 40 分。 |

## A 核心结果达成度（60/60）

A1: Agent 报告的 Linear 多种子均值为 0.2037，落入满分带 [0.185, 0.215]，且报告了 3 个种子及标准差，evidence_table.csv 与 metrics.json 证据齐全，得 30 分。A2: 每种子排序均严格满足 Linear < LOCF < Median 且 Linear < Mean；LOCF 均值 0.2961 落入 [0.20, 0.42]，Median/Mean 均值落入 [0.55, 1.05]，量级符合；报告中给出了详尽的跨种子稳健性说明，结论标签 supported 与证据一致，得 30 分。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示 metrics.json 与 evidence_table.csv 等实测证据文件齐全，且内部数值与报告严格一致。seed=42 掩码点总数 2385 及 Linear test MAE 0.2033249300539183 与冻结协议参考值精确匹配（bit-for-bit）。未发现抄论文数字当实测的行为，深度方法数值均诚实标注为引用。证据真实且可核对，给满分 40 分。

## 证据与重算说明

独立重算未执行，但基于提交物内部强一致性判定：metrics.json 和 evidence_table.csv 列完整且数值严格对应。关键实测数：seed=42 掩码点 2385，Linear MAE=0.2033249300539183，LOCF MAE=0.3023943111054866，均与 PAPER_ANCHOR 辅助事实完美吻合。

## 结论

- **科学结论**: `supported`
- 亮点: 协议复现极其精确，与冻结参考协议 bit-for-bit 匹配；多种子稳健性分析详实，严格区分实测与论文引用值，证据链完整且高度一致。
- 不足: 无明显弱点，提交物堪称 L1 层级科研复现的标杆范例。