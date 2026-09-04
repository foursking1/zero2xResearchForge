# EVAL REPORT v3: 2406.00775_constrained_attack

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 82.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 42.0 | 60 | Agent实测MLP的CAPGD鲁棒准确率为16.94%，CPGD为99.63%，差距>40pp且CAPGD≤40%，满足Rubric满分带条件。但根据eval103梯度化给分铁律，对比论文最接近的锚值TabNet(19.3%)，偏差约为12.2%，落入10%-20%偏差区间，故A维度给42分，严禁把落入宽松成功带直接给满分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示证据等级为2（齐全自洽）。metrics.json与evidence_table.csv内部数值严格一致，urldata_check.json与verify_data.py提供了数据规模与占比的校验证据，代码逻辑完整且无测试集泄漏，符合B=40的最高档标准。 |

## A 核心结果达成度（42.0/60）

Agent实测MLP的CAPGD鲁棒准确率为16.94%，CPGD为99.63%，差距>40pp且CAPGD≤40%，满足Rubric满分带条件。但根据eval103梯度化给分铁律，对比论文最接近的锚值TabNet(19.3%)，偏差约为12.2%，落入10%-20%偏差区间，故A维度给42分，严禁把落入宽松成功带直接给满分。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示证据等级为2（齐全自洽）。metrics.json与evidence_table.csv内部数值严格一致，urldata_check.json与verify_data.py提供了数据规模与占比的校验证据，代码逻辑完整且无测试集泄漏，符合B=40的最高档标准。

## 证据与重算说明

独立重算未执行。关键实测数：url.csv规模11430×64，phishing占比50%；MLP(seed=0) CPGD 99.63%，CAPGD 16.94%，约束满足率1.0；ResMLP(seed=0) CPGD 99.85%，CAPGD 20.50%。所有数值在report、evidence_table.csv、metrics.json中严格一致。

## 结论

- **科学结论**: `supported`
- 亮点: 完整实现了CAPGD的核心机制与约束修复算子，在两个深层模型上稳定复现了论文核心结论，证据链完整且多文件交叉验证一致。
- 不足: 受限于算力未使用论文原架构（如TabTransformer/TabNet），导致实测数值与论文具体锚值存在10%以上的偏差，未能精确命中锚值。