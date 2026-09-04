# EVAL REPORT: 2604.04673v1（Minimaxity and Admissibility of Bayesian Neural Networks）

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: WorkBuddy（LLM 裁判，独立脚本重算）
- 评测时间: 2026-08-13

## 总分: 88 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---|---|---|
| A 核心结果达成度 | 49 | 60 | 10 条数值/比较锚中 9 条命中（R14 Horseshoe k=100≈130 未达，agent 全新 run 157 vs 容差带 110.5–149.5）；C03 fixed@p=100 超幅处于 MC 边缘 |
| B 证据真实性 | 24 | 25 | 独立重算 MLE=p、BetaPrime max、Horseshoe k 曲线逐位一致；全新全量 run 产物内部自洽；1 处小瑕疵（冻结早期 run 含 BetaPrime=2496 异常值未披露） |
| C 方法与报告 | 15 | 15 | 方法严格对齐论文 §5.1/§5.2、多 seed+高精度复算、边界诚实完整 |

## A 核心结果达成度（49/60）

### C07 MLE risk = p（R01-R03，3 条 numeric）

| 规则 | 锚值 | agent 报告 | 独立重算 | 命中 |
|---|---|---|---|---|
| R01 MLE p=5 | 5.0 (0.5) | 5.0 | 5.0（全部 r 点精确） | ✅ |
| R02 MLE p=50 | 50.0 (5.0) | 50.0 | 50.0（全部 r 点精确） | ✅ |
| R03 MLE p=100 | 100.0 (10.0) | 100.0 | 100.0（全部 r 点精确） | ✅ |

### C01/C02/C03 径向风险（R04-R09）

| 规则 | 锚值 | agent 冻结 | agent 全新 run | 独立重算（冻结） | 命中 |
|---|---|---|---|---|---|
| R07 BetaPrime max p=5 | ≈5.0 (10%) | 5.0016 | 4.994 | 5.0016 | ✅ |
| R08 BetaPrime max p=50 | ≈50.0 (10%) | 50.032 | 50.025 | 50.032 | ✅ |
| R09 BetaPrime max p=100 | ≈100.0 (10%) | 100.026 | 100.017 | 100.026 | ✅ |
| R04 p=5 fixed>minimax | trend | 5.0315>5 | max 5.388, 476/501 点超 | 5.0315>5 | ✅ |
| R05 p=50 fixed/dropout>minimax | trend | (r 覆盖不足) | fixed 50.074 / dropout 50.127 | 冻结 r≤17 未达 | ✅（全新 run） |
| R06 p=100 fixed>minimax | trend | (r 覆盖不足) | 主协议 max 99.993 未超；高精度 r=500 100.024、5-seed 均值 100.016 | — | ⚠️ 边缘 |

- C03 判定说明：fixed@p=100 在主协议（N_mc=50k 单 seed）下 max=99.993 恰低于 p；但高精度复算（N_mc=200k, K_dir=30）r=500 处 100.024（≈5 SE）、5-seed 均值 100.016，超幅仅 ~0.02%，处于 MC 分辨率边缘。agent 判 partially_supported 且如实说明，合理。

### C04/C05/C06 稀疏度风险（R10-R16）

| 规则 | 锚值 | agent 报告 | 独立重算（冻结 sparsity json） | 命中 |
|---|---|---|---|---|
| R15 BetaPrime p=5 仅依赖 \|\|θ\|\| 且≈p | trend | 单条曲线 max 5.10 | betaprime_risk max 5.100 | ✅ |
| R11/R12/R13 Horseshoe 随 k 强变化 | trend | k=1 max 2.79–2.92；k=5 max 5.25–9.09；p=50/100 dense vs sparse 比值 12.5×/23.6× | k=1 max 2.922、k=5 max 5.255（冻结 v2） | ✅ |
| R16 Horseshoe max p=100 > 100 | 100.0 (0) | k=100 max 157.1 > 100 | — | ✅ |
| R14 Horseshoe k=100 p=100 ≈ 130 | 130.0 (15%) | 全新减采样 run max 157.1 | — | ❌ 超容差（+20.9%） |

- R14 未命中说明：agent 全新 run（10 draws×5 dirs 减采样）得 157.1，超出容差带 [110.5, 149.5]；论文自报 ~130。方向（密集 k=p 远高于 minimax）一致，数值偏高源于 Horseshoe MC 样本过少，agent 已在局限中声明。扣除该条权重分。

### A 小结

10 条关键锚 9 条命中（含 3 条 MLE 精确锚 + 3 条 BetaPrime 锚 + 2 条 fixed 超 minimax + Horseshoe 变化趋势）；2 条边缘/未达（R06 p=100 超幅 MC 边缘、R14 数值超容差）。按权重折合约 49/60。

## B 证据真实性（24/25）

**独立重算抽查（裁判脚本 judge_check_04673.py，从冻结数据重算）：**

| 抽查项 | agent 报告 | 裁判重算 | 一致 |
|---|---|---|---|
| MLE risk p=5/50/100 | 5.0 / 50.0 / 100.0 | 5.0 / 50.0 / 100.0（全部 r 点恒定） | ✅ |
| BetaPrime max p=5（冻结） | 5.0016 | 5.0016（r≤200 run） | ✅ |
| BetaPrime max p=50（冻结） | 50.032 | 50.032（r≤17 run） | ✅ |
| BetaPrime max p=100（冻结） | 100.026 | 100.026（r≤25 run） | ✅ |
| Fixed BNN max p=5 冻结 | 5.0315 | 5.0315（172/201 点超 p） | ✅ |
| Horseshoe k=1/k=5 max（冻结） | 2.922 / 5.255 | 2.922 / 5.255（sparsity_p5_fixed_hs_v2.json） | ✅ |

**全新 run 产物内部自洽核查：**
- `radial_risk_p5_full.json`（501 点 r=0..500）：MLE 恒 5.0、fixed max 5.3877、bp max 4.994、dropout max 6.608、476/501 点超 p —— 与 solution.md 完全一致
- `se_check.json`：5 个独立 seed 的原始 replicate 值完整可查，mean/SE/z 值与报告一致
- `betaprime_shrinkage_verify.json`：a(0)=0.25/0.020408/0.010101 = 1/(p−1) 精确，单调/有界验证通过
- `highprecision_check.json`：p50 r=500 fixed 50.1107、p100 r=500 fixed 100.0240 与报告一致

**小瑕疵（扣 1 分）**：冻结数据中存在早期 run（radial_p5_20260416_121859.json，r≤50）含 BetaPrime max=2496 的明显 MC 未收敛异常值，agent 选用了 r≤200 的覆盖更全 run 作冻结参照（合理），但报告未披露该异常 run 的存在。不影响结论，记为轻微透明性不足。

## C 方法与报告（15/15）

- C1 方法合理性（5/5）：严格按论文 §5.1/§5.2 口径（d=3 网络、M_v=200k、N_mc=50k、K_dir=10、收缩网格 2500 点、Horseshoe Gibbs 3000/1000/thin2）；直接 import 冻结源码 `src.*` 重跑全新全量实验，无泄漏、步骤完整可复现
- C2 不确定性/稳健性（5/5）：5-seed 标准误复测（r=500）、N_mc=200k/K_dir=30 高精度复算、收缩函数 M_v 敏感性（200k vs 2M）、减采样稀疏度对照——覆盖充分
- C3 边界与结论（5/5）：明确披露重要性采样 ESS 崩溃（低至 1e-6）、Horseshoe MC 误差、冻结数据 r 覆盖不足、p=100 超幅处于分辨率边缘；结论分档（supported/partially_supported）有数据支撑、不夸大

## 结论

- **科学结论**：C01/C02/C04/C05/C07 **supported**；C03 **partially_supported**（fixed@p=100 超幅 ~0.02% 处于 MC 边缘，agent 处理诚实且正确）；C06 partially（Horseshoe 方向正确但 k=100 数值 157 vs 论文 130 超容差）
- 证据真实性接近满分：冻结数据重算逐位一致、全新 run 产物内部自洽、稳健性实验完整
- 备注：这是目前评测中方法最扎实的一篇——不仅分析冻结数据，还实际重跑了完整实验并做了多级稳健性验证；主要扣分在 R14 数值超容差与 C03 的固有边缘性
