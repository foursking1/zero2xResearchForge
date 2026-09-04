# EVAL REPORT v7: 2604.04681v1

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 62.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 15.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **42.0** | 60 | A1: 12分。完整交付了TASK.md要求的所有核心产物，包括solution.md、可运行代码、evidence_table.csv和metrics.json，机器可读结果齐全。A2: 15分。受partially_supported结论硬上限约束（A2≤15）。Agent在CIFAR10/100上复现了C02，但PAPER_ANCHOR中带有具体数值的核心锚点（ImageNet、COCO、FID等）均未验证，且PSD机制复现与论文矛盾。A3: 15分。方法极其严谨，诚实记录了PSD和Alpha的复现矛盾，未掩盖负面结果，代码和证据链完全可复算。 |
| B 真值一致性/可验证性 | 20.0 | 40 | truth_check=diverged | agent数 vs 锚点逐项比对：
1. R07/R08/R09 (ImageNet-1K ResNet18/ViT/Vim 准确率锚点 70.0/78.0/75.0)：agent 未复现，无对应数字 → unverified。
2. R03 (COCO CIDEr 锚点 45.6)、R13-R15 (FID 锚点 10.0/12.0/8.0)：agent 未复现 → unverified。
3. R29/R30 (Overhead 锚点 0.015/0.02)：agent 未提供与 base method 对比的 overhead 秒数 → unverified。
4. R21/R22 (PSD 频率分离，论文声称噪声>信号)：agent 报出 psd_signal_ratio=0.646, psd_noise_ratio=0.354, psd_r22_pass=False → 与论文真值明确矛盾 (diverged)。
5. CIFAR10/100 准确率：agent 报出 95.34/79.77 等，但 PAPER_ANCHOR 中 R04-R06 目标值为 '—'，无具体锚点数值可比对。
综合：核心数值锚点均未验证，PSD 机制验证偏离，truth_check 判定为 diverged。 |

## A 核心结果达成度（42.0/60 = A1 12.0 + A2 15.0 + A3 15.0）

A1: 12分。完整交付了TASK.md要求的所有核心产物，包括solution.md、可运行代码、evidence_table.csv和metrics.json，机器可读结果齐全。A2: 15分。受partially_supported结论硬上限约束（A2≤15）。Agent在CIFAR10/100上复现了C02，但PAPER_ANCHOR中带有具体数值的核心锚点（ImageNet、COCO、FID等）均未验证，且PSD机制复现与论文矛盾。A3: 15分。方法极其严谨，诚实记录了PSD和Alpha的复现矛盾，未掩盖负面结果，代码和证据链完全可复算。

## B 真值一致性/可验证性（20.0/40）[truth_check=diverged]

agent数 vs 锚点逐项比对：
1. R07/R08/R09 (ImageNet-1K ResNet18/ViT/Vim 准确率锚点 70.0/78.0/75.0)：agent 未复现，无对应数字 → unverified。
2. R03 (COCO CIDEr 锚点 45.6)、R13-R15 (FID 锚点 10.0/12.0/8.0)：agent 未复现 → unverified。
3. R29/R30 (Overhead 锚点 0.015/0.02)：agent 未提供与 base method 对比的 overhead 秒数 → unverified。
4. R21/R22 (PSD 频率分离，论文声称噪声>信号)：agent 报出 psd_signal_ratio=0.646, psd_noise_ratio=0.354, psd_r22_pass=False → 与论文真值明确矛盾 (diverged)。
5. CIFAR10/100 准确率：agent 报出 95.34/79.77 等，但 PAPER_ANCHOR 中 R04-R06 目标值为 '—'，无具体锚点数值可比对。
综合：核心数值锚点均未验证，PSD 机制验证偏离，truth_check 判定为 diverged。

## 证据与重算说明

独立重算未执行（基于磁盘证据扫描判定）。关键实测数：CIFAR10 BLS-InfoBatch 30% 准确率 95.34，CIFAR100 79.77；PSD 分析 signal_ratio=0.646 > noise_ratio=0.354（与论文 Figure 2 矛盾）。证据等级为 2，有详尽的机器可读数字，但缺乏对 PAPER_ANCHOR 核心数值锚点的覆盖。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 实验设计严谨，诚实且透明地记录了所有复现结果，包括与论文理论机制（PSD、Alpha）相矛盾的证据，未做任何掩盖或数据编造，证据链极其完整。
- 不足: 受限于冻结数据范围，未能验证 PAPER_ANCHOR 中带有具体数值的大规模数据集和多任务核心锚点，导致真值比对层面大量 unverified，且核心理论机制（频率分离）在复现中未能成立。