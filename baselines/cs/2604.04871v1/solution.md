# StatsClaw 架构声明验证报告（arXiv:2604.04871v1）

- 任务：对 TASK.md 中 4 条可证伪声明（C01–C04）设计并执行分析，使用冻结数据（原始根目录 `F:\dataset\24_2604.04871v1`，原位读取）重现论文关键结果并给出判定。
- 分析方法：**结构性源码审计**（grep/regex 于 `statsclaw_repo/` 冻结框架源码）+ **论文文本对照**（`pdftotext` 从冻结 PDF 提取）+ **数值佐证**（冻结的 `data/monte_carlo_results.csv`）。
- 可复现：全部指标由 `agent_solution/code/analyze_claims.py` 实际运行产生；运行命令：

```bash
cd <task_root> && python agent_solution/code/analyze_claims.py
```

---

## 1. 数据与方法

### 1.1 使用数据（原位读取，未复制）

| 数据 | 路径（冻结，只读） |
|---|---|
| 论文 PDF | `F:\dataset\24_2604.04871v1\arxiv_2604.04871v1_original.pdf` |
| StatsClaw 框架源码 | `F:\dataset\24_2604.04871v1\statsclaw_repo\`（提交 `4dc6512`，2026-04-10） |
| 示例包（StatsClaw 产物） | `F:\dataset\24_2604.04871v1\example-probit\`（提交 `b93969f`，2026-04-01） |
| 蒙特卡洛冻结数据 | `F:\dataset\24_2604.04871v1\data\monte_carlo_results.csv` |

### 1.2 口径与参数

- **代理（agent）清单**：`statsclaw_repo/agents/*.md` 中的定义文件（共 9 个：builder, distiller, leader, planner, reviewer, scriber, shipper, simulator, tester）。
- **信息隔离检查**：对 builder/tester/simulator 三个执行代理，用正则逐条核对其"禁止读取"约束（`NEVER READS` / `Never receives` / `MUST NOT read`）是否显式排除另一流水线的规范文档（spec.md / test-spec.md / sim-spec.md / implementation.md），共 10 项检查；另做 3 项"正向对照"（各代理确实收到自己的主规范）。
- **状态机检查**：解析 `statsclaw-repo/skills/statsclaw-protocol/SKILL.md` 的 State Model 链与 "Hard Enforcement: State Transition Preconditions" 表，统计状态数、中断态、前提条件行数。
- **论文文本对照**：`pdftotext -layout` 提取全文，关键词短语匹配（先归一化空白以消除分页断行）。
- **数值佐证（补充）**：对 `monte_carlo_results.csv` 的 24 行（4 个 N × 2 个参数 × 3 种方法，各 500 次重复）重算覆盖区间、失败数、N=5000 时 MLE 最大绝对偏误、MH 接受率区间、MLE/Gibbs 耗时比。

### 1.3 免责说明

`verification/` 与 `report/` 下的既有复现报告仅作为裁判参考，本报告的全部数值均为上述脚本本次实际运行所得，未直接采用既有报告数字（除明确标注"论文引用"处）。

---

## 2. 结果

### 2.1 关键指标表（本次运行计算值）

| 声明 | 指标 | 计算值 | 口径/来源 |
|---|---|---|---|
| C01 | 代理定义文件数 | 9 | `statsclaw_repo/agents/*.md` |
| C01 | 信息隔离检查通过 | 10 / 10 | builder/tester/simulator 的 NEVER READS / Never receives / MUST NOT read |
| C01 | 主规范"正向对照"通过 | 3 / 3 | 各执行代理收到自己的主规范 |
| C01 | isolation 技能流水线规则成立 | 7 / 7 | `skills/isolation/SKILL.md` |
| C01 | Leader 派发隔离规则存在 | 是 | `agents/leader.md` "MUST NOT pass spec.md to tester" |
| C02 | 仓库代理定义文件数 | 9 | `agents/*.md` |
| C02 | 论文正文声称代理数 | eight（8） | 论文引用：Section 2.1 "orchestrates eight specialized agents" |
| C02 | 论文脚注第 9 代理 | 是（distiller, brain-mode only） | 论文引用：脚注 1 |
| C02 | 附录 A1 表列出的代理 | 8 / 8 匹配 | 论文引用：Table A1 |
| C02 | 仓库 README 自称代理数 | 9 | `statsclaw_repo/README.md` |
| C02 | 单一 Claude Code 会话 | 是（论文正文+协议均支持） | 论文引用 + `SKILL.md` "Agent tool 派发" |
| C03 | planner 产出 spec.md / test-spec.md / sim-spec.md | 是 / 是 / 是 | `agents/planner.md` |
| C03 | "independently sufficient" 出现 | 1 | `agents/planner.md` |
| C03 | 派发时隔离规则（builder/tester/simulator） | 是 / 是 / 是 | `skills/isolation/SKILL.md` |
| C04 | 状态机命名状态数 | 10 | `SKILL.md` State Model 链 |
| C04 | 核心（非可选）状态数 | 9 | 剔除可选的 KNOWLEDGE_EXTRACTED |
| C04 | 中断状态数 | 3（HOLD/BLOCKED/STOPPED） | `SKILL.md` |
| C04 | 前提条件表行数（覆盖 9 个目标状态） | 18 行 | `SKILL.md` "Hard Enforcement" 表 |
| C04 | Leader 按前提条件门控状态迁移 | 是 | `agents/leader.md` |

### 2.2 补充数值佐证（本次从冻结 CSV 重算）

| 指标 | 计算值 | 说明 |
|---|---|---|
| 蒙特卡洛总有效重复 | 12,000（24 单元 × 500） | `n_valid` 求和 |
| 模拟失败数 | 0 | `n_fail` 求和 |
| 95% 覆盖率区间 | [0.920, 0.962] | 全部 24 单元 |
| N=5000 时 MLE 最大绝对偏误 | 0.00228 | `max|bias|` over beta_0/beta_1 |
| MH 接受率区间 | [0.3961, 0.4009] | 论文引用口径 ~0.40 |
| MLE/Gibbs 耗时比 | 268–541× | N=200→5000，beta_0 单元 |
| RMSE 随 N 衰减比（N=200→5000, MLE） | 5.31（beta_0）/ 5.73（beta_1） | 论文引用口径 ~1/sqrt(N)，期望 ~√25=5.0 |

> 数值佐证仅用于确认 StatsClaw 产出的 example-probit 包确实收敛且结果合理（支持 C01/C03 中"可产生可验证的统计软件"这一上下文），不构成对 C01–C04 的直接判定。

---

## 3. 结论（声明判定）

### C01：StatsClaw 是多代理架构，且在代码生成与验证之间实施信息屏障 — **supported**

依据：
- **多代理**：仓库 `agents/` 目录存在 9 个代理定义文件，每个均有独立角色（Leader 编排、Planner 规划、Builder/Simulator/Tester 三执行代理、Scriber 记录、Reviewer 收敛门、Shipper 发布；Distiller 为可选）。
- **信息屏障**：10/10 项显式禁止检查全部命中。builder.md:30/69 显式 `NEVER READS test-spec.md` 与 `MUST NOT read test-spec.md`；tester.md:29/67 显式 `NEVER READS spec.md, implementation.md` 与 `MUST NOT read spec.md`；simulator.md:44/83 显式 `Never receives spec.md, test-spec.md` 与 `MUST NOT read`。`skills/isolation/SKILL.md` 的 7 条流水线规则全部成立；Leader 派发规则（不得向 tester 传 spec.md）存在。
- **论文引用**：摘要原文 "information barriers between code generation and code validation"；2.2 节详述三规范隔离。
- 判定：**supported**（代码与论文双重一致）。

### C02：StatsClaw 在单个 Claude Code 会话内编排八个专门代理 — **partially_supported**

依据：
- **支持侧**：论文引用（Section 2.1）正文即 "StatsClaw orchestrates eight specialized agents within a single Claude Code session"；附录 Table A1 恰好列出 8 个代理（Leader, Planner, Builder, Tester, Simulator, Scriber, Reviewer, Shipper）且全部在仓库中找到对应定义；"单一会话内以 Agent tool 派发、非独立进程"亦被 `SKILL.md`（"You MUST use the Agent tool to dispatch every teammate"）支持。
- **不支持侧（计数分歧）**：仓库实际含 **9** 个代理定义文件；仓库自身 README 亦自称 "a team of **9** specialized AI agents"。第 9 个（distiller）被论文脚注 1 明确说明为可选的 Brain mode（默认关闭、未列入本论文讨论）。因此"八个"仅指核心架构，与实现中的文件计数（9）不完全一致。
- 判定：**partially_supported**。若声明按"论文描述的核心 8 代理架构"理解则成立；若按"实现的实际代理集合"理解，则计数为 9（distiller 为可选附加），声明需加脚注修正。

### C03：规划代理产出相互独立的规范文档并派发给相互隔离的代理 — **supported**

依据：
- planner.md 明确产出 `spec.md`（builder）、`test-spec.md`（tester）、`sim-spec.md`（simulator，模拟工作流 11/12 才有）；要求所有规范 "independently sufficient"，并含禁止泄漏规则（"MUST NOT leak implementation details into test-spec.md"、"MUST NOT leak test scenarios into spec.md"）。
- `skills/isolation/SKILL.md` 派发规则：builder 只收到 spec.md（NEVER 提及 test-spec.md/sim-spec.md）；tester 只收到 test-spec.md（NEVER 提及 spec.md/sim-spec.md/implementation.md）；simulator 只收到 sim-spec.md（NEVER 提及 spec.md/test-spec.md）。三项派发隔离检查全部命中。
- **论文引用**：摘要 "produces two independent documents… Neither agent sees the other's document"；2.2 节 "the planner produces three self-contained specification documents… Each document is independently sufficient for its recipient. Neither references the other."
- 局限：运行期实际的 `spec.md`/`test-spec.md`/`sim-spec.md` 产物位于 workspace 仓库（`skills/workspace-sync/SKILL.md`），不在本次冻结数据中（冻结数据中 0 个此类文件）；故验证的是**机制在代码中的强制规定**，而非某次运行的产物文件。example-probit 包（含 `probit_spec.pdf` 输入与 `ARCHITECTURE.md`"Generated by scriber"记录）佐证该流程确实被用于产出真实 R 包。
- 判定：**supported**（机制层面完全成立；运行产物不在冻结范围属数据可用性限制）。

### C04：StatsClaw 实现状态机，在每次迁移处强制顺序门与必需前提条件 — **supported**

依据：
- `SKILL.md` 定义了状态链（CREDENTIALS_VERIFIED → NEW → PLANNED → SPEC_READY → PIPELINES_COMPLETE → DOCUMENTED → [KNOWLEDGE_EXTRACTED] → REVIEW_PASSED → READY_TO_SHIP → DONE，共 10 个命名状态、其中 9 个为核心状态）与 3 个中断态（HOLD/BLOCKED/STOPPED）。
- "Hard Enforcement: State Transition Preconditions" 表给出 **18 行前提条件**，覆盖除入口状态 NEW 外的全部 9 个目标状态（如 SPEC_READY 需 comprehension.md+spec.md+test-spec.md 且 planner 已派发；PIPELINES_COMPLETE 需 implementation.md+audit.md 且隔离已核验等），并写明"先读当前状态、核验全部前提、再写 status.md"的执行规程。
- leader.md 明确"Gate state transitions on artifact existence and preconditions"。
- **论文引用**：Section 2.1 "enforces a state machine with mandatory preconditions at each transition"；2.1 末 "progresses through nine states… with hard gates at each transition"；附录 A.2 "governed by a state machine with mandatory preconditions enforced as hard gates at each transition… No state can be skipped."
- 计数口径注：论文称"nine states"，仓库含 10 个命名状态（多出的 KNOWLEDGE_EXTRACTED 为可选，brain mode 才进入）；剔除该可选态后恰好 9 个核心状态，与论文"nine states"一致。
- 判定：**supported**（顺序门 + 前提条件机制完整实现；状态计数的细微差异已在口径中说明）。

---

## 4. 汇总

| 声明 | 判定 | 一句话依据 |
|---|---|---|
| C01 多代理 + 信息屏障 | **supported** | 9 个代理定义；10/10 显式隔离检查 + 7/7 流水线规则 + Leader 派发规则 |
| C02 八个专门代理、单会话 | **partially_supported** | 论文描述 8 代理（附录 A1 全匹配、单会话成立），但实现含 9 个代理文件（distiller 可选 brain-mode） |
| C03 规划代理产出独立规范 | **supported** | planner 产出三规范且"独立自足"；三派发路径均隔离（运行产物不在冻结数据内） |
| C04 顺序门 + 强制前提 | **supported** | 18 行前提条件表覆盖 9 个目标状态；"No state can be skipped" |

## 5. 局限

- 冻结数据不含 workspace 运行目录，C03 的运行期规范产物（spec.md 等）无法直接核验，仅验证代码层面的强制机制。
- C02 的"八个"为论文口径；实现为九文件。判定采用部分支持，避免掩盖计数差异。
- 数值佐证来自复现工作区冻结 CSV，非论文原表；论文表 1 的数值仅在"C01–C04 无关紧要"的意义上作为背景提及，不用于判定。
