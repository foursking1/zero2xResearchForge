# EVAL REPORT v3: 2607.18127_cloudens

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 80.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 42.0 | 60 | 实测数值：ClouDens MD Standard=16.84，LowFN=21.76；GRU MD Standard=6.45，LowFN=11.32。论文锚值：ClouDens Standard=20.94，LowFN=26.24。偏差计算：Standard偏差19.58%，LowFN偏差17.07%，两者均严格落入10%-20%偏差区间。依据梯度化铁律，A得42分。此外，检测质量方面TP(14<15)与FP(39>38)未严格优于GRU，仅IM覆盖达标，进一步印证部分核心子项未完美达成。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 证据等级2（齐全自洽）。虽缺失标准的metrics.json，但提供了meta_*.json、data_facts.json及完整的evidence_table和grid CSV作为替代。特别是提供了batch16的验证运行，精确复现了论文GRU基线锚值（5.89），形成了极强的交叉校验证据链，内部数值严格自洽，给38分。 |

## A 核心结果达成度（42.0/60）

实测数值：ClouDens MD Standard=16.84，LowFN=21.76；GRU MD Standard=6.45，LowFN=11.32。论文锚值：ClouDens Standard=20.94，LowFN=26.24。偏差计算：Standard偏差19.58%，LowFN偏差17.07%，两者均严格落入10%-20%偏差区间。依据梯度化铁律，A得42分。此外，检测质量方面TP(14<15)与FP(39>38)未严格优于GRU，仅IM覆盖达标，进一步印证部分核心子项未完美达成。

## B 证据真实性/实际复现（38.0/40）

证据等级2（齐全自洽）。虽缺失标准的metrics.json，但提供了meta_*.json、data_facts.json及完整的evidence_table和grid CSV作为替代。特别是提供了batch16的验证运行，精确复现了论文GRU基线锚值（5.89），形成了极强的交叉校验证据链，内部数值严格自洽，给38分。

## 证据与重算说明

独立重算未执行。关键实测数：data_facts确认39365行/2406特征/26488测试点；evidence_table中MD 99.8 ClouDens NAB Standard=16.8437, LowFN=21.7555；validation_batch16中GRU MD NAB Standard=5.8920（与论文锚值5.89绝对差<0.01）。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 代码管线完整且提供了batch16的交叉验证，精确复现了论文GRU基线数值，极大增强了证据可信度；对局限性和batch敏感性的分析非常诚实且深入。
- 不足: 主运行下ClouDens的NAB数值偏差接近20%，且逐点TP/FP未能严格优于GRU基线，导致检测质量claim仅部分成立。