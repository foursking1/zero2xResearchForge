# EVAL REPORT v7: 2604.04842v1

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 47.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 12.0 | 33 | |
| A3 方法严谨与可复现 | 13.0 | 15 | |
| **A 合计** | **37.0** | 60 | A1: 交付物完整，包含metrics.json、evidence_table.csv及可运行代码，核心交付物齐备且机器可读（12分）。A2: 结论判定为partially_supported，敏锐发现了C02中Harmful Content并非最高的内在矛盾，但核心指标未能实际复现，受限于结论硬上限及未复现真值，给12分。A3: 方法严谨，诚实区分了paper_cited与computed_from_frozen_data，代理PPL实验设计合理且无数据泄漏（13分）。 |
| B 真值一致性/可验证性 | 10.0 | 40 | truth_check=unverified | Agent实测数：proxy char-PPL mean = 3.06，local TE occurrence rate = 0.25。锚点真值：R09 PPL = 15.0，R04 TE = 0.44。比对结果：偏离/无法核对。Agent使用n-gram代理PPL和3个episode的局部judge，与论文GPT-2和8模型GPT-4o judge量纲和规模完全不同，导致实测数字无法验证论文真值。虽然Agent诚实标注了paper_cited，但本质上核心锚点属于unverified（数字无法对应任何论文真值），B给10分。 |

## A 核心结果达成度（37.0/60 = A1 12.0 + A2 12.0 + A3 13.0）

A1: 交付物完整，包含metrics.json、evidence_table.csv及可运行代码，核心交付物齐备且机器可读（12分）。A2: 结论判定为partially_supported，敏锐发现了C02中Harmful Content并非最高的内在矛盾，但核心指标未能实际复现，受限于结论硬上限及未复现真值，给12分。A3: 方法严谨，诚实区分了paper_cited与computed_from_frozen_data，代理PPL实验设计合理且无数据泄漏（13分）。

## B 真值一致性/可验证性（10.0/40）[truth_check=unverified]

Agent实测数：proxy char-PPL mean = 3.06，local TE occurrence rate = 0.25。锚点真值：R09 PPL = 15.0，R04 TE = 0.44。比对结果：偏离/无法核对。Agent使用n-gram代理PPL和3个episode的局部judge，与论文GPT-2和8模型GPT-4o judge量纲和规模完全不同，导致实测数字无法验证论文真值。虽然Agent诚实标注了paper_cited，但本质上核心锚点属于unverified（数字无法对应任何论文真值），B给10分。

## 证据与重算说明

独立重算未执行。关键实测数：局部ASR=0.25/0.333，代理char-PPL=3.06。Agent诚实区分了引用数据与实测数据，未将论文数字伪装成实测结果，但实测数据因实验规模与模型差异无法与论文真值直接比对。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `unverified`
- 亮点: 极其诚实且严谨，明确区分了论文引用数据与本机代理计算数据，未造假；敏锐捕捉到了论文自身claim与表格数据的矛盾（C02 Harmful Content）。
- 不足: 受限于冻结数据的不完整性，未能复现核心的8模型ASR/SS及GPT-2 PPL实验，导致实测数字无法与论文真值直接比对，证据验证度不足。