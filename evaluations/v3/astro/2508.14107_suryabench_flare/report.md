# EVAL REPORT v3: 2508.14107_suryabench_flare

- 执行 agent: Claude Code (deepseek-chat, 经 DeepSeek Anthropic 兼容网关)
- 评测裁判: SciSolveBench LLM 裁判 v3（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 70.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 30.0 | 60 | Agent 报告的 test 期 TSS 为 0.5674。对照 SCORE_RUBRIC 数值带：满分带 [0.20, 0.42] 不满足；半满带 (0.42, 0.70] 满足；零分带 <0.10 或 >0.70 不满足。0.5674 明确落入半满带，且同步报告了 HSS、base-rate 漂移分析及阈值敏感性，证据落盘，故按 rubric 授予半满带固定分 30 分。因冻结数据无影像，GOES 历史 persistence 技能与论文 SDO 影像基线不同源，无法落入满分带。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示证据等级为 2（齐全自洽）。metrics.json 与 evidence_table.csv 均存在且列完整。关键抽查数 test 期 base_rate=0.2943 (n=43848) 与冻结锚值一致；TSS=0.5674 可由证据表 TP=11880, FP=10932, TN=20013, FN=1023 精确重算，相对差 <1e-6。无抄数嫌疑，证据链完整闭环，授予满分 40。 |

## A 核心结果达成度（30.0/60）

Agent 报告的 test 期 TSS 为 0.5674。对照 SCORE_RUBRIC 数值带：满分带 [0.20, 0.42] 不满足；半满带 (0.42, 0.70] 满足；零分带 <0.10 或 >0.70 不满足。0.5674 明确落入半满带，且同步报告了 HSS、base-rate 漂移分析及阈值敏感性，证据落盘，故按 rubric 授予半满带固定分 30 分。因冻结数据无影像，GOES 历史 persistence 技能与论文 SDO 影像基线不同源，无法落入满分带。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示证据等级为 2（齐全自洽）。metrics.json 与 evidence_table.csv 均存在且列完整。关键抽查数 test 期 base_rate=0.2943 (n=43848) 与冻结锚值一致；TSS=0.5674 可由证据表 TP=11880, FP=10932, TN=20013, FN=1023 精确重算，相对差 <1e-6。无抄数嫌疑，证据链完整闭环，授予满分 40。

## 证据与重算说明

独立重算未执行（基于提交物静态核对与磁盘证据扫描）。关键实测数逐字引用：test n=43848, base_rate=0.294266, threshold=0.38, TP=11880, FP=10932, TN=20013, FN=1023, TSS=0.567444, HSS=0.463645。evidence_table 各行 TSS/HSS 均可由混淆矩阵重算，metrics.json 包含完整的漂移分解与 Bootstrap CI。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 方法极其严谨，特征严格滞后防泄漏，对 base-rate 漂移和泛化归因的分析量化透彻，证据表与 metrics 数值严格自洽且可重算。
- 不足: 受限于冻结数据仅含 GOES 标量序列，模型 TSS 落入半满带，无法复现论文 SDO 影像 CNN 基线的数值区间，导致 A 维度无法获得满分。