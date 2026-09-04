# EVAL REPORT: 2406.00775_constrained_attack

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判（qwen3.7-max）
- 评测时间: 2026-08-19

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1: agent报告MLP模型CAPGD鲁棒准确率16.94%，CPGD为99.63%；rubric band表：[CAPGD ≤ CPGD − 40pp 且 CAPGD ≤ 40% → 35分]；16.94 ≤ 99.63-40 且 16.94 ≤ 40 成立，落入满分带 → 35分。A2: agent报告2个模型（MLP和ResMLP）全部满足CAPGD<CPGD，且MLP的CAPGD=16.94%≤20%，同时报告了n_attacked与约束满足率；rubric band表：[≥2个模型全部满足CAPGD<CPGD，且至少一个CAPGD≤20%；报告n_attacked与约束满足率 → 25分]；条件全部满足，落入满分带 → 25分。A总分60。 |
| B 证据真实性 | 25 | 25 | 提交物齐全（代码、evidence_table、metrics.json、report均具备）。论文数值与实测数值严格区分。urldata_check.json核验url.csv为11430×64，phishing占比50%，与锚值一致；CAPGD约束满足率报告为1.0。内部数值一致。独立重算未执行。B总分25。 |
| C 方法与报告 | 15 | 15 | C1方法合理，详细对应Algorithm 1各组件及14条约束的R_Omega修复；C2实验严谨，明确只攻击关键类正确分类样本，测试集隔离，L2 ε=0.5口径正确；C3结论与证据匹配，充分讨论了未实现CAA、目标函数替换等局限性。C总分15。 |

## A 核心结果达成度（60/60）

A1: agent报告MLP模型CAPGD鲁棒准确率16.94%，CPGD为99.63%；rubric band表：[CAPGD ≤ CPGD − 40pp 且 CAPGD ≤ 40% → 35分]；16.94 ≤ 99.63-40 且 16.94 ≤ 40 成立，落入满分带 → 35分。A2: agent报告2个模型（MLP和ResMLP）全部满足CAPGD<CPGD，且MLP的CAPGD=16.94%≤20%，同时报告了n_attacked与约束满足率；rubric band表：[≥2个模型全部满足CAPGD<CPGD，且至少一个CAPGD≤20%；报告n_attacked与约束满足率 → 25分]；条件全部满足，落入满分带 → 25分。A总分60。

## B 证据真实性（25/25）

提交物齐全（代码、evidence_table、metrics.json、report均具备）。论文数值与实测数值严格区分。urldata_check.json核验url.csv为11430×64，phishing占比50%，与锚值一致；CAPGD约束满足率报告为1.0。内部数值一致。独立重算未执行。B总分25。

## C 方法与报告（15/15）

C1方法合理，详细对应Algorithm 1各组件及14条约束的R_Omega修复；C2实验严谨，明确只攻击关键类正确分类样本，测试集隔离，L2 ε=0.5口径正确；C3结论与证据匹配，充分讨论了未实现CAA、目标函数替换等局限性。C总分15。

## 证据与重算说明

独立重算未执行。关键实测数值：url.csv规模11430×64，phishing占比50%（5715/5715）；MLP(seed=0) CPGD鲁棒准确率99.63%，CAPGD 16.94%，约束满足率1.0；ResMLP(seed=0) CPGD 99.85%，CAPGD 20.50%，约束满足率1.0。

## 结论

- **科学结论**: `supported`
- 亮点: 完整实现了CAPGD的核心机制（自适应步长、动量、双起点、repair算子），并在两个深层模型上稳定复现了论文的核心结论，证据链完整且透明。
- 不足: 受限于算力未实现CAA组合攻击及论文原架构（如TabTransformer），但已在局限性中充分说明，不影响核心claim的验证。