# 2406.10292_cto_trial_outcomes — agent solution

CTO「LLM+时序链接自动标注临床试验结局」关键论断验证（L1）。

## 交付物

- `claim.md` — 四档判定与关键数字
- `solution.md` — 方法+核心结果摘要
- `report.md` — 完整报告（方法/结果/局限/失效场景）
- `code/` — 可复现脚本（`run_all.sh` 一键运行）
- `results/` — 证据表、指标 JSON、阈值扫描、覆盖率
- `report_fig/` — 复现 vs 论文锚点图
- `evidence/` — 关键证据导出副本

## 如何运行

```bash
bash agent_solution/code/run_all.sh
```

数据目录自动定位：`$CTO_DATA_DIR` → 任务 `data/` → `/mnt/f/dataset/biomed/2406.10292_cto_trial_outcomes/` → `/mnt/d/dataset/...`。5 个冻结 CSV 的 SHA-256 在运行期核验。

## 依赖

Python ≥3.8；pandas, numpy, scikit-learn, matplotlib。无 GPU。

## 判定摘要

- (a) CTORF 复现：**supported**（全体 F1 0.9551 vs 0.909，rel. +5.1%；κ 0.9335，rel. +28.1%）
- (b) 人工-自动一致性：**supported**（匹配 3,239/5,060/2,823/11,122；F1 0.9551、κ 0.9335）
- (c) 失效场景：**supported**（无监管/摘要/新闻/p值/链接/股价缺失 → 覆盖损失与保守兜底）
- 主论断：**supported**