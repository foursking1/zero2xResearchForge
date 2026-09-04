# EVAL REPORT v7: 2401.15089_pst_matbench

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 59.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 12.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **39.0** | 60 | A1: 交付了完整的代码、metrics.json、evidence_table.csv和详细报告，机器可读结果完整，给12分。A2: 实测MAE（Gap 0.504, Form 0.167, Shear 0.108）与论文真值（0.210, 0.032, 0.074）存在显著偏离（均超出容差带），但消融实验方向与论文一致，属于定性匹配但定量偏离。受partially_supported结论硬上限（A2≤15）限制，给12分。A3: 方法严谨，采用任务允许的简化代理模型（PDD直方图+LightGBM），固定种子且使用验证集early stopping防泄漏，逻辑sound且可复现，给15分。 |
| B 真值一致性/可验证性 | 20.0 | 40 | truth_check=diverged | 真值比对：1) Band Gap MAE: agent 0.5037 vs 锚点 0.210 (容差±0.03) → 偏离；2) Formation Energy MAE: agent 0.1671 vs 锚点 0.032 (容差±0.01) → 偏离；3) Shear Modulus MAE: agent 0.1084 vs 锚点 0.074 (容差±0.01) → 偏离；4) 消融方向: agent PDD-only(0.814) > Comp(0.528) > 组合(0.516) vs 锚点 PDD(0.596) > Comp(0.273) > PST(0.212) → 绝对数值偏离，但排序方向吻合。综合判定为diverged，因绝对精度差距较大（1.5x-5x），B给20分。 |

## A 核心结果达成度（39.0/60 = A1 12.0 + A2 12.0 + A3 15.0）

A1: 交付了完整的代码、metrics.json、evidence_table.csv和详细报告，机器可读结果完整，给12分。A2: 实测MAE（Gap 0.504, Form 0.167, Shear 0.108）与论文真值（0.210, 0.032, 0.074）存在显著偏离（均超出容差带），但消融实验方向与论文一致，属于定性匹配但定量偏离。受partially_supported结论硬上限（A2≤15）限制，给12分。A3: 方法严谨，采用任务允许的简化代理模型（PDD直方图+LightGBM），固定种子且使用验证集early stopping防泄漏，逻辑sound且可复现，给15分。

## B 真值一致性/可验证性（20.0/40）[truth_check=diverged]

真值比对：1) Band Gap MAE: agent 0.5037 vs 锚点 0.210 (容差±0.03) → 偏离；2) Formation Energy MAE: agent 0.1671 vs 锚点 0.032 (容差±0.01) → 偏离；3) Shear Modulus MAE: agent 0.1084 vs 锚点 0.074 (容差±0.01) → 偏离；4) 消融方向: agent PDD-only(0.814) > Comp(0.528) > 组合(0.516) vs 锚点 PDD(0.596) > Comp(0.273) > PST(0.212) → 绝对数值偏离，但排序方向吻合。综合判定为diverged，因绝对精度差距较大（1.5x-5x），B给20分。

## 证据与重算说明

独立重算未执行。关键实测数提取自metrics.json和evidence_table.csv：mp_gap MAE 0.5037，mp_e_form MAE 0.1671，log_gvrh MAE 0.1084；消融：Comp-only 0.5275，PDD-only 0.8142，PST-ish 0.5156。证据文件齐全，内部数值严格对齐，无抄袭论文数字嫌疑。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 严格遵循了任务允许的简化代理模型方案，完整执行了5折CV协议，消融实验方向与论文完全一致，且诚实客观地分析了简化模型带来的精度局限性。
- 不足: 受限于特征简化（扁平直方图丢弃元素身份）和模型简化（LightGBM vs Transformer），绝对预测精度与论文真值差距较大（特别是Formation Energy差约5倍），未能定量复现PST的精度优势。