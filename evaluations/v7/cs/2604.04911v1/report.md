# EVAL REPORT v7: 2604.04911v1

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 49.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 10.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **37.0** | 60 | A1: 交付物完整，包含solution、代码、evidence表和metrics.json，完全符合任务要求（12分）。A2: 核心指标复现存在显著偏差（VE偏离4个数量级，FE偏离约30%），C02-C04因缺数据无法复现，整体结论为partially_supported，科学结论保真度受限，且受硬上限约束（10分）。A3: 方法极其严谨，诚实记录复现偏差并进行深入的敏感性分析（如zoom口径Variant A），无数据编造，可复现性强（15分）。 |
| B 真值一致性/可验证性 | 12.0 | 40 | truth_check=diverged | agent数 C01_FE_repro_overall_FE=0.690 vs 锚点 R04=0.527 → 偏离（超容差0.026）；agent数 C01_VE_repro_overall_VE=2295.46 vs 锚点 R03=0.243 → 严重偏离（量级错误，超容差0.012）；agent数 C01_CameraOverall_repro=1148.07 vs 锚点 R06=0.385 → 严重偏离；C02-C04指标（R07-R09, R13-R15）仅有paper_citation，无实测数据 → unverified。综合判定 truth_check=diverged。 |

## A 核心结果达成度（37.0/60 = A1 12.0 + A2 10.0 + A3 15.0）

A1: 交付物完整，包含solution、代码、evidence表和metrics.json，完全符合任务要求（12分）。A2: 核心指标复现存在显著偏差（VE偏离4个数量级，FE偏离约30%），C02-C04因缺数据无法复现，整体结论为partially_supported，科学结论保真度受限，且受硬上限约束（10分）。A3: 方法极其严谨，诚实记录复现偏差并进行深入的敏感性分析（如zoom口径Variant A），无数据编造，可复现性强（15分）。

## B 真值一致性/可验证性（12.0/40）[truth_check=diverged]

agent数 C01_FE_repro_overall_FE=0.690 vs 锚点 R04=0.527 → 偏离（超容差0.026）；agent数 C01_VE_repro_overall_VE=2295.46 vs 锚点 R03=0.243 → 严重偏离（量级错误，超容差0.012）；agent数 C01_CameraOverall_repro=1148.07 vs 锚点 R06=0.385 → 严重偏离；C02-C04指标（R07-R09, R13-R15）仅有paper_citation，无实测数据 → unverified。综合判定 truth_check=diverged。

## 证据与重算说明

独立重算未执行。关键实测数：FE_repro=0.690（Variant A修正口径=0.327），VE_repro=2295.46（8样本smoke test）。Agent诚实报告了复现偏差，未编造数据，但实测数字与论文真值存在显著差异。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 科学态度极其严谨，严格区分论文引用与冻结数据实测，对复现偏差进行了深入的敏感性和归因分析，坚决拒绝编造数据。
- 不足: 受限于环境和冻结数据范围，核心指标（VE/FE）复现严重偏离论文真值，且大部分claim仅能进行论文内部一致性校验，未能实现端到端独立复现。