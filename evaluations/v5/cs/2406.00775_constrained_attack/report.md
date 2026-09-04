# EVAL REPORT v5: 2406.00775_constrained_attack

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 33.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **60.0** | 60 | A1: 完整产出了任务要求的核心交付物，包括evidence_table.csv、metrics.json、完整可运行代码及详细报告，得12分。A2: 实测MLP和ResMLP的CAPGD鲁棒准确率分别为16.94%和20.50%，相比CPGD（>99%）下降约80pp，完美复现了论文中CAPGD显著优于CPGD且将鲁棒准确率压至10%-20%区间的核心claim，效应与量级高度匹配，得33分。A3: 方法严谨，正确隔离测试集，仅攻击关键类正确分类样本，实现了Algorithm 1的自适应步长、动量、双起点及复杂的约束修复算子，口径与论文一致，得15分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描确认存在metrics.json、evidence_table.csv及urldata_check.json等完整证据链，证据等级为2。实测数值在报告、CSV和JSON中严格一致，且提供了数据规模与分布的独立校验证据，无测试集泄漏，符合最高档标准，得40分。 |

## A 核心结果达成度（60.0/60 = A1 12.0 + A2 33.0 + A3 15.0）

A1: 完整产出了任务要求的核心交付物，包括evidence_table.csv、metrics.json、完整可运行代码及详细报告，得12分。A2: 实测MLP和ResMLP的CAPGD鲁棒准确率分别为16.94%和20.50%，相比CPGD（>99%）下降约80pp，完美复现了论文中CAPGD显著优于CPGD且将鲁棒准确率压至10%-20%区间的核心claim，效应与量级高度匹配，得33分。A3: 方法严谨，正确隔离测试集，仅攻击关键类正确分类样本，实现了Algorithm 1的自适应步长、动量、双起点及复杂的约束修复算子，口径与论文一致，得15分。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描确认存在metrics.json、evidence_table.csv及urldata_check.json等完整证据链，证据等级为2。实测数值在报告、CSV和JSON中严格一致，且提供了数据规模与分布的独立校验证据，无测试集泄漏，符合最高档标准，得40分。

## 证据与重算说明

独立重算未执行。关键实测数：url.csv规模11430×64，phishing占比50%；MLP(seed=0) CPGD 99.63%，CAPGD 16.94%，约束满足率1.0；ResMLP(seed=0) CPGD 99.85%，CAPGD 20.50%，约束满足率1.0。所有数值在report、evidence_table.csv、metrics.json中严格一致。

## 结论

- **科学结论**: `supported`
- 亮点: 完整且精确地实现了CAPGD的核心机制与复杂的表格约束修复算子，在两个深层模型上稳定复现了论文的核心结论，证据链完整、透明且多文件交叉验证一致。
- 不足: 受限于算力未实现CAA组合攻击及论文原架构（如TabTransformer），但已在局限性中充分说明，不影响核心claim的验证。