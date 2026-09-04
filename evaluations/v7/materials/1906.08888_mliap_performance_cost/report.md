# EVAL REPORT v7: 1906.08888_mliap_performance_cost

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 70.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 15.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **42.0** | 60 | A1：核心交付物完整，包含 metrics.json, evidence_table.csv 等机器可读结果，得 12 分。A2：复现了能量/力 MAE 量级、无过拟合及模型排序方向，但化学趋势仅部分复现，结论为 partially_supported。受结论级硬上限约束，A2 给至该档上限 15 分。A3：方法严谨，自写 BP 描述符并验证解析梯度，采用 80/20 验证集调参防泄漏，代码与证据文件支持完整复算，得 15 分。 |
| B 真值一致性/可验证性 | 28.0 | 40 | truth_check=matched | agent数 vs 锚点比对：1. 数据规模：agent报出 Mo train=194/test=23, Cu train=262/test=31 vs 锚点3 'train ~200-260, test ~23-31' → 精确吻合。2. 能量精度：agent报出最佳模型均值 5.1 meV/atom (范围1.4-9.8) vs 锚点4 'meV/atom 量级' → 量级吻合。3. 力精度：agent报出均值 0.174 eV/Å (范围0.06-0.30) vs 锚点5 '~0.1 eV/Å 量级' → 量级吻合。4. 无过拟合：agent报出 train/test ratio 0.70 vs 锚点6 '训练与测试误差相近' → 吻合。5. 化学趋势：agent报出 fcc最低，但bcc与金刚石排序未严格遵循 vs 锚点8 'fcc最低、bcc次之、金刚石最高' → 部分偏离。综合定量指标均吻合，truth_check 判定为 matched，但受 partially_supported 结论硬上限限制，B 给 28 分。 |

## A 核心结果达成度（42.0/60 = A1 12.0 + A2 15.0 + A3 15.0）

A1：核心交付物完整，包含 metrics.json, evidence_table.csv 等机器可读结果，得 12 分。A2：复现了能量/力 MAE 量级、无过拟合及模型排序方向，但化学趋势仅部分复现，结论为 partially_supported。受结论级硬上限约束，A2 给至该档上限 15 分。A3：方法严谨，自写 BP 描述符并验证解析梯度，采用 80/20 验证集调参防泄漏，代码与证据文件支持完整复算，得 15 分。

## B 真值一致性/可验证性（28.0/40）[truth_check=matched]

agent数 vs 锚点比对：1. 数据规模：agent报出 Mo train=194/test=23, Cu train=262/test=31 vs 锚点3 'train ~200-260, test ~23-31' → 精确吻合。2. 能量精度：agent报出最佳模型均值 5.1 meV/atom (范围1.4-9.8) vs 锚点4 'meV/atom 量级' → 量级吻合。3. 力精度：agent报出均值 0.174 eV/Å (范围0.06-0.30) vs 锚点5 '~0.1 eV/Å 量级' → 量级吻合。4. 无过拟合：agent报出 train/test ratio 0.70 vs 锚点6 '训练与测试误差相近' → 吻合。5. 化学趋势：agent报出 fcc最低，但bcc与金刚石排序未严格遵循 vs 锚点8 'fcc最低、bcc次之、金刚石最高' → 部分偏离。综合定量指标均吻合，truth_check 判定为 matched，但受 partially_supported 结论硬上限限制，B 给 28 分。

## 证据与重算说明

独立重算未执行。关键实测数：Mo train=194/test=23，Cu train=262/test=31；最佳模型能量MAE均值5.1 meV/atom，力MAE均值0.174 eV/Å；train/test ratio均值0.70。所有数值均在 evidence_table.csv 与 metrics.json 中有详细落盘记录，且包含底层配置级误差分布，证据链扎实。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `matched`
- 亮点: 数据统计精确，四类代理模型实现完整且防泄漏协议严谨；落盘了 per-config 级别的详细误差数组，证据链极其扎实且内部高度自洽。
- 不足: 受限于代理模型表达能力，化学趋势（bcc 与金刚石结构的严格排序）未能完全复现，导致最终结论仅为 partially_supported，触发评分硬上限。