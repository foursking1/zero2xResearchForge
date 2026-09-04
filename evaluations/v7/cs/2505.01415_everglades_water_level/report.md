# EVAL REPORT v7: 2505.01415_everglades_water_level

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 55.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 13.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **40.0** | 60 | A1: 核心交付物完整，包含代码、evidence_table及多维度metrics CSV，机器可读，得12分。A2: 结论为partially_supported（受硬上限≤15约束）。成功复现线性退化趋势，但核心模型（NBEATS、Chronos、NLinear）绝对数值与论文锚点严重偏离，得13分。A3: 防泄漏设计严密，提供verify_data脚本与固定种子，方法sound且可复现，得15分。 |
| B 真值一致性/可验证性 | 15.0 | 40 | truth_check=diverged | 逐条比对：1) NBEATS 28d MAE: agent数 0.451 vs 锚点 0.176 → 严重偏离；2) NLinear 28d MAE: agent数 0.397 vs 锚点 0.185 → 严重偏离；3) DLinear 28d MAE: agent数 0.451 vs 锚点 0.392 → 在宽容差内但仍有偏离；4) Chronos 28d MAE: agent数 0.348 vs 锚点 0.088 → 严重偏离且未能复现最优claim；5) 线性退化增幅: agent DLinear +69%/NLinear +83% vs 锚点 DLinear +313%/NLinear +71% → 趋势吻合但模型间相对次序偏离。整体判定为diverged。 |

## A 核心结果达成度（40.0/60 = A1 12.0 + A2 13.0 + A3 15.0）

A1: 核心交付物完整，包含代码、evidence_table及多维度metrics CSV，机器可读，得12分。A2: 结论为partially_supported（受硬上限≤15约束）。成功复现线性退化趋势，但核心模型（NBEATS、Chronos、NLinear）绝对数值与论文锚点严重偏离，得13分。A3: 防泄漏设计严密，提供verify_data脚本与固定种子，方法sound且可复现，得15分。

## B 真值一致性/可验证性（15.0/40）[truth_check=diverged]

逐条比对：1) NBEATS 28d MAE: agent数 0.451 vs 锚点 0.176 → 严重偏离；2) NLinear 28d MAE: agent数 0.397 vs 锚点 0.185 → 严重偏离；3) DLinear 28d MAE: agent数 0.451 vs 锚点 0.392 → 在宽容差内但仍有偏离；4) Chronos 28d MAE: agent数 0.348 vs 锚点 0.088 → 严重偏离且未能复现最优claim；5) 线性退化增幅: agent DLinear +69%/NLinear +83% vs 锚点 DLinear +313%/NLinear +71% → 趋势吻合但模型间相对次序偏离。整体判定为diverged。

## 证据与重算说明

独立重算未执行。关键实测数（如MLPResidual 0.298, NLinear 0.397, DLinear 0.451, Chronos 0.348）均有落盘CSV支撑，数据事实（1411行，日期范围）核对正确，但模型输出数值与论文真值存在显著差异。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 防泄漏设计严谨，证据文件极其详实且多维分解，对未能复现的绝对数值和Chronos劣势进行了客观的局限性分析。
- 不足: NBEATS等经典模型未能复现论文优势（MAE偏高），且线性模型间的相对退化幅度排序与论文锚值相反，Chronos受限于本地小权重未能验证claim c。