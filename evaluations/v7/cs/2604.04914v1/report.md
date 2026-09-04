# EVAL REPORT v7: 2604.04914v1

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 54.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 12.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **39.0** | 60 | A1: 交付了完整的代码、evidence表和metrics.json，机器可读结果完整，得12分。A2: 结论为partially_supported，受硬上限约束A2≤15。Agent诚实反映了冻结数据与论文架构的差异以及求解器超时问题，未伪造数据，定性趋势部分支持，给12分。A3: 方法严谨，详细记录了ONNX提取、MIP编码修复及witness精确校验，代码可复现性强，得15分。 |
| B 真值一致性/可验证性 | 15.0 | 40 | truth_check=diverged | R08 (小模型unknown减少比例): agent数 12.5% vs 锚点 45.0% → 严重偏离。R09 (单引擎解析比例): agent数 100.0% (仅2个样本) / NaN vs 锚点 60.0% → 偏离/不可比。R10 (CMARS 26 unit shift): agent未提供CMARS相关实测数 → 无法核对。由于定量指标均偏离或未覆盖，truth_check判定为diverged。 |

## A 核心结果达成度（39.0/60 = A1 12.0 + A2 12.0 + A3 15.0）

A1: 交付了完整的代码、evidence表和metrics.json，机器可读结果完整，得12分。A2: 结论为partially_supported，受硬上限约束A2≤15。Agent诚实反映了冻结数据与论文架构的差异以及求解器超时问题，未伪造数据，定性趋势部分支持，给12分。A3: 方法严谨，详细记录了ONNX提取、MIP编码修复及witness精确校验，代码可复现性强，得15分。

## B 真值一致性/可验证性（15.0/40）[truth_check=diverged]

R08 (小模型unknown减少比例): agent数 12.5% vs 锚点 45.0% → 严重偏离。R09 (单引擎解析比例): agent数 100.0% (仅2个样本) / NaN vs 锚点 60.0% → 偏离/不可比。R10 (CMARS 26 unit shift): agent未提供CMARS相关实测数 → 无法核对。由于定量指标均偏离或未覆盖，truth_check判定为diverged。

## 证据与重算说明

独立重算未执行。关键实测数：R08风格指标smaller_model_unknown_reduction为12.5%（锚值45%）；R09风格指标resolved_by_only_one_engine_fraction为100%（基于2个解析查询，锚值60%）；MIP与CROWN大量查询在20s超时。未包含CMARS(R10)相关数据。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 诚实且详尽地分析了冻结数据与论文架构的差异，MIP编码修复与witness校验逻辑严谨，证据链真实可靠，未强行凑数。
- 不足: 受限于求解器预算（20s）和模型不匹配，未能复现核心数值锚点，且缺失CMARS相关验证，导致定量指标严重偏离。