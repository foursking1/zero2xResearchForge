# EVAL REPORT v7: 2205.13760_tranception_proteingym

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 98.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 33.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **60.0** | 60 | A1: 核心交付物完整，包含 metrics.json、evidence_table.csv 及可运行代码，机器可读结果齐全（12分）。A2: 科学结论保真，实测 5/6 assay 支持 LM>基线 的主论断，对 GFP 反例进行了基于多重突变和浅比对的科学归因，结论 supported 合理（33分）。A3: 方法严谨，采用 masked-marginal 及正确的氨基酸重整化，零样本无泄漏，提供完整代码与中间打分文件支持复算（15分）。 |
| B 真值一致性/可验证性 | 38.0 | 40 | truth_check=matched | 1. agent数：ESM-2 650M 在 5/6 assay 上 Spearman ρ 优于 BLOSUM62（均值 0.463 vs 0.245） vs 锚点：LM ≥ 简单基线（多数 assay 成立） → 吻合。2. agent数：GFP assay (MSA Neff=14.9, 浅比对) 单序列 LM ρ=0.108 表现最差 vs 锚点：浅比对（Neff 小）的蛋白单序列 LM 弱，需检索/MSA 补强 → 吻合。3. agent数：6 个 assay 变体数在 1195~51714 之间 vs 锚点：每个 assay 1000-20万+突变 → 吻合。 |

## A 核心结果达成度（60.0/60 = A1 12.0 + A2 33.0 + A3 15.0）

A1: 核心交付物完整，包含 metrics.json、evidence_table.csv 及可运行代码，机器可读结果齐全（12分）。A2: 科学结论保真，实测 5/6 assay 支持 LM>基线 的主论断，对 GFP 反例进行了基于多重突变和浅比对的科学归因，结论 supported 合理（33分）。A3: 方法严谨，采用 masked-marginal 及正确的氨基酸重整化，零样本无泄漏，提供完整代码与中间打分文件支持复算（15分）。

## B 真值一致性/可验证性（38.0/40）[truth_check=matched]

1. agent数：ESM-2 650M 在 5/6 assay 上 Spearman ρ 优于 BLOSUM62（均值 0.463 vs 0.245） vs 锚点：LM ≥ 简单基线（多数 assay 成立） → 吻合。2. agent数：GFP assay (MSA Neff=14.9, 浅比对) 单序列 LM ρ=0.108 表现最差 vs 锚点：浅比对（Neff 小）的蛋白单序列 LM 弱，需检索/MSA 补强 → 吻合。3. agent数：6 个 assay 变体数在 1195~51714 之间 vs 锚点：每个 assay 1000-20万+突变 → 吻合。

## 证据与重算说明

独立重算未执行。关键实测数：evidence_table.csv 中 BRCA1_HUMAN LM_esm2_650M ρ=0.5198，GFP_AEQVI ρ=0.1079；metrics.json 中对应值为 0.5198288 和 0.107947，内部高度一致。中间结果 CSV 文件（如 baseline_scores）证实了实际推理过程。

## 结论

- **科学结论**: `supported`
- **可验证性**: `matched`
- 亮点: 实验设计严谨，对 GFP 反例进行了深入的归因分析（多重突变+浅比对），并额外进行了 joint masked-marginal 校验，证据链完整且科学态度诚实。
- 不足: 受限于冻结数据包仅包含 6 个 assay，未能覆盖论文中 87 个 assay 的全貌，且未实现带检索的 Tranception 模型，但已在报告中充分声明。