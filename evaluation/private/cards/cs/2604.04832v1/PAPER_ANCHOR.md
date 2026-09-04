# PAPER_ANCHOR（私有）：2604.04832v1

> 论文：When One Sensor Fails: Tolerating Dysfunction in Multi-Sensor Prototypes
> 出处：arXiv:2604.04832v1, April 2026
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 13 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（numeric）FDR-based task complexity analysis predicts paper-vs-scissors is over 10x more d

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | numeric | Normalized FDR score for paper-vs-scissors gesture pair shou | 0.073 | abs 0.02 / 5.0% |
| R02 | numeric | Normalized FDR score for rock-vs-paper gesture pair should b | 0.842 | abs 0.02 / 5.0% |
| R03 | numeric | Normalized FDR score for rock-vs-scissors gesture pair shoul | 1.0 | abs 0.02 / 5.0% |
| R04 | trend | Low FDR for paper-scissors should correspond to lower MCC co | — | abs — / —% |
| R12 | exists | Preprocessed windowed sEMG segments must exist with 296 samp | windowed_segments | abs — / —% |
| R13 | exists | Extracted feature vectors must have 72 dimensions (8 sensors | 72 | abs — / —% |

### C02（numeric）MLP validation oracle confirms FDR predictions: paper-vs-scissors achieves MCC o

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R05 | numeric | MCC score for paper-vs-scissors binary MLP classifier should | 0.872 | abs 0.05 / 5.0% |
| R06 | numeric | MCC score for rock-vs-paper binary MLP classifier should be  | 0.99 | abs 0.02 / 5.0% |
| R07 | numeric | MCC score for rock-vs-scissors binary MLP classifier should  | 1.0 | abs 0.02 / 5.0% |

### C03（figure）Sensor ablation audit reveals task-dependent sensor importance: Sensor 2 is high

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R08 | figure | Per-class sensor criticality figure showing FDR shift scores | — | abs — / —% |
| R09 | trend | Sensor 2 should show significantly higher FDR shift for 'pap | — | abs — / —% |
| R10 | trend | Sensors 6 and 7 should show minimal FDR shift (redundant) ac | — | abs — / —% |
| R11 | trend | Sensor importance should vary across gesture classes (task-d | — | abs — / —% |
