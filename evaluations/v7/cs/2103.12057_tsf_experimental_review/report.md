# EVAL REPORT v7: 2103.12057_tsf_experimental_review

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 34.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 4.0 | 12 | |
| A2 科学结论保真 | 10.0 | 33 | |
| A3 方法严谨与可复现 | 10.0 | 15 | |
| **A 合计** | **24.0** | 60 | A1: 提交了完整的训练与评估代码，但缺失任务明确要求的 evidence_table.csv 和 report.md，核心结果未落盘，给4分。A2: 散文声称的数值（GRU 17.7, MLP 20.2）支持序列模型优于MLP的方向，但无落盘证据支撑，且优势幅度弱于论文，受证据等级硬约束及partially_supported上限（≤15）限制，给10分。A3: 代码逻辑正确实现了防泄漏归一化和固定起点划分，方法sound，但无实际结果验证，给10分。 |
| B 真值一致性/可验证性 | 10.0 | 40 | truth_check=unverified | Agent数（提取自EVAL_REPORT散文）：GRU WAPE=17.7，MLP WAPE=20.2。锚点真值：GRU=15.182，MLP=21.114。比对：GRU 17.7 vs 15.182 → 偏离16.6%；MLP 20.2 vs 21.114 → 偏离4.3%。因缺失 metrics.json 和 evidence_table.csv 等机器可读落盘文件，数值无法独立验证，判定为 unverified，给10分。 |

## A 核心结果达成度（24.0/60 = A1 4.0 + A2 10.0 + A3 10.0）

A1: 提交了完整的训练与评估代码，但缺失任务明确要求的 evidence_table.csv 和 report.md，核心结果未落盘，给4分。A2: 散文声称的数值（GRU 17.7, MLP 20.2）支持序列模型优于MLP的方向，但无落盘证据支撑，且优势幅度弱于论文，受证据等级硬约束及partially_supported上限（≤15）限制，给10分。A3: 代码逻辑正确实现了防泄漏归一化和固定起点划分，方法sound，但无实际结果验证，给10分。

## B 真值一致性/可验证性（10.0/40）[truth_check=unverified]

Agent数（提取自EVAL_REPORT散文）：GRU WAPE=17.7，MLP WAPE=20.2。锚点真值：GRU=15.182，MLP=21.114。比对：GRU 17.7 vs 15.182 → 偏离16.6%；MLP 20.2 vs 21.114 → 偏离4.3%。因缺失 metrics.json 和 evidence_table.csv 等机器可读落盘文件，数值无法独立验证，判定为 unverified，给10分。

## 证据与重算说明

独立重算未执行。关键实测数值（GRU=17.7, MLP=20.2）仅提取自EVAL_REPORT散文，无对应的evidence_table.csv或metrics.json落盘支撑，属空壳/不可验证证据。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `unverified`
- 亮点: 代码结构完整，正确实现了论文要求的固定起点、防泄漏归一化和MIMO滑窗协议。
- 不足: 严重缺失标准的evidence_table.csv和report.md等落盘证据文件，导致无法验证实际运行结果，仅凭散文声称数值。