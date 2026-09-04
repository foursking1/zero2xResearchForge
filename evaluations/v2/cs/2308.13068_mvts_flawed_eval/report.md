# EVAL REPORT v2: 2308.13068_mvts_flawed_eval

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1: agent 报告 SWaT F1pa=0.9472, F1pw=0.0044 (差距0.9428)；PSM F1pa=0.9742, F1pw=0.0217 (差距0.9525)。均满足 F1pa≥0.85 且差距≥0.4，落入满分带，得25分。A2: agent 报告 oracle 阈值下逐点 F1，SWaT 上 PCA(0.7964) ≥ GRU-AE(0.7889)，PSM 上 PCA(0.6131) ≥ GRU-AE(0.5257)。两个数据集均报告且简单基线均胜出，落入满分带，得25分。A3: 报告了逐点与 point-adjust 协议下的 F1 差异与排序反转（随机猜测从垫底到第一），给出 supported 标签且与证据强一致，落入满分带，得10分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示 metrics.json 与 evidence_table.csv 均存在且列完整。抽查 PSM 异常比例 27.76% (24381/87841) 与锚值一致；随机猜测逐点 F1 (SWaT 0.0044, PSM 0.0217) 量级正确。evidence_table 中的 PCA 与 GRU-AE 逐点 F1 数值与报告及 metrics.json 严格一致，无抄数或泄漏痕迹。落入最高档 [30,40]，给 40 分。 |

## A 核心结果达成度（60/60）

A1: agent 报告 SWaT F1pa=0.9472, F1pw=0.0044 (差距0.9428)；PSM F1pa=0.9742, F1pw=0.0217 (差距0.9525)。均满足 F1pa≥0.85 且差距≥0.4，落入满分带，得25分。A2: agent 报告 oracle 阈值下逐点 F1，SWaT 上 PCA(0.7964) ≥ GRU-AE(0.7889)，PSM 上 PCA(0.6131) ≥ GRU-AE(0.5257)。两个数据集均报告且简单基线均胜出，落入满分带，得25分。A3: 报告了逐点与 point-adjust 协议下的 F1 差异与排序反转（随机猜测从垫底到第一），给出 supported 标签且与证据强一致，落入满分带，得10分。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示 metrics.json 与 evidence_table.csv 均存在且列完整。抽查 PSM 异常比例 27.76% (24381/87841) 与锚值一致；随机猜测逐点 F1 (SWaT 0.0044, PSM 0.0217) 量级正确。evidence_table 中的 PCA 与 GRU-AE 逐点 F1 数值与报告及 metrics.json 严格一致，无抄数或泄漏痕迹。落入最高档 [30,40]，给 40 分。

## 证据与重算说明

独立重算未执行，但代码逻辑完整且包含 verify_frozen_facts.py 复核脚本。关键实测数：PSM 异常比例 27.76%；随机猜测 F1pa (SWaT 0.9472, PSM 0.9742)；PCA 逐点 F1 (SWaT 0.7964, PSM 0.6131)。所有数值在 report、metrics.json 和 evidence_table.csv 中高度一致，证据链闭环。

## 结论

- **科学结论**: `supported`
- 亮点: 实验设计极其严谨，不仅完美复现了核心结论，还额外引入了固定阈值对照和逐通道标准化变体，深刻揭示了阈值选择对“简单vs复杂”结论的敏感性，报告逻辑清晰。
- 不足: 深度方法仅实现了 GRU-AE，未覆盖 Transformer 类（如 AT）以作更全面的横向对比，但作为 L2 任务已远超预期。