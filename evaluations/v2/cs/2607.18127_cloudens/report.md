# EVAL REPORT v2: 2607.18127_cloudens

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 91.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 53.0 | 60 | A1: agent报告MD Standard ClouDens 16.84 vs GRU 6.45 (比值2.61)，LowFN 21.76 vs 11.32 (比值1.92)，两profile均>=1.3，落入满分带，得30分。A2: agent报告ClouDens MD Standard 16.84 ∈ [14,28]，LowFN 21.76 ∈ [18,34]，落入满分带，得20分（GRU满足加分项但不超上限）。A3: agent报告MD下TP 14 < GRU 15，FP 39 > GRU 38，仅IM覆盖5 >= 4满足1条，落入满足1条带，得3分。方向性校验无惩罚。A总分53。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘扫描显示evidence_table.csv、grid CSV、data_facts.json等实测证据文件齐全，且内部数值与报告严格一致。agent还提供了batch16的验证运行结果，精确复现了论文GRU基线数值，证明代码逻辑正确且未抄数。证据真实可靠，给38分。 |

## A 核心结果达成度（53.0/60）

A1: agent报告MD Standard ClouDens 16.84 vs GRU 6.45 (比值2.61)，LowFN 21.76 vs 11.32 (比值1.92)，两profile均>=1.3，落入满分带，得30分。A2: agent报告ClouDens MD Standard 16.84 ∈ [14,28]，LowFN 21.76 ∈ [18,34]，落入满分带，得20分（GRU满足加分项但不超上限）。A3: agent报告MD下TP 14 < GRU 15，FP 39 > GRU 38，仅IM覆盖5 >= 4满足1条，落入满足1条带，得3分。方向性校验无惩罚。A总分53。

## B 证据真实性/实际复现（38.0/40）

磁盘扫描显示evidence_table.csv、grid CSV、data_facts.json等实测证据文件齐全，且内部数值与报告严格一致。agent还提供了batch16的验证运行结果，精确复现了论文GRU基线数值，证明代码逻辑正确且未抄数。证据真实可靠，给38分。

## 证据与重算说明

独立重算未执行。抽查关键实测数：data_facts.json确认39365行/2406特征/26488测试点；evidence_table.csv中MD 99.8 ClouDens NAB Standard=16.8437, LowFN=21.7555；validation_batch16中GRU MD NAB Standard=5.8920（与论文锚值5.89绝对差<0.01）。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 代码管线完整且提供了batch16的交叉验证，精确复现了论文GRU基线数值，极大增强了证据可信度；对局限性和batch敏感性的分析非常诚实且深入。
- 不足: 在主运行（batch 32）的MD评分下，ClouDens的逐点TP/FP未能严格优于GRU（14/39 vs 15/38），导致Claim B（检测质量）在MD下仅部分成立。