# PAPER_ANCHOR（私有）：2604.04871v1

> 论文：StatsClaw: An AI-Collaborative Workflow for Statistical Software Development
> 出处：arXiv preprint
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 19 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（exists）StatsClaw is a multi-agent architecture that enforces information barriers betwe

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R02 | exists | Agent prompt or configuration files must exist for each of t | — | abs — / —% |
| R13 | exists | Builder specification document (spec.md) must NOT contain si | — | abs — / —% |
| R14 | exists | Simulator specification document (sim-spec.md) must NOT cont | — | abs — / —% |
| R15 | exists | Tester specification document (test-spec.md) must define det | — | abs — / —% |

### C02（numeric）StatsClaw orchestrates eight specialized agents within a single Claude Code sess

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | numeric | StatsClaw defines exactly 8 primary specialized agent roles: | 8 | abs 0 / 0% |

### C03（exists）The planning agent produces independent specification documents dispatched to se

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R03 | exists | The planner must produce three isolated specification docume | — | abs — / —% |
| R04 | exists | Each specification document must be self-contained: spec.md  | — | abs — / —% |

### C04（numeric）StatsClaw implements a state machine enforcing sequential gates with mandatory p

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R05 | numeric | The state machine defines 13 states: initialize, plan, execu | 13 | abs 0 / 0% |
| R06 | exists | State machine configuration or code defining workflow transi | — | abs — / —% |
| R19 | trend | The workflow enforces sequential gate ordering: plan must co | — | abs — / —% |

### C05（numeric）StatsClaw supports ten distinct workflow patterns from simple bug fixes to green

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R07 | numeric | StatsClaw supports exactly 10 workflow patterns: paper2featu | 10 | abs 0 / 0% |
| R08 | exists | Configuration or documentation listing all 10 supported work | — | abs — / —% |

### C06（exists）StatsClaw was demonstrated end-to-end on a probit estimation package producing a

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R09 | exists | The probit estimation case study must produce standard R pac | — | abs — / —% |
| R10 | exists | The probit package must contain R source files implementing  | — | abs — / —% |

### C07（trend）StatsClaw was evaluated across three applications of increasing complexity

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R11 | trend | StatsClaw was evaluated on three applications of increasing  | — | abs — / —% |
| R12 | exists | Distinct evaluation artifacts must exist for each of the thr | — | abs — / —% |

### C10（exists）The reviewer cross-compares all pipeline outputs before issuing a ship verdict

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R16 | exists | Reviewer agent prompt and review.md template must show cross | — | abs — / —% |
| R17 | exists | Review output (review.md) must contain cross-references betw | — | abs — / —% |
