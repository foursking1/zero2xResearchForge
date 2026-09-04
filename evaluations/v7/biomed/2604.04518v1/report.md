# EVAL REPORT v7: 2604.04518v1

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 65.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 13.0 | 15 | |
| **A 合计** | **39.0** | 60 | A1(12): 核心交付物完整，包含metrics.json、evidence_table.csv及详尽的solution报告，机器可读结果齐全。A2(14): agent诚实且准确地判定C01成立，但受限于算力与proxy方法，C02/C03的核心修复效果未能复现，判定为contradicted，整体结论为partially_supported，符合其实际复现情况，给予中上分数。A3(13): 方法设计严谨，对CPU算力限制导致的超参缩减、CFKD proxy替代及SpRAy自动聚类等deviation进行了极其详尽且诚实的记录，无数据泄漏，可复现性强。 |
| B 真值一致性/可验证性 | 26.0 | 40 | truth_check=matched | 逐条比对：1) R01(Squares sym AGA): agent数 50.1% (0.50125) vs 锚点 51.1% → 吻合(在±2.5容差内)；2) R08(SpRAy Squares acc): agent数 99.2%~100% vs 锚点 100.0% → 吻合(在±5.0容差内)；3) R02(Squares sym WGA): agent数 0.5% (0.005) vs 锚点 1.8% → 偏离(超出±0.5容差，但方向正确)；4) R09(Blond minority SpRAy acc): agent数 0% vs 锚点 20.0% → 偏离(自动聚类导致少数组崩溃)。满足≥2个锚点吻合，truth_check判为matched，但受partially_supported结论硬上限(B≤28)钳制，给26分。 |

## A 核心结果达成度（39.0/60 = A1 12.0 + A2 14.0 + A3 13.0）

A1(12): 核心交付物完整，包含metrics.json、evidence_table.csv及详尽的solution报告，机器可读结果齐全。A2(14): agent诚实且准确地判定C01成立，但受限于算力与proxy方法，C02/C03的核心修复效果未能复现，判定为contradicted，整体结论为partially_supported，符合其实际复现情况，给予中上分数。A3(13): 方法设计严谨，对CPU算力限制导致的超参缩减、CFKD proxy替代及SpRAy自动聚类等deviation进行了极其详尽且诚实的记录，无数据泄漏，可复现性强。

## B 真值一致性/可验证性（26.0/40）[truth_check=matched]

逐条比对：1) R01(Squares sym AGA): agent数 50.1% (0.50125) vs 锚点 51.1% → 吻合(在±2.5容差内)；2) R08(SpRAy Squares acc): agent数 99.2%~100% vs 锚点 100.0% → 吻合(在±5.0容差内)；3) R02(Squares sym WGA): agent数 0.5% (0.005) vs 锚点 1.8% → 偏离(超出±0.5容差，但方向正确)；4) R09(Blond minority SpRAy acc): agent数 0% vs 锚点 20.0% → 偏离(自动聚类导致少数组崩溃)。满足≥2个锚点吻合，truth_check判为matched，但受partially_supported结论硬上限(B≤28)钳制，给26分。

## 证据与重算说明

独立重算未执行。磁盘证据扫描显示证据等级为2，metrics.json与evidence_table.csv数据丰富且内部自洽，包含大量中间模型指标与运行日志，证据链完整闭环。关键实测数均有落盘文件支撑，无编造痕迹。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `matched`
- 亮点: 科学态度极其严谨，对未能复现的claim没有强行凑数，而是通过feature-probe机制分析给出了令人信服的解释；数据与代码证据链极其完整。
- 不足: 受限于CPU算力，部分核心correction方法使用了缩减网格或proxy，导致C02/C03的定量结果与论文存在较大差距，未能复现论文的核心修复效果。