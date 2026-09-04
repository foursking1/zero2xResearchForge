# EVAL REPORT v5: 2604.04681v1

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 70.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 15.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **42.0** | 60 | A1: 12分。完整交付了TASK.md要求的所有核心产物，包括solution.md、可运行代码、evidence_table和metrics.json，无缺失。A2: 15分。Agent在可用数据（CIFAR10/100）上完美复现了C02的准确率claim（与论文差异<1.5pp），但论文的核心理论机制（PSD频率分离、Alpha超参）在复现中被明确contradict（signal>noise, alpha=0.9最优），且C01/C04因客观数据缺失无法验证。整体科学结论判定为partially_supported，受硬上限约束给15分。A3: 15分。方法极其严谨，明确区分了全规模复现与低资源CPU对比，诚实记录了PSD和Alpha的复现矛盾，无数据泄漏，代码和证据链完全可复算。 |
| B 证据真实性/实际复现 | 28.0 | 40 | 28分。证据等级为2（齐全自洽），提供了详尽的metrics.json、evidence_table以及逐epoch的训练曲线、配对统计检验p值等底层证据。但受限于partially_supported结论的硬上限，B维度最高给28分。 |

## A 核心结果达成度（42.0/60 = A1 12.0 + A2 15.0 + A3 15.0）

A1: 12分。完整交付了TASK.md要求的所有核心产物，包括solution.md、可运行代码、evidence_table和metrics.json，无缺失。A2: 15分。Agent在可用数据（CIFAR10/100）上完美复现了C02的准确率claim（与论文差异<1.5pp），但论文的核心理论机制（PSD频率分离、Alpha超参）在复现中被明确contradict（signal>noise, alpha=0.9最优），且C01/C04因客观数据缺失无法验证。整体科学结论判定为partially_supported，受硬上限约束给15分。A3: 15分。方法极其严谨，明确区分了全规模复现与低资源CPU对比，诚实记录了PSD和Alpha的复现矛盾，无数据泄漏，代码和证据链完全可复算。

## B 证据真实性/实际复现（28.0/40）

28分。证据等级为2（齐全自洽），提供了详尽的metrics.json、evidence_table以及逐epoch的训练曲线、配对统计检验p值等底层证据。但受限于partially_supported结论的硬上限，B维度最高给28分。

## 证据与重算说明

独立重算未执行（基于磁盘证据扫描判定）。关键实测数：CIFAR10 BLS-InfoBatch 30%准确率95.34（论文95.6），CIFAR100 BLS-InfoBatch 30%准确率79.77（论文78.4），PSD分析显示signal_ratio=0.646 > noise_ratio=0.354（与论文Figure 2矛盾）。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 实验设计极其严谨，诚实且透明地记录了所有复现结果，包括与论文理论机制（PSD、Alpha）相矛盾的证据，未做任何掩盖或数据编造，证据链极其完整。
- 不足: 受限于冻结数据范围，未能验证大规模数据集和多任务claim；论文的核心理论机制（频率分离）在复现中未能成立，导致整体结论只能为部分支持。