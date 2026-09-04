# EVAL REPORT v5: 2604.04868v1

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v5（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 69.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **41.0** | 60 | A1: 完整提交了solution.md、代码、evidence_table和metrics.json，核心交付物无缺失(12分)。A2: 核心指标ROC-AUC和SHAP完美复现并支持论文claim，但C02因冻结数据缺失判定为inconclusive，C01/C04的attention部分因数据不全判定为partially_supported；整体结论未完全成立，受硬上限约束给14分。A3: 方法论极其严谨，敏锐发现sklearn默认shuffle导致的特征索引错位并修正，逻辑sound且可复现(15分)。 |
| B 证据真实性/实际复现 | 28.0 | 40 | 证据等级为2，metrics.json与evidence_table齐全且内部自洽，代码提供了完整的冻结数据解析与校验逻辑。但受partially_supported结论硬上限约束，B最高给28分。 |

## A 核心结果达成度（41.0/60 = A1 12.0 + A2 14.0 + A3 15.0）

A1: 完整提交了solution.md、代码、evidence_table和metrics.json，核心交付物无缺失(12分)。A2: 核心指标ROC-AUC和SHAP完美复现并支持论文claim，但C02因冻结数据缺失判定为inconclusive，C01/C04的attention部分因数据不全判定为partially_supported；整体结论未完全成立，受硬上限约束给14分。A3: 方法论极其严谨，敏锐发现sklearn默认shuffle导致的特征索引错位并修正，逻辑sound且可复现(15分)。

## B 证据真实性/实际复现（28.0/40）

证据等级为2，metrics.json与evidence_table齐全且内部自洽，代码提供了完整的冻结数据解析与校验逻辑。但受partially_supported结论硬上限约束，B最高给28分。

## 证据与重算说明

独立重算未执行（基于冻结数据解析）。关键实测数：Baseline ROC-AUC=0.9958（锚值0.974），SHAP informative share=98.8%，Random features ROC-AUC range=0.0126。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 方法论审查极其细致，成功识别并修正了参考流水线中因特征洗牌导致的索引错位问题；对缺失证据诚实报告，展现了极高的科研诚信。
- 不足: 受限于冻结数据且无模型权重，未能补充运行C02所需的PCA嵌入提取，导致部分核心claim只能判定为inconclusive或partially_supported。