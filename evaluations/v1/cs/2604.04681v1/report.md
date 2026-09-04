# EVAL REPORT: 2604.04681v1（BLS 批量损失分数数据剪枝）

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: WorkBuddy（LLM 裁判）
- 评测时间: 2026-08-13

## 总分: 55 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---|---|---|
| A 核心结果达成度 | 25 | 60 | 30% 剪枝快速验证：BLS-InfoBatch 精度与 full 持平（33.45 vs 33.70）；但仅 n_train=2000/10 epochs 子集，非论文全量训练，多数锚无法对齐 |
| B 证据真实性 | 25 | 25 | 训练结果全部实跑（3 seeds 存档）；JSON 含完整配置可复现；无编造 |
| C 方法与报告 | 5 | 15 | 无 solution.md 汇总、无 evidence 表、无结论判定——补跑未完成收尾 |

## A 核心结果达成度（25/60）

**关键背景**：论文为大规模数据剪枝基准（CIFAR10/100 全量 + ResNet18 全 epoch 训练）。agent 用 **n_train=2000 子集 + 10 epochs** 快速验证（CPU 环境限制）。

| 规则 | 锚 | agent 值（30% 剪枝） | 判定 |
|---|---|---|---|
| R04 BLS-InfoBatch CIFAR10@30% | 与 full 统计等价 | full 33.70 vs BLS-IB 33.45（seed0）/ 36.10（seed1）| ⚠️ 方向成立（持平/略优）但子集规模无统计效力 |
| R05 BLS-SeTa CIFAR100@50% | 统计等价 | 未跑（仅 30% 有数据）| ❌ 缺失 |
| R07 ResNet18 70% | ~70% acc | 子集上仅 30%+ 水平 | ❌ 规模不符 |
| R02 MJ+ST 平价 | trend | 未验证 | ❌ |

→ 仅 R04 的方向性验证（剪枝后精度保持）成立，其余因训练规模限制无法对齐锚。约 25/60。

## B 证据真实性（25/25）

- 训练结果真实：cifar10/cifar100 × full/BLS-InfoBatch/BLS-SeTa/InfoBatch/SeTa × 3 seeds，JSON 含完整配置（alpha=0.7、batch 64、n_train 2000）
- 10 epochs 曲线完整（valid_acc 数组逐 epoch）；run_all.log 记录执行
- 无编造、配置透明——扣分只在 A（规模）和 C（报告缺失）

## C 方法与报告（5/15）

- C1 方法（3/5）：BLS 剪枝流程正确接入官方 repo（F:/dataset/2604.04681v1/code/BLS），多方法对照（full vs BLS vs InfoBatch vs SeTa）
- C2 稳健性（2/5）：3 seeds 存档 ✓；但无统计检验
- C3 报告（0/5）：**无 solution.md、无 evidence 表、无结论**——补跑被中断在收尾

## 结论

- **科学结论**：`partially_supported`（仅方向性）——BLS-InfoBatch 在 30% 剪枝下精度保持 full 水平（33.45 vs 33.70），与论文"剪枝不损精度"声称方向一致；但训练规模（2000 样本/10 epoch）远小于论文，无法构成统计级验证
- 重型训练任务（2.2GB 数据），CPU 环境下 agent 只能做缩规模验证，且补跑未完成报告收尾
- 备注：若需完整评测，需 GPU 环境跑全量训练（本机 CPU 不可行）
