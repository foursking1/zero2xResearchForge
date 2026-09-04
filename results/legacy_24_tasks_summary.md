# Legacy 24 篇造题汇总（轻量协议 v2.0，未跑评测）

- 生成时间：2026-08-13 10:59
- 生成方式：`work/build_legacy_tasks.py`（解析 truth/*.md → claims/rules → 四件套）
- 数据：引用 F:\dataset 与 E:\scisolvebench-data\asset-data\datasets-v1\v1（原位读取，不复制）
- 状态：**compiled（未自测校准）**——claude 自测与难度校准留待评测阶段

| 论文 ID | 标题（截断） | claims | rules | 数据位置 |
|---|---|---|---|---|
| 08_tapley_2004 | GRACE Measurements of Mass Variability in the Earth System | 7 | 24 | F:\dataset\08_tapley_2004 |
| 2604.04477v1 | MVISFOLD 3D vascular reconstruction | 6 | 14 | F:\dataset\2604.04477v1 |
| 2604.04518v1 | Shortcut Learning Correction | 10 | 15 | F:\dataset\2604.04518v1 |
| 2604.04673v1 | Minimaxity and Admissibility of Bayesian Neural Networks | 7 | 22 | F:\dataset\2604.04673v1 |
| 2604.04681v1 | BLS Dynamic Data Pruning | 11 | 30 | F:\dataset\2604.04681v1 |
| 2604.04832v1 | When One Sensor Fails (EMG) | 3 | 13 | F:\dataset\2604.04832v1 |
| 2604.04842v1 | PCSA Counseling Vulnerability | 8 | 20 | F:\dataset\2604.04842v1 |
| 2604.04858v1 | FairLogue Intersectional Fairness | 10 | 34 | F:\dataset\2604.04858v1 |
| 2604.04868v1 | (12 claims) | 12 | 17 | F:\dataset\2604.04868v1 |
| 2604.04871v1 | (9 claims) | 9 | 19 | F:\dataset\24_2604.04871v1 |
| 2604.04878v1 | (6 claims) | 6 | 14 | F:\dataset\2604.04878v1 |
| 2604.04891v1 | (2 claims) | 2 | 10 | F:\dataset\2604.04891v1 |
| 2604.04895v1 | Agentic Federated Learning | 10 | 16 | F:\dataset\2604.04895v1 |
| 2604.04898v1 | (10 claims) | 10 | 21 | F:\dataset\2604.04898v1 |
| 2604.04911v1 | SpatialEdit Spatial Image Editing | 7 | 22 | F:\dataset\2604.04911v1 |
| 2604.04914v1 | DRL Policy Formal Verification | 10 | 11 | F:\dataset\2604.04914v1 |
| 2604.04915v1 | (7 claims) | 7 | 14 | F:\dataset\2604.04915v1 |
| 2604.04923v1 | STL RL Representation Geometry | 7 | 20 | F:\dataset\2604.04923v1 |
| 2604.04930v1 | Confidence Dynamics Early Stopping | 8 | 22 | F:\dataset\2604.04930v1 |
| bensen_2007 | Seismic ambient noise surface wave dispersion | 14 | 25 | E:\...\datasets-v1\v1\bensen_2007 |
| bonjean_2002 | Tropical Pacific Currents (TAO) | 10 | 26 | F:\dataset\42_bonjean_2002_mem_n |
| gehlen_2019 | (2 claims) | 2 | 36 | E:\...\datasets-v1\v1\gehlen_2019 |
| pages2k_2019 | (6 claims) | 6 | 37 | E:\...\datasets-v1\v1\pages2k_2019 |
| wong_2020 | (8 claims) | 8 | 22 | E:\...\datasets-v1\v1\wong_2020 |

## 说明

- 每篇四件套：`tasks_legacy/<id>/TASK.md` + `PAPER_ANCHOR.md` + `SCORE_RUBRIC.md` + `CALIBRATION.md` + `data/DATA_MANIFEST.md`（2026-08-13 11:24 从 tasks/ 移入独立目录，避开批量造题 agent 的清理）
- TASK.md 问题来自 truth claims（可证伪）；PAPER_ANCHOR 锚来自 verification rules（含 target_value/tolerance）
- SCORE_RUBRIC 按 v2.0：A 达成度 60 / B 证据真实性 25 / C 方法与报告 15
- CALIBRATION 记录目标难度 L2 ~30，未跑自测
- 待办：claude 自测校准、专家审题、评测
