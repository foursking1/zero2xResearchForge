# EVAL REPORT v7: 1903.02557_dash_supernova_class

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 92.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 27.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **54.0** | 60 | A1(12)：核心交付物完整，产出了metrics.json、evidence_table.csv等机器可读结果，覆盖全部69条冻结光谱。A2(27)：结论supported合理，达到了任务卡设定的子集成立阈值（总体>=0.80, Ia>=0.90），与Table 1分型比率绝对差在15pp容差内；但未完成Table 2全量逐对象复现一致率，仅spot-check两对象，按rubric扣3分。A3(15)：方法严谨，正确处理了Ic-broad排除口径，透明说明了numpy 2.x兼容性monkeypatch，代码逻辑sound且可复现。 |
| B 真值一致性/可验证性 | 38.0 | 40 | truth_check=matched | 1. 总体匹配率：agent数 56/64=0.875 vs 锚点 197/212=0.929 → 满足子集>=0.80阈值，吻合。2. Ia匹配率：agent数 49/54=0.907 vs 锚点 127/129=0.984 → 满足子集>=0.90阈值，吻合。3. II匹配率：agent数 6/8=0.750 vs 锚点 25/28=0.893 → 绝对差14.3pp，在<=15pp容差内，吻合。4. 速度：agent数 3.59s/69条 vs 锚点 <20s/212条 → 吻合。5. 抽查DES16C3bq：agent数 Ia-norm vs 锚点 Ia-norm → 吻合。6. 抽查DES16E2aoh：agent数 Ia-91bg vs 锚点 Ia-91T → 大类吻合，子类型因模型版本差异偏离（符合CALIBRATION放宽规则）。综合判定为matched。 |

## A 核心结果达成度（54.0/60 = A1 12.0 + A2 27.0 + A3 15.0）

A1(12)：核心交付物完整，产出了metrics.json、evidence_table.csv等机器可读结果，覆盖全部69条冻结光谱。A2(27)：结论supported合理，达到了任务卡设定的子集成立阈值（总体>=0.80, Ia>=0.90），与Table 1分型比率绝对差在15pp容差内；但未完成Table 2全量逐对象复现一致率，仅spot-check两对象，按rubric扣3分。A3(15)：方法严谨，正确处理了Ic-broad排除口径，透明说明了numpy 2.x兼容性monkeypatch，代码逻辑sound且可复现。

## B 真值一致性/可验证性（38.0/40）[truth_check=matched]

1. 总体匹配率：agent数 56/64=0.875 vs 锚点 197/212=0.929 → 满足子集>=0.80阈值，吻合。2. Ia匹配率：agent数 49/54=0.907 vs 锚点 127/129=0.984 → 满足子集>=0.90阈值，吻合。3. II匹配率：agent数 6/8=0.750 vs 锚点 25/28=0.893 → 绝对差14.3pp，在<=15pp容差内，吻合。4. 速度：agent数 3.59s/69条 vs 锚点 <20s/212条 → 吻合。5. 抽查DES16C3bq：agent数 Ia-norm vs 锚点 Ia-norm → 吻合。6. 抽查DES16E2aoh：agent数 Ia-91bg vs 锚点 Ia-91T → 大类吻合，子类型因模型版本差异偏离（符合CALIBRATION放宽规则）。综合判定为matched。

## 证据与重算说明

独立重算未执行。关键实测数均来自落盘证据：总体匹配率56/64=0.875，Ia匹配率49/54=0.907，全批次墙钟耗时3.59s。evidence_table.csv包含69条完整记录，与metrics.json及report.md严格一致，无数据伪造或泄漏迹象。rlap列因numpy 2.x兼容性问题全为failed，但不影响核心分类指标。

## 结论

- **科学结论**: `supported`
- **可验证性**: `matched`
- 亮点: 完整执行了69条冻结光谱的DASH v06推理，逐条证据表与指标JSON严格一致，对工程兼容性问题（numpy 2.x）和模型版本差异处理透明且合理。
- 不足: 未严格按照任务卡要求单独拆分带'?'的分型匹配率（Ia?/II?/Ibc?），且未完成Table 2全量逐对象复现一致率。