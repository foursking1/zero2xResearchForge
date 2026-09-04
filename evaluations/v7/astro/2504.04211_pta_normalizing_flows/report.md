# EVAL REPORT v7: 2504.04211_pta_normalizing_flows

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 37.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 5.0 | 33 | |
| A3 方法严谨与可复现 | 5.0 | 15 | |
| **A 合计** | **22.0** | 60 | A1(12): 核心交付物完整，包含机器可读的 metrics.json 和 evidence_table.csv，符合任务要求。A2(5): 结论为 partially_supported，受硬上限约束(A2≤15)。核心指标重加权 Hellinger 均值 0.611 远超论文真值 0.2611，且落入 rubric 零分带(>0.6)；BF 仅 1/3 模型对满足 |Δln BF|≤1，定量复现失败，仅保留方向正确的部分支持，给 5 分。A3(5): 存在明显方法论顾虑，Hellinger 降维至 2 维(非论文 22 维)，NF 训练缩减 40 倍导致证据估计崩溃，MCMC 链长不足触发 autocorr 警告，评估严谨性受损，给 5 分。 |
| B 真值一致性/可验证性 | 15.0 | 40 | truth_check=diverged | agent数 vs 锚点真值比对：1) 重加权 Hellinger 均值：agent 0.6105 vs 锚点 0.2611 → 严重偏离；2) 逐模型 Hellinger (Reweighted)：agent PL 0.518 / SMBHB 0.324 / DW 0.989 vs 锚点 PL 0.3911 / SMBHB 0.4216 / DW 0.1729 → 均偏离，DW 甚至因 IS 塌缩达到 0.989；3) BF 一致性：agent 仅 1/3 模型对 |Δln BF| ≤ 1 (SMBHB/PL 0.998) vs 锚点要求多数模型对在不确定度内一致 → 偏离。因核心定量指标全面偏离论文真值，truth_check 判定为 diverged，且受 partially_supported 结论硬上限约束(B≤28)，综合给 15 分。 |

## A 核心结果达成度（22.0/60 = A1 12.0 + A2 5.0 + A3 5.0）

A1(12): 核心交付物完整，包含机器可读的 metrics.json 和 evidence_table.csv，符合任务要求。A2(5): 结论为 partially_supported，受硬上限约束(A2≤15)。核心指标重加权 Hellinger 均值 0.611 远超论文真值 0.2611，且落入 rubric 零分带(>0.6)；BF 仅 1/3 模型对满足 |Δln BF|≤1，定量复现失败，仅保留方向正确的部分支持，给 5 分。A3(5): 存在明显方法论顾虑，Hellinger 降维至 2 维(非论文 22 维)，NF 训练缩减 40 倍导致证据估计崩溃，MCMC 链长不足触发 autocorr 警告，评估严谨性受损，给 5 分。

## B 真值一致性/可验证性（15.0/40）[truth_check=diverged]

agent数 vs 锚点真值比对：1) 重加权 Hellinger 均值：agent 0.6105 vs 锚点 0.2611 → 严重偏离；2) 逐模型 Hellinger (Reweighted)：agent PL 0.518 / SMBHB 0.324 / DW 0.989 vs 锚点 PL 0.3911 / SMBHB 0.4216 / DW 0.1729 → 均偏离，DW 甚至因 IS 塌缩达到 0.989；3) BF 一致性：agent 仅 1/3 模型对 |Δln BF| ≤ 1 (SMBHB/PL 0.998) vs 锚点要求多数模型对在不确定度内一致 → 偏离。因核心定量指标全面偏离论文真值，truth_check 判定为 diverged，且受 partially_supported 结论硬上限约束(B≤28)，综合给 15 分。

## 证据与重算说明

独立重算未执行。关键实测数来自 results/metrics.json 与 evidence_table.csv，内部一致：重加权 Hellinger 均值 0.6105，直接 Hellinger 均值 0.7947；logZ MCMC(HME) 约 69000，logZ NF(IS) 约 68970；BF 排序一致但量级差异大。数据侧核实 10 颗脉冲星 4944 个活动 ToA。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 诚实报告了计算资源受限导致的 NF 欠训练与 IS 塌缩，未伪造数据或用论文数字冒充实测；证据文件结构完整，数值追溯性好，BF 模型排序与 MCMC 完全一致。
- 不足: 核心指标 Hellinger 距离因降维和欠训练未能复现论文声称的对齐效应；MCMC 参考链长不足且使用截断调和均值，影响证据估计的严谨性。