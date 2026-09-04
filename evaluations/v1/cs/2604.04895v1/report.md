# EVAL REPORT: 2604.04895v1（Agentic Federated Learning: Distributed Training Orchestration）

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: WorkBuddy（LLM 裁判，独立脚本重算）
- 评测时间: 2026-08-13

## 总分: 84 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---|---|---|
| A 核心结果达成度 | 46 | 60 | 4 条 numeric 锚全部达成；C01/C02/C04 支持或基本支持；C03 因冻结数据缺失 + 论文内部矛盾判 inconclusive（诚实） |
| B 证据真实性 | 25 | 25 | 独立重算 C01（accuracy 均值/范围/2pp 内占比）与 C02（k_std>0 比例/静态配置数/k_std 均值/k_medio 范围）全部逐位一致；R08 冻结配置确认 alpha=0.1 |
| C 方法与报告 | 13 | 15 | provenance 标注体系优秀（computed vs PAPER-CITED 分明）；solution.md 完整；扣 2 分：无多 seed 敏感性（受冻结数据限制） |

## A 核心结果达成度（46/60）

PAPER_ANCHOR 共 16 条规则：4 条 numeric/compare + 1 条 figure + 6 条 trend + 5 条 exists。

| 规则 | 锚 | agent 结果 | 判定 |
|---|---|---|---|
| R01（numeric）| CoT+Qwen3 8b CIFAR-10 可比 accuracy（目标 0.0，容差 15%）| CoT+qwen3:8b acc=0.3925（冻结 CSV）；30 配置均值 0.3782±0.0137、范围 4.61pp、90% 在均值 ±2pp 内；prompt 间 ANOVA p=0.55 | ✅ 支持（"不同 LLM/提示可比"成立）|
| R02（numeric）| 同上 MNIST | 论文 Table 1 MNIST 半：均值 96.46%、范围 2.2pp（PAPER-CITED）| ✅ 方向一致（仅引用，不可独立复核）|
| R08（numeric）| Dirichlet alpha = 0.1（abs 0.01）| 冻结 run_reproduction.py 全部 5 处 + pyproject.toml 均为 dirichlet-alpha=0.1 | ✅ 精确命中 |
| R09（numeric）| 主实验 25 clients（abs 0）| K-Agent 官方 CSV 与论文 Table 1（25 clients/50 rounds 口径）逐值核对一致；本地复现仅 5 clients smoke（明确标注非论文规模）| ✅ 间接支持（论文实验规模）|
| R04（trend）C02 K 动态调整 | K 跨轮变化 | k_std>0 占 86.7%（26/30），k_std 均值 3.17/中位数 2.45，4 个静态 K 配置与论文叙述吻合 | ✅ 支持 |
| R05（trend）C03 raw LLM > ToolAgent | — | 冻结无机器可读数据；论文 Table 2 显示 10 clients 处 ToolAgent(0.786) > LLM(0.694)，与 Figure 4 叙述矛盾 → inconclusive | ⚠️ 诚实 inconclusive |
| R06/R07（trend）C04 token 可扩展性 | 50 clients LLM cost > Tool；增长 LLM > Tool | 论文 Table 2（PAPER-CITED）：token 增长 LLM ×6.53 vs Tool ×1.16；50 clients 处 LLM $0.001593 > Tool $0.000961 | ✅ 支持（仅引用）|
| R03/R10-R16（figure/exists）| — | C02 figure/上下文性、repository 模块、3 次运行、token 明细等：冻结集均无机器可读产物，如实标注 | — 无法验证（非 agent 过错）|

→ 4 条 numeric 全命中；C01/C02/C04 核心叙事获数据支持；C03 判 inconclusive 非 agent 过错（论文自身 Table 2 vs Figure 4 矛盾）。按权重约 46/60。

## B 证据真实性（25/25）

- **独立重算抽查（C01 + C02）**：裁判脚本直接解析冻结 `k_agent.csv`（30 配置）：accuracy 均值 0.3782、范围 0.0461、±2pp 内占比 0.900、k_std>0 比例 0.867、静态 K 配置 4 个、k_std 均值 3.170、k_medio 范围 [4.93, 12.67] —— **与 agent 报告全部逐位一致** ✅
- **R08 独立核对**：裁判 grep 冻结 `run_reproduction.py` 与 `selection-agent/pyproject.toml`，dirichlet-alpha=0.1 全配置一致 ✅
- evidence_table.csv 40 项指标均带 provenance 列（computed from frozen ... / PAPER-CITED），无编造痕迹；代码可运行（run_all.py）

## C 方法与报告（13/15）

- C1 方法合理性（5/5）：统计推断规范（单因素 ANOVA + Welch t 检验），口径定义清晰（k_std 度量、±2pp 判据）；CIFAR-10/MNIST/论文引用三层证据分离明确
- C2 稳健性（3/5）：ANOVA/两两检验提供了统计显著性证据；但冻结集仅存 3 次运行聚合值，无法做多 seed 重跑/置信区间复核（受数据限制）
- C3 边界与结论（5/5）：**亮点**——发现并明确报告论文 Table 2 与 Figure 4 叙述的方向矛盾（C03），拒绝强行下结论；局限 5 条诚实；PAPER-CITED 与 computed 标签贯穿全文

## 结论

- **科学结论**：论文核心主张（不同 LLM/提示下 accuracy 可比、K-Agent 动态调整 K、ToolAgent 的 token 可扩展性优于 raw LLM）在可用数据范围内得到支持；C03（raw LLM 优于 ToolAgent）无法验证且论文内部数据矛盾 → `partially_supported`
- 数据真实性满分（C01/C02 全可重算且一致）；A 扣分主因：C03 inconclusive + exists/figure 类规则无冻结产物可验证
- 备注：本包为"官方 artifact 分析 + 论文引用"混合型，agent 对证据层级（computed / PAPER-CITED / missing）的标注是全 24 篇中最好的之一
