# EVAL REPORT v3: 1912.12171_so2sat

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 49.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 14.0 | 60 | 实测OA=0.9747，锚值OA=0.61，相对差d≈59.78%。按数值带匹配铁律，d>50%落入0-11分带，基础分给11分。附加S1+S2与S2-only双口径报告+3分，最终A=14分。虽然Agent合理解释了OA虚高是因为冻结validation集内部空间自相关，但绝对数值未逼近锚值，严格按rubric字面区间给分。 |
| B 证据真实性/实际复现 | 35.0 | 40 | 磁盘证据扫描显示证据等级为2，metrics.json、evidence_table、代码等齐全。核心指标OA=0.974699在metrics.json、evidence_table和报告间严格一致。但部分基线的evidence_table整体行f1=9.000000存在明显异常（代码bug），自洽性一般，扣除部分分数，给35分。 |

## A 核心结果达成度（14.0/60）

实测OA=0.9747，锚值OA=0.61，相对差d≈59.78%。按数值带匹配铁律，d>50%落入0-11分带，基础分给11分。附加S1+S2与S2-only双口径报告+3分，最终A=14分。虽然Agent合理解释了OA虚高是因为冻结validation集内部空间自相关，但绝对数值未逼近锚值，严格按rubric字面区间给分。

## B 证据真实性/实际复现（35.0/40）

磁盘证据扫描显示证据等级为2，metrics.json、evidence_table、代码等齐全。核心指标OA=0.974699在metrics.json、evidence_table和报告间严格一致。但部分基线的evidence_table整体行f1=9.000000存在明显异常（代码bug），自洽性一般，扣除部分分数，给35分。

## 证据与重算说明

独立重算未执行。关键实测数（落盘）：overall_accuracy=0.974699，kappa=0.972313，train_size=19297，seed=42。SVM基线OA=0.6748。数据冗余分析（redundancy_nn.json）显示83.7%同标签近邻，解释了OA膨胀原因。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 实验设计严谨，主动量化了冻结validation.h5内部的空间自相关，对OA远超论文锚值给出了有充分落盘证据支撑的协议差异解释。
- 不足: 绝对值0.975与锚值0.61相对差约60%，严格意义上的“逼近0.61”未复现；部分evidence_table整体行f1=9.000000为明显异常值，影响证据洁净度。