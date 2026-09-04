# EVAL REPORT: 2604.04898v1（QED-Nano: Teaching a Tiny Model to Prove Hard Theorems）

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: WorkBuddy（LLM 裁判，独立脚本重算 `_prep/judge_check_04898.py`）
- 评测时间: 2026-08-13

## 总分: 50 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---|---|---|
| A 核心结果达成度 | 10 | 60 | 12 条 numeric 锚全部为论文声称值，冻结数据（本地 Qwen2.5-1.5B judge / 无 RSA / 无 IMO-AnswerBench / 无训练日志）无法复算；仅 C03 token 换分方向性与 C04 奖励数据存在性获部分支持 |
| B 证据真实性 | 25 | 25 | 裁判独立重算 3 实验 mean score 与配对检验，逐位一致 |
| C 方法与报告 | 15 | 15 | 统计口径严谨、口径差异表完整、局限披露诚实充分 |

## A 核心结果达成度（10/60）

### 关键前提（裁判核实）

论文 12 条 numeric 锚（R01-R07、R13-R15、R18、R20）全部来自 Gemini-3-Pro judge 的 avg@3 grade%。冻结数据：
- judge 为本地 Qwen2.5-1.5B-Instruct（0–7 rubric），与论文 judge 不可比（gold 解本地均值 5.867/7 ≈ 84%，论文 QED-Nano 无 scaffold 仅 40.0%——量纲不同）；
- **RSA scaffold 未实现**（仅 direct / RC 有完整 run，DSM 仅 1 例 wiring test）；
- IMO-AnswerBench 不在冻结快照；
- 无 step 级 RL 训练日志（Fig.3 曲线不可复现）。

→ 12 条 numeric 锚 **0 条可在冻结数据上以论文口径独立复算**，agent 全部如实标注 paper_reported，未编造数字。

### claim 判定复核

| Claim | agent 判定 | 裁判复核 | 依据 |
|---|---|---|---|
| C01 40.0/44.9/67.5（无 scaffold） | **inconclusive** | ✅ 合理 | 本地 30 题子集 qed_nano_direct=5.433 < qwen3_direct=5.489（p=0.73），与论文相对排序（QED-Nano 40.0 vs Qwen3 20.4）方向相左——受 judge 差异与 30 题子集限制，不足以证伪亦不支持 |
| C02 56.9/62.6/76.5（+RSA） | **inconclusive** | ✅ 合理 | RSA 未实现，RC 代理 5.506/7（p=0.66 vs direct）不显著 |
| C03 scaffold 对比（RSA 56.9% / 2,045,764 tokens） | **partially_supported** | ✅ 合理 | RSA 数值不可复现；方向性支持成立：RC 7.0× / DSM 76.9× tokens（vs direct），DSM 6.0 > RC 5.506 > direct 5.433，与论文 ranking 一致 |
| C04 rubric 奖励 RL（~350 步奖励+评测分同步上升） | **partially_supported** | ✅ 合理 | 数据存在性支持：FineProofs-RL 5227 题 × ~128 奖励/题、全部带 rubrics、96.7% 行 reward_mean>0；时间趋势不可验证（无训练日志） |

### A 小结

12 条 numeric 锚 0 条达成（全部数据限制）；4 条 claim 中无一条的绝对数值可在冻结数据上以论文口径复现。相比 04858（C04 实质达成 u-values 全 0），本篇无实质达成锚，仅 C03/C04 方向性与数据存在性部分成立 → A=10/60。

## B 证据真实性（25/25）

**独立重算抽查（裁判脚本 judge_check_04898.py，从冻结 JSONL 独立重算）：**

| 抽查项 | agent 报告 | 裁判重算 | 一致 |
|---|---|---|---|
| qwen3_direct mean score（IMO-30shot, n=90） | 5.489 | 5.4889 | ✅ 逐位 |
| qed_nano_direct mean score | 5.433 | 5.4333 | ✅ 逐位 |
| qed_nano_rc mean score（n=89 valid，1 例 NaN） | 5.506 | 5.5056 | ✅ 逐位 |
| mean tokens（direct / rc） | 1137.4 / 7968.3 | 1137.4 / 7968.3 | ✅ 逐位 |
| frac≥6（qwen3 / qed_nano） | 0.756 / 0.689 | 0.7556 / 0.6889 | ✅ 逐位 |
| 配对 diff qwen3−qednano（t-test p） | +0.0556 (0.7254) | +0.0556 (0.7254) | ✅ 逐位 |
| 配对 diff rc−direct（t-test p） | +0.0722 (0.6593) | +0.0722 (0.6593) | ✅ 逐位 |

- 代码完整（analyze_datasets / analyze_reproduction / analyze_rewards / build_evidence / make_figures），全部产物落盘
- 诚实声明：误运行将 dataset_overview.json 写入冻结目录（3KB 分析产物非原始数据），已披露

## C 方法与报告（15/15）

- C1 方法合理性（5/5）：配对检验（按题聚合 3 seed 均值后 paired t-test + Wilcoxon）口径正确；6 项论文↔本地 harness 口径差异表清晰（judge/scaffold/AnswerBench/解码/规模）；无泄漏
- C2 稳健性（5/5）：3 seeds × 双数据集（IMO 30 题 + ProofBench 15 题）交叉验证；双统计检验一致
- C3 边界与结论（5/5）：局限披露完整（judge 差异、subset、RSA 未实现、AnswerBench 缺失、无训练日志）；inconclusive/partially_supported 判定保守不夸大，未把"本地相对比较"包装成论文数值复现

## 结论

- **科学结论**：4 条 claim 无一条绝对数值可复现（judge/scaffold/数据缺失三重限制），C01/C02 `inconclusive`、C03/C04 `partially_supported`（方向性 + 数据存在性）→ 整体 `inconclusive`（数据受限）
- 证据真实性满分：全部 computed_local 数字（含配对检验 p 值）独立重算逐位一致
- 主要扣分在 A 达成度：本篇是数据受限最严重的任务之一（论文主结果依赖 Gemini-3-Pro 与 RSA，均不在冻结集内），agent 执行正确但可达成锚极少
