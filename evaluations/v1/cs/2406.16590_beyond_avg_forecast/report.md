# EVAL REPORT: 2406.16590_beyond_avg_forecast

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判（qwen3.7-max）
- 评测时间: 2026-08-19

## 总分: 77.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 37.0 | 60 | A1(15分)：agent 正确读取了给定的 6 个 .tsf 文件（M3 月/季/年合计 2829 条，Tourism 1311 条，总计 4140 条），严格按 `@horizon` 留测，SMAPE 口径正确，无泄漏，得 15 分。A2(22分)：agent 独立复现了 F2（末步 NHITS 占优，首步接近）和 F5（胜率落入 30-70% 区间），部分复现 F3（频率视角表现异质），但未复现 F1（Overall ETS 优于 NHITS）、F4（异常点未被经典超越）和 F6（困难问题优势未缩小）。符合 rubric 中“复现 2-3 个发现”的半满带，得 22 分。A 维度总计 37 分。 |
| B 证据真实性 | 25 | 25 | 提交物齐全，包含完整的代码结构、evidence_table.csv、metrics.json 和 report.md。报告严格区分了论文数值（含 M4）与实测数值（仅 M3+Tourism），内部表格与 JSON 数值高度一致，无抄数嫌疑，证据真实性满分。 |
| C 方法与报告 | 15 | 15 | C1(5分)：深度全局模型（N-HiTS）与 6 种经典局部方法配置清晰，多视角评估定义明确可操作。C2(6分)：严格防泄漏，测试段仅用于评分，困难/异常条件定义基于 SNaive 训练期残差，无泄漏，固定种子。C3(4分)：结论标签 `partially_supported` 与实测证据完美匹配，并在 Limitations 中深刻讨论了缺失 M4 数据对 F1/F4 方向反转的合理归因。 |

## A 核心结果达成度（37.0/60）

A1(15分)：agent 正确读取了给定的 6 个 .tsf 文件（M3 月/季/年合计 2829 条，Tourism 1311 条，总计 4140 条），严格按 `@horizon` 留测，SMAPE 口径正确，无泄漏，得 15 分。A2(22分)：agent 独立复现了 F2（末步 NHITS 占优，首步接近）和 F5（胜率落入 30-70% 区间），部分复现 F3（频率视角表现异质），但未复现 F1（Overall ETS 优于 NHITS）、F4（异常点未被经典超越）和 F6（困难问题优势未缩小）。符合 rubric 中“复现 2-3 个发现”的半满带，得 22 分。A 维度总计 37 分。

## B 证据真实性（25/25）

提交物齐全，包含完整的代码结构、evidence_table.csv、metrics.json 和 report.md。报告严格区分了论文数值（含 M4）与实测数值（仅 M3+Tourism），内部表格与 JSON 数值高度一致，无抄数嫌疑，证据真实性满分。

## C 方法与报告（15/15）

C1(5分)：深度全局模型（N-HiTS）与 6 种经典局部方法配置清晰，多视角评估定义明确可操作。C2(6分)：严格防泄漏，测试段仅用于评分，困难/异常条件定义基于 SNaive 训练期残差，无泄漏，固定种子。C3(4分)：结论标签 `partially_supported` 与实测证据完美匹配，并在 Limitations 中深刻讨论了缺失 M4 数据对 F1/F4 方向反转的合理归因。

## 证据与重算说明

独立重算未执行。抽查关键实测数值：总序列数 4140（M3 2829 + Tourism 1311）；Overall SMAPE（ETS 16.99，NHITS 17.34）；Horizon first_step（ETS 12.48，NHITS 13.26），last_step（NHITS 21.54）；Win-rate NHITS vs ETS 0.432。所有数值在 report.md、evidence_table.csv 和 metrics.json 中完全一致。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 实验设计严谨，多视角评估协议实现完整；对未复现的论文发现（如 F1、F4）能结合数据子集差异（无 M4、Tourism 强季节性）给出极具说服力的科学归因，展现了极强的科研分析能力。
- 不足: 受限于冻结数据包（无 M4）和轻量级 N-HiTS 配置，未能复现论文中深度模型在 Overall 和异常点上的绝对优势，导致核心发现方向一致性（A2）得分受限。