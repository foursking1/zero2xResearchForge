# EVAL REPORT v3: 2211.15895_bertos_oxidation_state

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 63.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 35.0 | 60 | 逐项核对实测数值：PS(ICSD×ICSD)=96.78%（锚96.25±1.5），PS(ICSD_oxide×ICSD_oxide)=97.50%（锚97.04±1.5），PS(ICSD_CN×ICSD_CN)=96.34%（锚95.75±1.5），PC=86.63%（锚84.80±3），金属/非金属精度及数据规模均落入满分带，4x4交叉矩阵与论文偏差≤0.14pp。原始计算得分为60，但受【磁盘证据扫描】证据等级=1的硬约束（A≤35），强制截断至35分。 |
| B 证据真实性/实际复现 | 28.0 | 40 | 【磁盘证据扫描】显示 metrics.json 与 evidence_table 特定命名文件缺失，判定证据等级=1，触发 B∈[11,29] 硬规则。尽管 agent 实际提交了 evaluation_results.json 及多个 CSV 且内含完整矩阵、与代码逻辑自洽，但 EVAL_REPORT.md 存在严重文本幻觉（将96%误写为0.01%）导致报告内部不一致，且文件命名未命中扫描正则，故给予该区间上限 28 分。 |

## A 核心结果达成度（35.0/60）

逐项核对实测数值：PS(ICSD×ICSD)=96.78%（锚96.25±1.5），PS(ICSD_oxide×ICSD_oxide)=97.50%（锚97.04±1.5），PS(ICSD_CN×ICSD_CN)=96.34%（锚95.75±1.5），PC=86.63%（锚84.80±3），金属/非金属精度及数据规模均落入满分带，4x4交叉矩阵与论文偏差≤0.14pp。原始计算得分为60，但受【磁盘证据扫描】证据等级=1的硬约束（A≤35），强制截断至35分。

## B 证据真实性/实际复现（28.0/40）

【磁盘证据扫描】显示 metrics.json 与 evidence_table 特定命名文件缺失，判定证据等级=1，触发 B∈[11,29] 硬规则。尽管 agent 实际提交了 evaluation_results.json 及多个 CSV 且内含完整矩阵、与代码逻辑自洽，但 EVAL_REPORT.md 存在严重文本幻觉（将96%误写为0.01%）导致报告内部不一致，且文件命名未命中扫描正则，故给予该区间上限 28 分。

## 证据与重算说明

独立重算未执行。关键实测数均落盘于 evaluation_results.json：PS(ICSD×ICSD)=96.7778%，PS(ICSD_CN×ICSD_CN)=96.3384%，PC=86.6273%，测试集块数 ICSD=5215, ICSD_CN=3724。落盘数据与代码逻辑自洽，但缺乏规范命名的 metrics.json/evidence_table，且总结报告存在幻觉。

## 结论

- **科学结论**: `supported`
- 亮点: 评估协议严谨，16格交叉矩阵与论文高度吻合，落盘 JSON/CSV 证据详实且与代码输出完全一致，科学结论完全成立。
- 不足: 输出文件命名未对齐扫描脚本预设的 metrics.json/evidence_table 规范导致证据等级降级；EVAL_REPORT.md 中存在将 96% 误写为 0.01% 的严重文本幻觉。