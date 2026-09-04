# PAPER_ANCHOR（私有）：2604.04895v1

> 论文：Agentic Federated Learning: The Future of Distributed Training Orchestration
> 出处：ICLR 2026 Workshop on AI for Mechanism Design and Strategic Decision Making
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 16 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（numeric）K-Agent using different LLMs and prompt techniques achieves comparable accuracy 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | numeric | K-Agent with CoT+Qwen3 8b on CIFAR-10 should achieve distrib | 0.0 | abs 0.0 / 15.0% |
| R02 | numeric | K-Agent with CoT+Qwen3 8b on MNIST should achieve distribute | 0.0 | abs 0.0 / 15.0% |
| R15 | exists | Aggregated Table 1 results must exist with mean +/- std for  | — | abs — / —% |

### C02（figure）K-Agent dynamically adapts its K value across communication rounds, demonstratin

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R03 | figure | Figure 3: Accuracy convergence curve for CoT+Qwen3 8b on CIF | — | abs — / —% |
| R04 | trend | The K value chosen by K-Agent should vary across communicati | — | abs — / —% |

### C03（trend）Raw LLM (gpt-4o-mini) client selection achieves better accuracy than ReAct ToolA

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R05 | trend | Raw LLM accuracy should exceed ToolAgent accuracy, which sho | — | abs — / —% |
| R16 | exists | Token usage data must include completion tokens, prompt toke | — | abs — / —% |

### C04（trend）ToolAgent shows better token scalability than raw LLM as client count increases,

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R06 | trend | At 50 clients, total token cost for LLM should exceed total  | — | abs — / —% |
| R07 | trend | LLM token cost growth from 5 to 50 clients should be greater | — | abs — / —% |

### C05（exists）K-Agent framework implements Plan, Memory, and Action modules for autonomous cli

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R10 | exists | K-Agent repository must contain Plan, Memory, and Action mod | — | abs — / —% |

### C06（numeric）FL experiments use Dirichlet distribution with alpha=0.1 for Non-IID data partit

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R08 | numeric | Data partitioning should use Dirichlet distribution with con | 0.1 | abs 0.01 / 0.0% |
| R09 | numeric | Experiments should use 25 clients for the main Non-IID feder | 25 | abs 0 / 0.0% |

### C07（exists）Chain-of-Thought prompting is evaluated alongside Description Only and Few-Shot 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R11 | exists | Repository must contain distinct prompt implementations for  | — | abs — / —% |

### C08（exists）Each experimental configuration is run 3 times with results reported as mean +/-

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R12 | exists | Results must include data from 3 independent runs per config |  | abs — / —% |

### C09（exists）ReAct ToolAgent uses tools (filter, get_stats, get_info_by_cid) to interact with

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R13 | exists | ToolAgent implementation must define the filter, get_stats,  | — | abs — / —% |

### C10（exists）Client-side agents dynamically manage privacy budgets and adapt model complexity

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R14 | exists | Repository or paper text should describe client-side agent r | — | abs — / —% |
