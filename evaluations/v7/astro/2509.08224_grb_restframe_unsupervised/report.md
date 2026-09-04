# EVAL REPORT v7: 2509.08224_grb_restframe_unsupervised

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 100.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 33.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **60.0** | 60 | A1：核心交付物完整，包含metrics.json和evidence_table.csv等机器可读文件，得12分。A2：实测数值与PAPER_ANCHOR探针真值完美吻合，Type I占比14.06%与论文一致，两族中位数显著分离，结论supported，得33分。A3：定宽解析逻辑严密，提供独立校验脚本，方法sound且完全可复现，得15分。 |
| B 真值一致性/可验证性 | 40 | 40 | truth_check=matched | agent数 vs 锚点逐条比对：总行数 320 vs 320（吻合）；Type I计数 45 vs 45（吻合）；Type I T90z中位数 0.27 vs 0.27（吻合）；Type I Epz中位数 706.0 vs 706（吻合）；Type II T90z中位数 14.5 vs 14.50（吻合）；T90z<2s数量 64 vs 64（吻合）；特定事件060614A=I+EE vs I+EE（吻合）。全部关键指标完美匹配锚点真值，truth_check=matched。 |

## A 核心结果达成度（60.0/60 = A1 12.0 + A2 33.0 + A3 15.0）

A1：核心交付物完整，包含metrics.json和evidence_table.csv等机器可读文件，得12分。A2：实测数值与PAPER_ANCHOR探针真值完美吻合，Type I占比14.06%与论文一致，两族中位数显著分离，结论supported，得33分。A3：定宽解析逻辑严密，提供独立校验脚本，方法sound且完全可复现，得15分。

## B 真值一致性/可验证性（40/40）[truth_check=matched]

agent数 vs 锚点逐条比对：总行数 320 vs 320（吻合）；Type I计数 45 vs 45（吻合）；Type I T90z中位数 0.27 vs 0.27（吻合）；Type I Epz中位数 706.0 vs 706（吻合）；Type II T90z中位数 14.5 vs 14.50（吻合）；T90z<2s数量 64 vs 64（吻合）；特定事件060614A=I+EE vs I+EE（吻合）。全部关键指标完美匹配锚点真值，truth_check=matched。

## 证据与重算说明

独立重算未执行（基于提交物静态核查与磁盘扫描）。关键实测数（总行数320、Type I计数45、T90z中位数0.27、Epz中位数706等）在metrics.json和evidence_table.csv中完整落盘，且与报告散文及PAPER_ANCHOR探针真值严格一致，证据链完整自洽，无抄数嫌疑。

## 结论

- **科学结论**: `supported`
- **可验证性**: `matched`
- 亮点: 数据解析严谨，完美覆盖所有核心指标与边界条件；对论文样本与冻结目录的差异归因深入且诚实。
- 不足: 无明显弱点，提交物规范且详实。