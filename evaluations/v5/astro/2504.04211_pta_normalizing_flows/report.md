# EVAL REPORT v5: 2504.04211_pta_normalizing_flows

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 55.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 10.0 | 33 | |
| A3 方法严谨与可复现 | 5.0 | 15 | |
| **A 合计** | **27.0** | 60 | A1(12): 核心交付物（代码、evidence_table、metrics.json、报告等）完整产出，符合任务要求。A2(10): 结论为partially_supported，受硬上限约束(A2≤15)。BF排序一致且NF加速方向正确，但核心指标Hellinger均值0.611远超论文0.2611，且IS塌缩，定量上部分不支持，给10分。A3(5): 存在明显方法论顾虑：Hellinger降维至2维、NF训练缩减40倍导致证据估计崩溃、MCMC链长不足触发autocorr警告，评估严谨性受损。 |
| B 证据真实性/实际复现 | 28.0 | 40 | 磁盘证据等级为2（齐全自洽），metrics.json与evidence_table.csv数值严格一致，无抄袭。但受partially_supported结论硬上限约束（B≤28），故给28分。 |

## A 核心结果达成度（27.0/60 = A1 12.0 + A2 10.0 + A3 5.0）

A1(12): 核心交付物（代码、evidence_table、metrics.json、报告等）完整产出，符合任务要求。A2(10): 结论为partially_supported，受硬上限约束(A2≤15)。BF排序一致且NF加速方向正确，但核心指标Hellinger均值0.611远超论文0.2611，且IS塌缩，定量上部分不支持，给10分。A3(5): 存在明显方法论顾虑：Hellinger降维至2维、NF训练缩减40倍导致证据估计崩溃、MCMC链长不足触发autocorr警告，评估严谨性受损。

## B 证据真实性/实际复现（28.0/40）

磁盘证据等级为2（齐全自洽），metrics.json与evidence_table.csv数值严格一致，无抄袭。但受partially_supported结论硬上限约束（B≤28），故给28分。

## 证据与重算说明

独立重算未执行。关键实测数（来自metrics.json与evidence_table.csv）：重加权Hellinger均值0.6105（PowerLaw 0.518, SMBHB 0.324, DW 0.989）；logZ MCMC(HME)约69000，logZ NF(IS)约68970；BF排序一致；NF每模型耗时约285-328秒。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 诚实报告了计算资源受限导致的NF欠训练与IS塌缩，未伪造数据；证据文件结构完整，数值追溯性好。
- 不足: 核心指标Hellinger距离因降维和欠训练未能复现论文声称的对齐效应；MCMC参考链长不足且使用截断调和均值，影响证据估计的严谨性。