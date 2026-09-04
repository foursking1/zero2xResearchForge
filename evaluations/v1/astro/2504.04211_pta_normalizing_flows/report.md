# EVAL REPORT: 2504.04211_pta_normalizing_flows

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判（qwen3.7-max）
- 评测时间: 2026-08-19

## 总分: 33.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 0 | 60 | agent 报告重加权 Hellinger 均值 = 0.611；rubric band 表：[≤0.45→60分]，[0.45-0.6→30分]，[>0.6→0分]；0.611 严格落入 >0.6 区间，触发零分条件。虽然 BF 排序一致且做了 NF vs MCMC 对照，但根据数值带匹配铁律，必须应用唯一满足的 >0.6 区间规则，故 A 得 0 分。 |
| B 证据真实性 | 20.0 | 25 | 提交物齐全（代码、evidence_table、metrics、report），明确区分论文值与实测值，无抄袭。但 NF 训练规模缩减 40 倍且 Hellinger 仅在 2 维边缘分布计算（非论文 22 维），证据可靠性受限。独立重算未执行。 |
| C 方法与报告 | 13.0 | 15 | 方法基本合理，对 IS 替代 HME 的解释清晰；明确报告了 ToA 版本差异、计算资源缩减等边界条件；结论标签 partially_supported 准确。未发现测试段泄漏。 |

## A 核心结果达成度（0/60）

agent 报告重加权 Hellinger 均值 = 0.611；rubric band 表：[≤0.45→60分]，[0.45-0.6→30分]，[>0.6→0分]；0.611 严格落入 >0.6 区间，触发零分条件。虽然 BF 排序一致且做了 NF vs MCMC 对照，但根据数值带匹配铁律，必须应用唯一满足的 >0.6 区间规则，故 A 得 0 分。

## B 证据真实性（20.0/25）

提交物齐全（代码、evidence_table、metrics、report），明确区分论文值与实测值，无抄袭。但 NF 训练规模缩减 40 倍且 Hellinger 仅在 2 维边缘分布计算（非论文 22 维），证据可靠性受限。独立重算未执行。

## C 方法与报告（13.0/15）

方法基本合理，对 IS 替代 HME 的解释清晰；明确报告了 ToA 版本差异、计算资源缩减等边界条件；结论标签 partially_supported 准确。未发现测试段泄漏。

## 证据与重算说明

独立重算未执行。关键实测数值：重加权 Hellinger 均值 0.611（PowerLaw 0.518, SMBHB 0.324, DW 0.989）；ln BF 差异（SMBHB/PL 0.998, DW/PL 6.698）；NF 总时间 323-328秒/模型。数值在 report、metrics.json 和 evidence_table.csv 中内部一致。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 诚实报告了计算资源受限导致的性能下降，未伪造数据；BF 排序与 MCMC 完全一致；对数据版本差异（ToA 数量）的核查非常细致。
- 不足: Hellinger 距离计算降维至 2 维且 NF 训练严重不足，导致核心指标未能落入半满分区间；MCMC 链长不足（autocorrelation tau 警告）影响参考证据的严谨性。