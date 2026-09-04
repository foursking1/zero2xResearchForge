# EVAL REPORT: 2607.18127_cloudens

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判（qwen3.7-max）
- 评测时间: 2026-08-20

## 总分: 93.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 53.0 | 60 | A1: agent 报告 MD Standard ClouDens 16.84 vs GRU 6.45 (比值 2.61)，LowFN 21.76 vs 11.32 (比值 1.92)，两 profile 均 >=1.3，落入满分带→30分。A2: agent 报告 ClouDens MD Standard 16.84 ∈ [14,28]，LowFN 21.76 ∈ [18,34]，落入满分带→20分（GRU 满足加分项但不超上限）。A3: agent 报告 MD 下 TP 14 < GRU 15，FP 39 > GRU 38，仅 IM 覆盖 5 >= 4 满足 1 条，落入满足1条带→3分。方向性校验无惩罚。 |
| B 证据真实性 | 25 | 25 | 提交物齐全（代码、evidence_table、report、data_facts）。数据事实抽查：parquet 39365行、5xx特征 2406个、异常窗 25个，均与锚值严格一致。agent 提供了 batch16 的验证运行，精确复现了论文 GRU MD NAB 5.89/10.95，证明代码逻辑正确且未抄数。主运行 batch32 的数值差异属合理实现/随机性差异。 |
| C 方法与报告 | 15 | 15 | C1(5分): 协议严格遵循论文（训练/测试划分、剔除异常窗、zero插补、min-max仅训练段、w=6、图构建权重合理）。C2(6分): 防泄漏措施完备，标签仅用于评估，无测试段泄漏。C3(4分): 结论标签与证据匹配，诚实报告了 MD 下 TP/FP 未严格优于 GRU 的局限性以及 batch 敏感性。 |

## A 核心结果达成度（53.0/60）

A1: agent 报告 MD Standard ClouDens 16.84 vs GRU 6.45 (比值 2.61)，LowFN 21.76 vs 11.32 (比值 1.92)，两 profile 均 >=1.3，落入满分带→30分。A2: agent 报告 ClouDens MD Standard 16.84 ∈ [14,28]，LowFN 21.76 ∈ [18,34]，落入满分带→20分（GRU 满足加分项但不超上限）。A3: agent 报告 MD 下 TP 14 < GRU 15，FP 39 > GRU 38，仅 IM 覆盖 5 >= 4 满足 1 条，落入满足1条带→3分。方向性校验无惩罚。

## B 证据真实性（25/25）

提交物齐全（代码、evidence_table、report、data_facts）。数据事实抽查：parquet 39365行、5xx特征 2406个、异常窗 25个，均与锚值严格一致。agent 提供了 batch16 的验证运行，精确复现了论文 GRU MD NAB 5.89/10.95，证明代码逻辑正确且未抄数。主运行 batch32 的数值差异属合理实现/随机性差异。

## C 方法与报告（15/15）

C1(5分): 协议严格遵循论文（训练/测试划分、剔除异常窗、zero插补、min-max仅训练段、w=6、图构建权重合理）。C2(6分): 防泄漏措施完备，标签仅用于评估，无测试段泄漏。C3(4分): 结论标签与证据匹配，诚实报告了 MD 下 TP/FP 未严格优于 GRU 的局限性以及 batch 敏感性。

## 证据与重算说明

独立重算未执行。抽查关键实测数：data_facts.json 确认 39365行/2406特征/26488测试点；evidence_table.csv 中 MD 99.8 ClouDens NAB Standard=16.8437, LowFN=21.7555；validation_batch16 中 GRU MD NAB Standard=5.8920（与论文锚值 5.89 绝对差 <0.01，验证了管线真实性）。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 代码管线完整且提供了 batch16 的交叉验证，精确复现了论文 GRU 基线数值，极大增强了证据可信度；对局限性和 batch 敏感性的分析非常诚实且深入。
- 不足: 在主运行（batch 32）的 MD 评分下，ClouDens 的逐点 TP/FP 未能严格优于 GRU（14/39 vs 15/38），导致 Claim B（检测质量）在 MD 下仅部分成立。