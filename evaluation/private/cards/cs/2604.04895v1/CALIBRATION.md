# CALIBRATION（私有）：2604.04895v1

## 1. 目标

- 层级：L2（RCBench 对齐端到端再发现），目标难度：普通 agent ~30（±10）。
- 自测方式：Claude Code 跑一遍 + 按 SCORE_RUBRIC 自评（**本轮未执行，留待评测阶段**）。

## 2. 设计要点

- claims：10 条（可证伪问题来源）。
- verification rules：16 条（裁判锚，见 PAPER_ANCHOR）。
- 数据：真实冻结（F:\dataset / scisolvebench-assets/datasets/v1），未复制、原位引用。

## 3. 状态

- **compiled（未自测校准）**：四件套齐；claude 自测与难度校准留待评测阶段。
- 记录时间：2026-08-13
