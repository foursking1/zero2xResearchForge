# SCORE_RUBRIC：L1 判分标准（私有）

- 任务：`2607.18127_cloudens`（ClouDens 云遥测上下文感知异常检测 critical claim）
- 判分模型：LLM 裁判（Claude / GLM 等均可；跨 agent 分数比较须使用同一裁判模型）
- 满分：100（A. 核心结果达成度 60 / B. 证据真实性 25 / C. 方法与报告 15）
- 判分流程：裁判读 TASK.md 与提交物 → 核对证据表数值 → 抽查重算 1-2 个关键数 → 按三维度打分。
- 锚值见 PAPER_ANCHOR.md（A1=Table IV MD/LF NAB；A2=混淆矩阵；A3=异常覆盖；A4=EQ2/Table V）。

## A. 核心结果达成度（60 分）

### A1. 方向性 claim（主 claim，MD 评分）— 30 分

判定 agent 证据表中 Mahalanobis（MD）策略下 ClouDens vs GRU 的 NAB（论文锚：Standard 20.94 vs 5.89；LowFN 26.24 vs 10.95）：

| 条件 | 得分 |
| --- | --- |
| 两个 profile 下 ClouDens > GRU，且 ClouDens/GRU 比值均 >= 1.3 | 30 |
| 两个 profile 下 ClouDens > GRU，比值 1.0-1.3（或一个 profile >=1.3 另一个 1.0-1.3） | 22 |
| 仅一个 profile 下 ClouDens > GRU（另一 profile 持平/反向，有讨论） | 12 |
| 方向不成立（ClouDens <= GRU 或结论标 contradicted） | <=5 |

- 若 agent 只做 LF 未做 MD → A1 最高 12 分。

### A2. 数值接近度（MD）— 20 分

agent 报告的 ClouDens MD NAB 与锚（Standard 20.94 / LowFN 26.24）比较：

| 条件 | 得分 |
| --- | --- |
| Standard ∈ [14, 28] 且 LowFN ∈ [18, 34] | 20 |
| Standard ∈ [10, 31] 且 LowFN ∈ [13, 39] | 13 |
| 其余（方向仍成立） | 6 |
| GRU MD NAB 纳入核对：GRU Standard <= 12、LowFN <= 16（锚 5.89/10.95，允许实现差异） | 加分项 +2（A2 上限 20） |

- 若 agent 以 LF 代替 MD 完成主 claim（LF 锚：ClouDens 11.38/18.11 vs GRU 6.58/13.16）→ A2 按 LF 锚同带宽给分，上限 13。

### A3. 检测质量与异常覆盖 — 10 分

| 条件 | 得分 |
| --- | --- |
| ClouDens TP > GRU TP 且 FP < GRU FP，且 ClouDens 检出 IM 异常数 >= GRU（锚 6/9 vs 4/9） | 10 |
| 满足其中任意 2 条 | 6 |
| 满足 1 条 | 3 |
| 均不满足 | 0 |

### 方向性校验

- 若报告 ClouDens 未超 GRU（任一 profile）→ A 总分直接 <= 20，结论应标 contradicted/inconclusive。
- 若测试期时点数与 26,488 偏差 > 1%，或 5xx count 特征数 != 2,406（偏差 > 1%）→ A 总分 x 0.8。

## B. 证据真实性（25 分）

- 提交必须含可运行代码 + 证据表（scoring_strategy/model/TP/TN/FP/FN/nab_standard/nab_lowfn/detected_* 列）——缺任一 → <=10 分。
- 裁判抽查 2 个关键数，从冻结数据重算：
  1. **数据事实**：parquet 行数 = 39,365；5xx count 特征数 = 2,406；anomaly_windows.csv 行数 = 25（测试期 19 窗 a7-a25；source 1=Issue Tracker）。
  2. **关键指标重算**：运行 agent 提交代码（或官方复现包，同随机种子）从冻结 parquet 重算 GRU 与 ClouDens 的 MD NAB（Standard）；与证据表一致（绝对差 <= 2.0 视为一致，容忍随机性）；若资源受限，至少完整重算 GRU（训练约 12 秒/A100）并验证 ClouDens 方向（可降 epoch 轻量运行 + 检查 agent 代码设置）。
- 计分：
  - 两个抽查数均可重算且一致 → 25。
  - 每个抽查数不可重算/不一致 → 各扣 8-12 分。
  - 无代码/代码不可运行 → 扣 8 分；evidence_table 缺失或列不完整 → 扣 5-10 分。
  - 报告把论文/复现包 CSV 数字当实测（抄数）→ B 直接 <= 10 分。

## C. 方法与报告（15 分）

| 子项 | 分值 | 判分要点 |
| --- | --- | --- |
| C1 方法合理性 | 5 | 协议正确：训练/测试日期划分、训练剔除异常窗、zero 插补、min-max 仅训练段、滑窗 w=6 单步预测、MD/LF 评分与阈值、NAB 计算；上下文图构建合理（共享属性→邻接权重）；GRU 与 ClouDens 除图外设置一致 |
| C2 防泄漏 | 6 | 异常标签只用于评估；min-max/插补统计量仅训练段；测试段未参与训练/验证/阈值选择；滑窗只用历史步 |
| C3 结论与边界 | 4 | claim A/B/C 结论标签与证据匹配；说明与论文复现包差异（版本/种子/GPU/epoch 数）；局限性诚实（随机性、计算资源、NAB 对阈值敏感） |

- 明显泄漏（用测试段训练/调参/校准）→ C 总分 <= 5，且 B 中该数不可信。

## 判定流程（judge 步骤）

1. 读 `TASK.md` → 确认提交物齐全（代码 + evidence_table.csv + report.md）。
2. 按 A1/A2/A3 判定（核对证据表 MD/LF 两策略数值与检出列表）。
3. 从冻结数据重算抽查 2 数 → 打 B。
4. 依 C1-C3 打 C。
5. 总分 = A+B+C；将得分与理由写入评测报告。

## 难度校准

- L1 设计目标区间 40-50（±10）。校准记录见 CALIBRATION.md（自测执行：待评测阶段执行，本批次跳过）。
- 主要杠杆：A1 方向门槛（比值 1.3）、A2 数值带宽（±33%）、A3 覆盖条件、B 抽查严格度（数据事实 + NAB 重算）。
