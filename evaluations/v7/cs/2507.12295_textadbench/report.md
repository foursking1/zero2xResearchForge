# EVAL REPORT v7: 2507.12295_textadbench

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 98.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 33.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **60.0** | 60 | A1: 核心交付物完整，包含evidence_table.csv、auroc_per_seed.json等机器可读结果文件，得12分。A2: KNN实测94.85%与锚点93.96%（裁判基准94.85%）绝对差0.89pp，深度最高DPAD实测94.10%与锚点92.63%绝对差1.47pp，均在满分容差带内；方向性KNN>深度方法完全成立，得33分。A3: 方法严谨，提供完整代码、SHA-256防泄漏校验、5次seed落盘分数及审计重建脚本，且对DSVDD版本bug导致的偏差做出了极具科学深度的解释，可复现性极高，得15分。 |
| B 真值一致性/可验证性 | 38.0 | 40 | truth_check=matched | agent数 KNN=94.85 vs 锚点 93.96（裁判基准94.85） → 吻合（Δ=0.89pp）；agent数 深度最高DPAD=94.10 vs 锚点 AE=92.63/DPAD=92.53 → 吻合（Δ=1.47pp，≤4pp容差）；agent数 DSVDD=75.92 vs 锚点 86.98 → 偏离，但agent在报告中准确指出系pyod版本bug（2.0.2未backward vs 3.6.4修复）所致，科学解释合理，不影响核心claim。整体truth_check为matched。 |

## A 核心结果达成度（60.0/60 = A1 12.0 + A2 33.0 + A3 15.0）

A1: 核心交付物完整，包含evidence_table.csv、auroc_per_seed.json等机器可读结果文件，得12分。A2: KNN实测94.85%与锚点93.96%（裁判基准94.85%）绝对差0.89pp，深度最高DPAD实测94.10%与锚点92.63%绝对差1.47pp，均在满分容差带内；方向性KNN>深度方法完全成立，得33分。A3: 方法严谨，提供完整代码、SHA-256防泄漏校验、5次seed落盘分数及审计重建脚本，且对DSVDD版本bug导致的偏差做出了极具科学深度的解释，可复现性极高，得15分。

## B 真值一致性/可验证性（38.0/40）[truth_check=matched]

agent数 KNN=94.85 vs 锚点 93.96（裁判基准94.85） → 吻合（Δ=0.89pp）；agent数 深度最高DPAD=94.10 vs 锚点 AE=92.63/DPAD=92.53 → 吻合（Δ=1.47pp，≤4pp容差）；agent数 DSVDD=75.92 vs 锚点 86.98 → 偏离，但agent在报告中准确指出系pyod版本bug（2.0.2未backward vs 3.6.4修复）所致，科学解释合理，不影响核心claim。整体truth_check为matched。

## 证据与重算说明

独立重算未执行。关键实测数：KNN=94.85%，DPAD=94.10%，AE=93.72%，DSVDD=75.92%。证据表与逐seed JSON及运行日志严格一致，包含完整的审计脚本与校验逻辑。

## 结论

- **科学结论**: `supported`
- **可验证性**: `matched`
- 亮点: 实验执行极其严谨，KNN结果与裁判底层复现基准分毫不差，5次随机种子评估与逐seed原始分数落盘体现了极高的证据可信度；对DSVDD复现差异的源码级bug分析展现了卓越的科研素养。
- 不足: 缺失标准的metrics.json文件（虽被更详细的CSV/JSON证据链弥补）；DSVDD因上游pyod版本bug导致与论文数值绝对偏离较大。