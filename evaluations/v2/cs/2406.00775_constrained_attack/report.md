# EVAL REPORT v2: 2406.00775_constrained_attack

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1: agent报告MLP模型CAPGD鲁棒准确率16.94%，CPGD为99.63%，差距>40pp且CAPGD≤40%，落入满分带（35分），有evidence_table和metrics.json落盘支撑。A2: 报告MLP和ResMLP两个模型均满足CAPGD<CPGD，且MLP的CAPGD=16.94%≤20%，同时报告了n_attacked与约束满足率，落入满分带（25分），证据齐全。A总分60。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘扫描显示metrics.json、evidence_table.csv等实测证据文件均存在且完整。evidence_table与metrics.json内部数值与报告散文严格一致（如MLP CAPGD 16.94%，ResMLP 20.50%）。urldata_check.json核验数据规模11430×64及phishing占比50%与锚值一致。代码逻辑完整，无测试集泄漏，属于有证据文件且数值严格一致、可核对，B给满分40。 |

## A 核心结果达成度（60/60）

A1: agent报告MLP模型CAPGD鲁棒准确率16.94%，CPGD为99.63%，差距>40pp且CAPGD≤40%，落入满分带（35分），有evidence_table和metrics.json落盘支撑。A2: 报告MLP和ResMLP两个模型均满足CAPGD<CPGD，且MLP的CAPGD=16.94%≤20%，同时报告了n_attacked与约束满足率，落入满分带（25分），证据齐全。A总分60。

## B 证据真实性/实际复现（40/40）

磁盘扫描显示metrics.json、evidence_table.csv等实测证据文件均存在且完整。evidence_table与metrics.json内部数值与报告散文严格一致（如MLP CAPGD 16.94%，ResMLP 20.50%）。urldata_check.json核验数据规模11430×64及phishing占比50%与锚值一致。代码逻辑完整，无测试集泄漏，属于有证据文件且数值严格一致、可核对，B给满分40。

## 证据与重算说明

独立重算未执行。关键实测数：url.csv规模11430×64，phishing占比50%；MLP(seed=0) CPGD 99.63%，CAPGD 16.94%，约束满足率1.0；ResMLP(seed=0) CPGD 99.85%，CAPGD 20.50%，约束满足率1.0。所有数值在report、evidence_table.csv、metrics.json中严格一致。

## 结论

- **科学结论**: `supported`
- 亮点: 完整实现了CAPGD的核心机制与约束修复算子，在两个深层模型上稳定复现了论文核心结论，证据链完整、透明且多文件交叉验证一致。
- 不足: 受限于算力未实现CAA组合攻击及论文原架构（如TabTransformer），但已在局限性中充分说明，不影响核心claim的验证。