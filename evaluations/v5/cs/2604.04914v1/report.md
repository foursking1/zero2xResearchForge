# EVAL REPORT v5: 2604.04914v1

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 65.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 12.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **39.0** | 60 | A1: 交付了完整的代码、evidence表和metrics.json，针对TASK.md要求的C01-C04均产出了实质性分析产物，得12分。A2: 结论为partially_supported，受硬上限约束A2≤15。Agent在C01/C03/C04上复现了定性趋势（如小模型unknown较少），但受限于20s超时和模型架构不匹配，R08/R09数值偏离较大，C02因缺数据inconclusive，定性匹配但弱，给12分。A3: 方法严谨，详细记录了ONNX提取、MIP编码修复及witness精确校验，代码可复现性强，得15分。 |
| B 证据真实性/实际复现 | 26.0 | 40 | 证据等级为2，提供了完整的metrics.json和evidence_table.csv，无造假痕迹。但受限于求解器预算导致大量超时，部分指标基于极小样本或为NaN，且结论为partially_supported触发硬上限（B≤28），故给26分。 |

## A 核心结果达成度（39.0/60 = A1 12.0 + A2 12.0 + A3 15.0）

A1: 交付了完整的代码、evidence表和metrics.json，针对TASK.md要求的C01-C04均产出了实质性分析产物，得12分。A2: 结论为partially_supported，受硬上限约束A2≤15。Agent在C01/C03/C04上复现了定性趋势（如小模型unknown较少），但受限于20s超时和模型架构不匹配，R08/R09数值偏离较大，C02因缺数据inconclusive，定性匹配但弱，给12分。A3: 方法严谨，详细记录了ONNX提取、MIP编码修复及witness精确校验，代码可复现性强，得15分。

## B 证据真实性/实际复现（26.0/40）

证据等级为2，提供了完整的metrics.json和evidence_table.csv，无造假痕迹。但受限于求解器预算导致大量超时，部分指标基于极小样本或为NaN，且结论为partially_supported触发硬上限（B≤28），故给26分。

## 证据与重算说明

独立重算未执行。关键实测数：R08风格指标smaller_model_unknown_reduction为12.5%（锚值45%）；R09风格指标resolved_by_only_one_engine_fraction为100%（基于2个解析查询，锚值60%）；MIP与CROWN大量查询在20s超时。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 诚实且详尽地分析了冻结数据与论文架构的差异，MIP编码修复与witness校验逻辑严谨，证据链真实可靠。
- 不足: 受限于求解器预算（20s）和模型不匹配，未能复现核心数值锚点，且大量查询超时导致统计指标有效性受限。