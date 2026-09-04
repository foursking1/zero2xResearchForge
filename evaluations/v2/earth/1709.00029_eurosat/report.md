# EVAL REPORT v2: 1709.00029_eurosat

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | Agent报告实测OA=97.9074%，论文锚值98.57%，相对差d=0.67%。根据rubric，d≤5%落入55-60分区间。因metrics.json与evidence_table.csv落盘且数值一致，证据齐全，基础分给57分。Agent在analysis.json中提供了详细的混淆对分析与推理期通道敏感性诊断，满足附加分析+3分条件，最终A得60分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘扫描显示metrics.json、evidence_table.csv、confusion_matrix.csv等实测证据文件齐全，可运行代码完整。内部数值严格一致：evidence_table中overall行tp=5287、fn=113、accuracy=0.979074，与metrics.json的overall_accuracy完全吻合；混淆矩阵对角线之和5287亦与tp一致。无抄袭锚值迹象，符合「有证据文件且数值与报告严格一致、可核对」的最高档，B给40分。 |

## A 核心结果达成度（60/60）

Agent报告实测OA=97.9074%，论文锚值98.57%，相对差d=0.67%。根据rubric，d≤5%落入55-60分区间。因metrics.json与evidence_table.csv落盘且数值一致，证据齐全，基础分给57分。Agent在analysis.json中提供了详细的混淆对分析与推理期通道敏感性诊断，满足附加分析+3分条件，最终A得60分。

## B 证据真实性/实际复现（40/40）

磁盘扫描显示metrics.json、evidence_table.csv、confusion_matrix.csv等实测证据文件齐全，可运行代码完整。内部数值严格一致：evidence_table中overall行tp=5287、fn=113、accuracy=0.979074，与metrics.json的overall_accuracy完全吻合；混淆矩阵对角线之和5287亦与tp一致。无抄袭锚值迹象，符合「有证据文件且数值与报告严格一致、可核对」的最高档，B给40分。

## 证据与重算说明

独立重算未执行。关键实测数：test OA=97.9074%（metrics.json与evidence_table.csv严格一致），多数类基线=10.259%，混淆矩阵对角线总和5287/5400=0.979074。论文锚值98.57%仅作为对比基准，未被当作实测结果。

## 结论

- **科学结论**: `supported`
- 亮点: 复现精度极高（OA 97.91%），核心证据链完整且内部数值严格一致；附加的通道敏感性诊断和混淆对分析深入，充分解释了RGB-only与多光谱的边界。
- 不足: README.md中存在早期占位符未更新的笔误（如'overall accuracy ≈ 95.%'和'baseline ≈ 18–19%'），与report.md及metrics.json中的真实数值不符，虽不影响核心证据有效性，但略显瑕疵。