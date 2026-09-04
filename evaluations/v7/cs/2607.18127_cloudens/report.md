# EVAL REPORT v7: 2607.18127_cloudens

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 62.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 13.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **40.0** | 60 | A1(12分)：核心交付物完整，提供了evidence_table.csv、grid CSV、data_facts.json等机器可读结果文件，覆盖所有必需输出。A2(13分)：结论为partially_supported（受硬上限A2≤15限制）。Agent报告的MD ClouDens NAB（Standard 16.84, LowFN 21.76）落在合理容差带内，方向正确（比值>1.3），但与论文真值（20.94/26.24）偏离约17-20%，且MD下TP/FP未严格优于GRU，故给13分。A3(15分)：方法严谨，防泄漏措施完备，且通过batch16交叉验证精确复现了GRU基线锚值，证明管线sound且可复算。 |
| B 真值一致性/可验证性 | 22.0 | 40 | truth_check=diverged | truth_check=diverged。逐条比对：1) MD ClouDens NAB Standard: agent 16.84 vs 锚点 20.94 → 偏离(-19.6%)；2) MD ClouDens NAB LowFN: agent 21.76 vs 锚点 26.24 → 偏离(-17.1%)；3) MD GRU NAB Standard: agent 6.45 vs 锚点 5.89 → 接近；4) LF GRU NAB Standard: agent 6.58 vs 锚点 6.58 → 完全吻合；5) Validation batch16 GRU MD NAB Standard: agent 5.89 vs 锚点 5.89 → 完全吻合；6) MD ClouDens TP/FP: agent 14/39 vs 锚点 16/37 → 偏离。核心指标存在10-20%的偏离，但agent提供的batch16验证运行完美复现GRU锚值，证明了代码管线的真实性与未抄数，故在diverged区间(10-25)给22分。 |

## A 核心结果达成度（40.0/60 = A1 12.0 + A2 13.0 + A3 15.0）

A1(12分)：核心交付物完整，提供了evidence_table.csv、grid CSV、data_facts.json等机器可读结果文件，覆盖所有必需输出。A2(13分)：结论为partially_supported（受硬上限A2≤15限制）。Agent报告的MD ClouDens NAB（Standard 16.84, LowFN 21.76）落在合理容差带内，方向正确（比值>1.3），但与论文真值（20.94/26.24）偏离约17-20%，且MD下TP/FP未严格优于GRU，故给13分。A3(15分)：方法严谨，防泄漏措施完备，且通过batch16交叉验证精确复现了GRU基线锚值，证明管线sound且可复算。

## B 真值一致性/可验证性（22.0/40）[truth_check=diverged]

truth_check=diverged。逐条比对：1) MD ClouDens NAB Standard: agent 16.84 vs 锚点 20.94 → 偏离(-19.6%)；2) MD ClouDens NAB LowFN: agent 21.76 vs 锚点 26.24 → 偏离(-17.1%)；3) MD GRU NAB Standard: agent 6.45 vs 锚点 5.89 → 接近；4) LF GRU NAB Standard: agent 6.58 vs 锚点 6.58 → 完全吻合；5) Validation batch16 GRU MD NAB Standard: agent 5.89 vs 锚点 5.89 → 完全吻合；6) MD ClouDens TP/FP: agent 14/39 vs 锚点 16/37 → 偏离。核心指标存在10-20%的偏离，但agent提供的batch16验证运行完美复现GRU锚值，证明了代码管线的真实性与未抄数，故在diverged区间(10-25)给22分。

## 证据与重算说明

独立重算未执行。关键实测数提取自results/evidence_table.csv与results/validation_batch16/grid_GRU.csv：MD 99.8 ClouDens NAB Standard=16.8437, LowFN=21.7555；MD 99.8 GRU NAB Standard=6.4487；batch16验证GRU NAB Standard=5.8920。data_facts.json确认39365行/2406特征/26488测试点。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 代码管线完整且极其诚实，提供了batch16的交叉验证精确复现论文GRU基线数值，形成了极强的证据链；对局限性和batch敏感性的分析非常深入。
- 不足: 主运行（batch 32）下ClouDens的MD NAB数值与论文真值偏离接近20%，且逐点TP/FP未能严格优于GRU基线，导致检测质量claim仅部分成立。