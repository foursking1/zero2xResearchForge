# EVAL REPORT: 2604.04914v1（Pensieve 符号性质验证）

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: WorkBuddy（LLM 裁判，独立脚本重算 + 冻结模型前向复验）
- 评测时间: 2026-08-13 21:15

## 总分: 71 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---|---|---|
| A 核心结果达成度 | 32 | 60 | 3 条 numeric 锚（R08 45% / R09 60%）均未定量命中；任务范围内 figure 类锚（C01/C03/C04）全部给出且定性方向一致；C02 数据不可得 → inconclusive |
| B 证据真实性 | 25 | 25 | 独立重算 216 条 JSONL 全部统计逐位一致；2 个 CROWN unsafe 反例用冻结 ONNX 模型前向求值 max_margin=0.0 复验一致；参数量逐位一致 |
| C 方法与报告 | 14 | 15 | 三后端实现严谨、模型精确提取、MIP 编码修复有记录；缺预算/多 seed 敏感性；局限 6 条诚实充分 |

## A 核心结果达成度（32/60）

### 锚点对照（PAPER_ANCHOR 11 条规则中与本任务 4 claim 相关的部分）

| 规则 | 类型 | 锚值 | agent 报告 | 命中 |
|---|---|---|---|---|
| R01 Capacity Utilization 热图 | figure | —（checkpoint × 查询） | 给出模型×查询热图（MIP/CROWN 各 1 张），定性一致 | ✅ 部分（缺 checkpoint 轴） |
| R02 Rebuffering/Robustness 聚合堆叠图 | figure | —（checkpoint × coverage） | 单 coverage=100% 堆叠图给出，unknown 为主定性一致 | ✅ 部分（缺两轴） |
| R03 执行时间箱线图 | figure | —（CROWN vs MIP） | 箱线图给出：CROWN 可秒级解析、MIP 全触顶，差异定性存在 | ✅ 部分（预算截断） |
| R08 较小模型 unknown 少 ~45% | numeric | 45.0 ± 5.0/10% | 12.5%（small vs mid/big，union 口径） | ❌（agent 明确标注"不作为论文数值复现"） |
| R09 被解析查询约 60% 仅单引擎判定 | numeric | 60.0 ± 5.0/10% | 100%（2/2） | ❌（同上，样本仅 2 个） |
| R10 CMARS pi_{2,30} 扰动 26 单位偏移 | numeric | 26.0 ± 1.0/5% | 不在本任务 4 claim 范围（TASK 仅 Pensieve） | —（不适用） |

### 各 claim 判定

| Claim | 判定 | 说明 |
|---|---|---|
| C01 Capacity Utilization 热图 | partially_supported | 3 模型×6 查询热图给出；MIP 0 解析、CROWN 仅 small×a3_b0（1.67s unsafe）；"100% coverage 下形式化解析极难、小模型更易解析"定性一致，但 checkpoint 轴缺失（冻结数据无） |
| C02 π^128/π^64 奖励曲线几乎一致 | inconclusive | 冻结数据无训练/奖励曲线；公开 ONNX 模型（48 输入、136,838 参数）与论文架构（25 输入、H=128/64、103,174/27,142）不匹配，无法构造验证 |
| C03 CROWN/MIP 执行时间差异 | partially_supported | 20s 预算下 MIP 0/72、CROWN 2/72（1.67s/2.05s 秒级解析）；big MIP 中位数 34.6s；差异定性存在但被预算截断，幅度不可定量复现 |
| C04 Rebuffering/Robustness 聚合 | partially_supported | small 3 unsafe/21 unknown、mid/big 全 unknown、Rebuffering 全 unknown；与论文图 6 在 100% coverage 下 unknown 为主定性一致，但 checkpoint × coverage 两轴缺失 |

### A 小结

本包为**数据不完整型 + 架构不匹配型**：论文数值锚（45%/60%）依赖的 checkpoint/reward/低 coverage 数据在冻结集中不存在，且公开模型与论文架构不符。agent 无任何直接矛盾证据，定性方向全部与论文一致，figure 类锚全部给出；但 R08/R09 两个数值锚未定量命中（给出 12.5%/100% 的替代口径参考并诚实标注非复现）。按容差加权约 32/60（figure 覆盖 + 定性一致 + 无矛盾，数值锚未命中扣分；C02 数据不可得不归因 agent）。

## B 证据真实性（25/25）

- **独立重算抽查（核心统计）**：裁判脚本从 216 条 `analysis_results.jsonl`（3 模型 × 24 查询 × 3 后端，数量吻合）独立重算：
  - C03 执行时间：small MIP med **20.73**（触顶 24/24）、CROWN med **20.03** min **1.67**（触顶 22/24）；big MIP med **34.62**——与 agent 报告逐位一致 ✅
  - 后端解析数：MIP 0/72、CROWN 2/72（small 两查询）✅
  - C04 聚合：small 3 unsafe/21 unknown、mid/big 24 unknown、Rebuffering 18/18 unknown ✅
  - R08/R09 风格指标：small vs mid/big unknown 减少 **12.5%**、单引擎判定占比 **100%** ✅
- **独立前向复验（反例真实性）**：裁判用冻结 ONNX 模型（`F:\dataset\2604.04914v1`）+ agent 的 `extract_relu_net`/`parse_vnnlib`，将 2 个 CROWN-BaB unsafe 的 witness 展开回 96 维输入做精确前向求值：两个反例 max_margin 均 **0.000000**（≤0 违规成立），与 agent 记录 best_margin=0.0 逐位一致 ✅
- **参数量复验**：small=136,838 / mid=363,398 / big=626,438，与 agent 报告逐位一致 ✅
- 代码完整可运行（`pensieve_verify/` 包 + run_analysis + make_figures + make_evidence）；结果全部有 JSONL 溯源；`paper_cited` vs `computed` 标注严格。未发现编造。

## C 方法与报告（14/15）

- C1 方法合理性（5/5）：三后端（heuristic/MIP/CROWN-BaB）实现完整；ONNX 模型精确提取（float64 前向、与 onnxruntime 校验 ≤2e-4）；比较网络编码正确；MIP big-M ReLU 编码符号错误有修复记录（6,078 行约束 0 违例）；无未来信息/泄漏
- C2 不确定性/稳健性（3/5→4/5）：给出触顶率、min/median/mean 分布统计与预算截断的诚实说明；但仅单一 20s 预算、单一 seed，无预算敏感性对照（如 60s/120s 或多 seed），对"unknown 比例"的稳健性缺乏分析。扣 1 分
- C3 边界与结论（5/5）：6 条局限非常诚实（数据不可得维度、后端能力差异、模型不匹配、certified 语义、MIP 编码、磁盘限制）；结论不夸大（明确"不作为论文数值的复现"）；C02 判 inconclusive 恰当

## 结论

- **科学结论**：`partially_supported`（3/4 claim 部分支持，C02 因数据不可得 inconclusive，无矛盾证据）
- agent 判定与裁判独立评估一致；数据真实性满分（JSONL 统计 + 反例前向 + 参数量三重复验）
- 主要扣分在 A：R08/R09 数值锚未定量命中（数据与架构限制，agent 已诚实标注非复现）+ C02 无法验证
- 备注：solution.md 完整（16.5KB，判定表、方法、结果、局限齐全）；进程 20:20 后无写入，产物稳定后评测
