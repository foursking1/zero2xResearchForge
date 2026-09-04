# Agent 执行评测汇总

- 编排进程：codex exec（会话 `019ff646`，22:00–22:22）
- 执行 agent：Claude Code 2.1.91（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判：codex（LLM 裁判，独立脚本重算抽查）
- 评测时间：2026-08-12 22:21–22:22
- 范围：仅 2 张完好卡（astro + materials；biomed 中文损坏、cs 无数据、earth 未完成，未纳入）

| 任务卡                                              | 总分     | A 达成度 | B 证据  | C 方法  | 执行状态 | 结论标签                       | 备注                                                  |
| ------------------------------------------------ | ------ | ----- | ----- | ----- | ---- | -------------------------- | --------------------------------------------------- |
| astro / 2508.14107_suryabench_flare              | **70** | 30/60 | 25/25 | 15/15 | 成功   | partially_supported        | TSS=0.5674 落半满带；漂移分解严谨（分年 TSS 均值 0.176 vs 聚合 0.567） |
| materials / 2606.23725_comp_refs_not_experiments | **98** | 60/60 | 25/25 | 13/15 | 成功   | contradicted (provisional) | 完整再发现 LOO+bootstrap 保守协议；仅缺"首充动力学方向性偏差"边界说明         |

## 证据真实性抽查结论（防作弊）

- **astro**：抽查 test 期 base rate（0.2943）与 TSS（0.5674）均独立重算一致（相对差 0.00e+00）；证据表 9 行全表可重算；代码 `code/run.py` 裁判实跑（9.5s，exit 0）逐值一致。
- **materials**：抽查 b1 MAE=0.6682 V、b2 r=−0.9385、b3 保守 CI 上界 1.0905 V 全部独立重算一致；SHA-256 数据校验与 `in_training_corpus` 防泄漏断言通过；代码实跑一致。
- 两张卡均**无编造证据**，B 项满分。

## 与设计校准的关系

- materials 98 分与 CALIBRATION 首测自测 98/100 完全一致（设计者自测上限）。
- astro 70 分符合预期区间（目标普通 agent 40-50，强 agent 90+；本卡固有难度：冻结数据无 SDO 影像，A 满分带 [0.20,0.42] 纯 GOES 口径难命中，agent 以严格滞后+漂移分解压到半满带并获 C 满分）。

## 遗留事项

1. biomed 卡四件套中文全损坏（写入时编码丢失），需修复后才可执行评测。
2. cs/wildtab 卡 data/ 为空（数据未就位），需补数据。
3. earth 卡仅 TASK.md（官方源 NXDOMAIN 被 blocked），需等数据源恢复。
4. 本轮 codex 在写汇总文件前 task_complete 退出，本文件由人工（WorkBuddy）补写。

