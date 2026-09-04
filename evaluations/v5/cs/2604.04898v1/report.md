# EVAL REPORT v5: 2604.04898v1

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 64.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 12.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **39.0** | 60 | A1: 核心交付物（solution.md, code, evidence_table, metrics.json）完整产出，符合任务要求，得12分。A2: 结论为partially_supported，受硬上限约束A2≤15；Agent诚实指出因judge和scaffold差异导致核心数值无法复现，但复现了部分定性趋势和数据集特征，给12分。A3: 方法严谨，明确区分论文引用与本地计算，统计分析扎实，代码可复现，得15分。 |
| B 证据真实性/实际复现 | 25.0 | 40 | 证据等级为2（齐全自洽），提供了丰富的JSON和CSV证据文件，内部自洽且来源标注规范。受partially_supported结论硬上限约束（B≤28），给25分。 |

## A 核心结果达成度（39.0/60 = A1 12.0 + A2 12.0 + A3 15.0）

A1: 核心交付物（solution.md, code, evidence_table, metrics.json）完整产出，符合任务要求，得12分。A2: 结论为partially_supported，受硬上限约束A2≤15；Agent诚实指出因judge和scaffold差异导致核心数值无法复现，但复现了部分定性趋势和数据集特征，给12分。A3: 方法严谨，明确区分论文引用与本地计算，统计分析扎实，代码可复现，得15分。

## B 证据真实性/实际复现（25.0/40）

证据等级为2（齐全自洽），提供了丰富的JSON和CSV证据文件，内部自洽且来源标注规范。受partially_supported结论硬上限约束（B≤28），给25分。

## 证据与重算说明

独立重算未执行。关键实测数：本地judge下IMO-ProofBench qed_nano_direct均分5.433/7，qed_nano_rc均分5.506/7；FineProofs-RL reward_mean为0.399；数据集规模与论文一致。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 极其严谨地识别了本地复现环境与论文的差异，拒绝编造数值，统计分析扎实，证据链完整自洽。
- 不足: 受限于本地环境与工具链，未能实现RSA scaffold及引入更强judge，导致核心数值锚点未能直接命中，结论仅为部分支持。