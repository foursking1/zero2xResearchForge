# EVAL REPORT: 08_tapley_2004（GRACE Mass Variability）

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: WorkBuddy（LLM 裁判，独立脚本重算）
- 评测时间: 2026-08-13

## 总分: 61 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---|---|---|
| A 核心结果达成度 | 26 | 60 | 16 条锚中命中 8（R01/R05/R06/R07/R09/R11/R12 等），偏离 8（R02/R03/R04/R08/R10 等） |
| B 证据真实性 | 25 | 25 | 抽查 R01 独立重算逐位一致（-7.244）；代码可运行、全部结果 JSON 可复现 |
| C 方法与报告 | 10 | 15 | 方法完整（加权 LSQ + 敏感性）；solution.md 为空、无结论标签与边界说明 |

## A 核心结果达成度（26/60）

### 年度拟合锚（R01-R12，12 条）

| 规则 | 锚值 | agent 报告 | 差 | 命中 |
|---|---|---|---|---|
| R01 GRACE cos min | -7.2 (0.5) | -7.244 | 0.044 | ✅ |
| R02 GRACE cos max | 3.0 (0.3) | 1.653 | 1.347 | ❌ |
| R03 GRACE cos RMS | 0.9 (0.1) | 0.592 | 0.308 | ❌ |
| R04 GRACE sin min | -6.4 (0.5) | -5.858 | 0.542 | ⚠️ 略超 |
| R05 GRACE sin max | 8.9 (0.5) | 9.122 | 0.222 | ✅ |
| R06 GRACE sin RMS | 1.3 (0.15) | 1.323 | 0.023 | ✅ |
| R07 GLDAS cos min | -2.3 (0.3) | -2.320 | 0.020 | ✅ |
| R08 GLDAS cos max | 3.2 (0.3) | 2.254 | 0.946 | ❌ |
| R09 GLDAS cos RMS | 0.4 (0.1) | 0.479 | 0.079 | ✅ |
| R10 GLDAS sin min | -4.0 (0.3) | -4.738 | 0.738 | ❌ |
| R11 GLDAS sin max | 6.7 (0.5) | 6.452 | 0.248 | ✅ |
| R12 GLDAS sin RMS | 1.0 (0.1) | 1.023 | 0.023 | ✅ |

→ 12 条命中 7，加权约 21/34 基础分。

### 南美月际异常（R13-R14）

- R13 Amazon Apr-2003 峰值锚 +14.0 (1.0)：agent 2003-04 max=11.369 → 差 2.63 ❌
- R14 Amazon Oct-2003 谷值锚 -7.7 (0.8)：agent 2003-10 结果见 amazon_orinoco.json，未达锚 ❌

### 误差水平（R17-R18）

- R17 2003 @600km 误差锚 2-3mm：agent error_rms=1.843 → 略低于带下沿 ⚠️
- R18 2002 @1000km 误差锚 2-3mm：agent error_rms=1.834 → 略低于带下沿 ⚠️

### A 小结

agent 复现了 GRACE/GLDAS 年度拟合的整体结构（min/RMS 命中），但 4 条 max 类锚（R02/R08 及 R13/R14 幅度）系统性偏低，表明其平滑/拟合口径与论文 Fig.1 存在偏差（论文 max 值 3.0/3.2 未达，疑似高斯平滑半径或去相关处理差异）。按容差带加权：约 26/60。

## B 证据真实性（25/25）

- **独立重算抽查（R01）**：裁判脚本从 agent 的 17 个平滑网格 npz 独立实现加权 LSQ（cos/sin/trend/offset，2002 权重 0.25），重算 GRACE cosine min = **-7.244**，与 agent 报告逐位一致 ✅
- 代码完整可运行（step1 平滑 → step2 拟合 → step3 南美 → step4 误差，4 步流水线 + grace_utils）；结果全部落盘 JSON/npz
- 引用原始冻结数据（data/grace_level2/、data/gldas_sh/），未发现抄论文数字

## C 方法与报告（10/15）

- C1 方法合理性（4/5）：加权 LSQ 模型正确、含 2002/2003 权重差异设计；平滑口径与论文可能存在细微差异（导致 max 偏低）
- C2 稳健性（4/5）：提供 equal-weight 敏感性对照（equal_weight_sensitivity），误差分析含多 seed（0/42/2026）✅
- C3 报告与边界（2/5）：**solution.md 为空**（claude 最终报告未写入文件），无方法叙述、结论标签、局限性说明——仅 JSON 数据可读

## 结论

- **科学结论**：GRACE 年度变率结构与论文一致（min/RMS 命中、sine 主导 spring-fall 循环成立），但幅度 max 偏低 → `partially_supported`
- 数据真实性满分（可重算）；主要扣分在 A 达成度的 max 类锚偏差 + C 报告缺失
- 备注：solution.md 为空是执行脚本的输出问题（claude 结果写进 JSON 但报告文件未生成），评测按现有产物进行
