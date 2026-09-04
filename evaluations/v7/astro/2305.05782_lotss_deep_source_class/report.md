# EVAL REPORT v7: 2305.05782_lotss_deep_source_class

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 100.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 33.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **60.0** | 60 | A1(12): 提交了完整的claim.md、code、evidence_table.csv、metrics.json和report.md，核心交付物齐全且机器可读。A2(33): 实测数值与PAPER_ANCHOR真值逐项精确吻合，包括三场行数、五类计数、百分比及流量分箱特征，科学结论完全保真。A3(15): 方法严谨，代码逻辑为纯FITS读取与计数，并进行了主/扩展表比对及flag重建交叉验证，sound且完全可复现。 |
| B 真值一致性/可验证性 | 40 | 40 | truth_check=matched | truth_check=matched。逐条比对：1) 总行数 agent 81,951 vs 锚点 81,951 → 吻合；2) en1 SFG计数 agent 22,720 vs 锚点 22,720 → 吻合；3) 总计RQAGN agent 7,442 vs 锚点 7,442 → 吻合；4) 可靠分类率 agent 94.7% vs 锚点 94.7% → 吻合；5) ELAIS-N1 <100μJy SFG占比 agent 84.1% vs 锚点 84.1% → 吻合；6) 50%交叉点 agent 0.99 mJy vs 锚点 ~1 mJy (容差0.5-2.5) → 吻合。所有关键指标均在容差内精确匹配。 |

## A 核心结果达成度（60.0/60 = A1 12.0 + A2 33.0 + A3 15.0）

A1(12): 提交了完整的claim.md、code、evidence_table.csv、metrics.json和report.md，核心交付物齐全且机器可读。A2(33): 实测数值与PAPER_ANCHOR真值逐项精确吻合，包括三场行数、五类计数、百分比及流量分箱特征，科学结论完全保真。A3(15): 方法严谨，代码逻辑为纯FITS读取与计数，并进行了主/扩展表比对及flag重建交叉验证，sound且完全可复现。

## B 真值一致性/可验证性（40/40）[truth_check=matched]

truth_check=matched。逐条比对：1) 总行数 agent 81,951 vs 锚点 81,951 → 吻合；2) en1 SFG计数 agent 22,720 vs 锚点 22,720 → 吻合；3) 总计RQAGN agent 7,442 vs 锚点 7,442 → 吻合；4) 可靠分类率 agent 94.7% vs 锚点 94.7% → 吻合；5) ELAIS-N1 <100μJy SFG占比 agent 84.1% vs 锚点 84.1% → 吻合；6) 50%交叉点 agent 0.99 mJy vs 锚点 ~1 mJy (容差0.5-2.5) → 吻合。所有关键指标均在容差内精确匹配。

## 证据与重算说明

独立重算未执行（基于代码逻辑与落盘文件一致性核对）。关键实测数 total_rows=81951、en1 SFG=22720、总计 RQAGN=7442 均在 results/metrics.json 与 results/evidence_table.csv 中一致体现，证据等级为2（齐全自洽且与真值吻合）。

## 结论

- **科学结论**: `supported`
- **可验证性**: `matched`
- 亮点: 精确复现了论文Table 2的所有计数与百分比，并通过多重交叉验证（主/扩展表比对、flag重建）保证了结果的严谨性；对低流量端口径差异的归因专业且合理。
- 不足: 裁判未独立重跑代码验证抽查数，仅依赖落盘文件与代码逻辑的静态核对；ELAIS-N1最暗箱样本量较小带来的插值敏感性已在报告中充分讨论，无明显实质弱点。