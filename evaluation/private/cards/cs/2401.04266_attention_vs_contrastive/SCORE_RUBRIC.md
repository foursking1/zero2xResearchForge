# SCORE_RUBRIC：L1 判分标准（私有）

- 任务：`2401.04266_attention_vs_contrastive`（表格数据 attention vs contrastive 基准：难度划分 + 传统方法竞争力 critical claim）
- 判分模型：LLM 裁判（跨 agent 分数比较须使用同一裁判模型）
- 满分：100（A. 核心结果达成度 60 / B. 证据真实性 25 / C. 方法与报告 15）
- 判分流程：裁判读 TASK.md 与提交物 → 核对证据表数值 → 抽查重算 1-2 个关键数 → 按三维度打分。

## A. 核心结果达成度（60 分）

### A1. 难度划分复现率（锚：论文 Table 6 自洽 12/14 hard + 14/14 easy；自检复现 10/14 hard + 13/14 easy = 23/28）— 30 分

以证据表 `agree` 列统计（predicted_difficulty 与 difficulty_paper 一致数 / 28）：

| 一致数（/28） | 得分 |
| --- | --- |
| ≥24 | 30 |
| 20–23 | 24 |
| 16–19 | 15 |
| <16 | ≤8 |

- 方向性红线：若 hard 组整体复现出 gap<4pp（如 ≥8/14 hard 判为 Easy）→ A1 直接 ≤15，且 (a) 结论必须标 contradicted/partial；若 easy 组整体复现 gap≥4pp（≥8/14 easy 判为 Hard）同样处理。
- 附加加分（+0，仅记录）：hard 组 median gap ≥ +5pp 且 easy 组 median gap ≤ +2pp 说明划分方向稳健（写入报告可抵 A1 档内上浮，不越档）。

### A2. 方向性 claim 验证 — 30 分

**A2a. 传统方法在 easy 数据集上占优（15 分）**（锚：自检复现 11/14；论文 §5.2「traditional methods are frequently superior on easy-to-classify datasets」）

| trad_on_easy（/14） | 得分 |
| --- | --- |
| ≥10 | 15 |
| 8–9 | 11 |
| 6–7 | 7 |
| <6 | ≤4 |

**A2b. no-best 解读与 hard 组深度占优边界（15 分）**（锚：自检复现 mlp_on_hard=1/14；论文 Table 4 SAINT hard AvgRank=1.69）

- mlp_on_hard ≤7/14，且报告正确解读「hard 上深度占优的完整表述依赖 SAINT/NPT 等 attention/contrastive 模型（论文 Table 4），MLP 代理既不支撑也不证伪，与 no-best 结论一致」→ 15。
- 数值对但解读有误（如声称「MLP 未胜说明深度在 hard 不占优，全面否定论文」）→ 8。
- mlp_on_hard ≥9/14 且声称「MLP 在 hard 全面占优」→ 需对照论文 Table 6（如 4538 上 SAINT 0.716 > GBT 0.659、MLP 类 DNN 0.631）给出注意/对比，给 ≤10；无对照 → 4。

### 方向一致性校验（claim 与证据表自洽）
- 若结论判定与 evidence_table 数值方向矛盾（例如声称「easy 上 GBT 系统性优于 LR」但表中 gap 多为负）→ A 总分 ×0.8。

## B. 证据真实性（25 分）

- 提交必须含可运行代码 + 证据表（28 行，含 openml_id/name/difficulty_paper/f1_lr/f1_gbt/f1_mlp/gap/predicted/agree + 汇总指标）——缺任一 → ≤10。
- 裁判抽查 1-2 个关键数（抽查字段：`f1_lr`、`f1_gbt`；优先 4538 或 1067 行）：
  - 运行提交代码（或等价重算脚本）从 `F:\dataset\cs\2401.04266_attention_vs_contrastive\datasets\` 重算，与证据表一致（|Δ|≤3pp）→ 25。
  - 可重算但证据表与代码输出不一致 → 15。
  - 代码无法运行 / 不读取冻结 CSV / 数值疑似直接抄论文 → ≤8。
- 裁判重算基准（自检 2026-08-14，macro-F1，3 seeds，HistGB+LR+MLP）：4538 f1_lr=34.2 / f1_gbt=53.1；1067 f1_lr=62.9 / f1_gbt=64.3。

## C. 方法与报告（15 分）

| 检查点 | 分值 | 判分要点 |
| --- | --- | --- |
| 方法合理性 | 5 | 划分 70/10/20 分层随机、≥5 固定种子取均值；macro-F1 明确定义；预处理用 Pipeline（插补/one-hot/标准化只拟合 train） |
| 防泄漏 | 5 | test 未参与任何拟合/调参/早停；冻结 CSV 未修改 |
| 局限性与口径 | 5 | 讨论 weighted vs macro 口径（论文表值≈weighted，如 Kc1 GBT 0.831）；sklearn GBM vs 论文 GBT 实现差异；30 次划分 vs ≥5 次；未训练 SAINT/NPT 的范围限制 |

- 明显泄漏（如用 test 调参/选模型）→ C 总分 ≤5，结论标记不可信。

## 难度校准
- L1 目标区间 40–50（±10）。若实测持续 >60 → 收紧 A1 满分档（≥26）或加重 B 抽查；若 <30 → 放宽容差（如 A1 ≥18 满分）。校准记录见 CALIBRATION.md。
