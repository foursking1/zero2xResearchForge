# EVAL REPORT v5: 2103.12057_tsf_experimental_review

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 43.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 4.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 10.0 | 15 | |
| **A 合计** | **28.0** | 60 | A1: 提交了完整的训练与评估代码，但缺失任务明确要求的 evidence_table.csv 和 report.md，核心结果表未落盘，给4分。A2: 报告数值（GRU 17.7, MLP 20.2）支持序列模型优于MLP的方向，但优势幅度（2.5）弱于论文（5.9），且结论为partially_supported，受硬上限约束给14分。A3: 代码逻辑正确实现了防泄漏归一化和固定起点划分，方法sound，但无实际结果验证，给10分。 |
| B 证据真实性/实际复现 | 15.0 | 40 | 磁盘扫描显示 metrics.json 与 evidence_table.csv 均缺失，仅有代码和配置JSON文件，属于部分证据（等级1）。且无真实运行结果落盘，散文数值无法验证，给15分。 |

## A 核心结果达成度（28.0/60 = A1 4.0 + A2 14.0 + A3 10.0）

A1: 提交了完整的训练与评估代码，但缺失任务明确要求的 evidence_table.csv 和 report.md，核心结果表未落盘，给4分。A2: 报告数值（GRU 17.7, MLP 20.2）支持序列模型优于MLP的方向，但优势幅度（2.5）弱于论文（5.9），且结论为partially_supported，受硬上限约束给14分。A3: 代码逻辑正确实现了防泄漏归一化和固定起点划分，方法sound，但无实际结果验证，给10分。

## B 证据真实性/实际复现（15.0/40）

磁盘扫描显示 metrics.json 与 evidence_table.csv 均缺失，仅有代码和配置JSON文件，属于部分证据（等级1）。且无真实运行结果落盘，散文数值无法验证，给15分。

## 证据与重算说明

独立重算未执行。关键实测数值（GRU=17.7, MLP=20.2）仅提取自EVAL_REPORT散文，无对应的evidence_table.csv或metrics.json落盘支撑，属部分证据/空壳声称。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 代码结构完整，正确实现了论文要求的固定起点、防泄漏归一化和MIMO滑窗协议。
- 不足: 严重缺失标准的evidence_table.csv和report.md等落盘证据文件，导致无法验证实际运行结果，仅凭散文声称数值。