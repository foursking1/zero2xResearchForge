# PAPER_ANCHOR（私有）：2604.04898v1

> 论文：QED-Nano: Teaching a Tiny Model to Prove Hard Theorems
> 出处：arXiv:2604.04898v1, April 2026
> 本文件为 LLM 裁判判分锚点（指标 + 数值 + 出处 + 容差），**只给裁判看，不给执行 agent 看**。

## 核心结果锚（来自官方 truth 的 verification rules）

共 21 条规则；以下按 claim 分组列出可数值化的锚（numeric/compare/trend）。

### C01（numeric）QED-Nano (4B) achieves 40.0% on IMO-ProofBench, 44.9% on ProofBench, and 67.5% o

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R01 | numeric | QED-Nano without scaffold achieves 40.0% avg@3 grade on IMO- | 40.0 | abs 0.0 / 5.0% |
| R02 | numeric | QED-Nano without scaffold achieves 44.9% avg@3 grade on Proo | 44.9 | abs 0.0 / 5.0% |
| R03 | numeric | QED-Nano without scaffold achieves 67.5% avg@3 grade on IMO- | 67.5 | abs 0.0 / 5.0% |

### C02（numeric）QED-Nano with RSA test-time scaffold achieves 56.9% on IMO-ProofBench, 62.6% on 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R04 | numeric | QED-Nano with RSA scaffold achieves 56.9% avg@3 grade on IMO | 56.9 | abs 0.0 / 5.0% |
| R05 | numeric | QED-Nano with RSA scaffold achieves 62.6% avg@3 grade on Pro | 62.6 | abs 0.0 / 5.0% |
| R06 | numeric | QED-Nano with RSA scaffold achieves 76.5% avg@3 grade on IMO | 76.5 | abs 0.0 / 5.0% |

### C03（numeric）Comparison of test-time scaffolds (Single Turn, RC, DSM, RSA) on IMO-ProofBench 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R07 | numeric | RSA scaffold achieves 56.9% on IMO-ProofBench, highest among | 56.9 | abs 0.0 / 5.0% |
| R08 | trend | Scaffold average token usage ordering: Single Turn (93,690)  | — | abs — / —% |

### C04（figure）RL training with rubric-based rewards shows increasing training reward and corre

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R09 | figure | Figure 3: RL training reward increases monotonically over ~3 | — | abs — / —% |

### C05（figure）RL with Reasoning Cache shows improved training stability and convergence speed 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R10 | figure | Figure 4: RC training curve is smoother, converges faster, a | — | abs — / —% |

### C06（trend）RC-trained checkpoint outperforms RL-trained checkpoint at every RC turn during 

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R11 | trend | RC-trained model grade > RL-trained model grade at every tur | — | abs — / —% |
| R12 | trend | The performance gap between RC-trained and RL-trained models | — | abs — / —% |

### C07（numeric）QED-Nano-SFT achieves 39.5% on IMO-ProofBench, 33.3% on ProofBench, 57.5% on IMO

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R13 | numeric | QED-Nano-SFT (SFT only) achieves 39.5% avg@3 grade on IMO-Pr | 39.5 | abs 0.0 / 5.0% |
| R14 | numeric | QED-Nano-SFT (SFT only) achieves 33.3% avg@3 grade on ProofB | 33.3 | abs 0.0 / 5.0% |
| R15 | numeric | QED-Nano-SFT (SFT only) achieves 57.5% avg@3 grade on IMO-An | 57.5 | abs 0.0 / 5.0% |
| R16 | trend | QED-Nano-SFT substantially exceeds Qwen3-4B-Thinking baselin | — | abs — / —% |

### C08（trend）Training on unique problems (4,300) achieves higher final IMO-ProofBench perform

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R17 | trend | Training on unique problems (4,300) achieves higher final IM | — | abs — / —% |

### C09（numeric）SFT ablation: Qwen3-4B Thinking-2507 with LR 3e-5 achieves best ProofBench score

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R18 | numeric | Qwen3-4B Thinking-2507 with LR 3e-5 achieves best ProofBench | 2.85 | abs 0.0 / 5.0% |
| R19 | trend | Qwen3-4B Thinking-2507 LR 3e-5 ProofBench score (2.85) is hi | — | abs — / —% |

### C10（numeric）GPT-OSS-20B with medium reasoning and ProofBench Strict prompt achieves best gra

| 规则 | 类型 | 描述 | 目标值 | 容差 |
|---|---|---|---|---|
| R20 | numeric | ProofBench Strict prompt achieves grader accuracy of 1.21 (l | 1.21 | abs 0.0 / 5.0% |
| R21 | trend | ProofBench Strict (1.21) has lowest grader accuracy error, o | — | abs — / —% |
