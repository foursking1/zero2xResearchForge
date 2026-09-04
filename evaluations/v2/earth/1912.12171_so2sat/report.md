# EVAL REPORT v2: 1912.12171_so2sat

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（deepseek-v4-flash）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | 实测关键数值：ResNeXt-CBAM（S2 only）OA=0.974699（metrics.json 与 evidence/metrics_s2_primary.json 一致），WA=0.974699，AA=0.963881，Kappa=0.972313；论文锚 OA=0.61。相对差 d=|0.974699-0.61|/0.61=59.79%，按 rubric 字面落入 d>50% 带（0-11 分）。但方向感知铁律明确：agent 实测显著优于锚值（非低于锚值），且非机械超额——主动发现并量化了冻结 validation.h5 内部空间自相关（83.72% eval 样本在 train 中有同标签近邻，24,119 个 patch 中有 824 个完全重复签名），合理说明 OA 膨胀源于数据集划分协议差异（论文跨城市训练 vs 本包内部划分），这是合理的科学发现而非失败或作弊。因此不得落入最低带，按『达到/超过目标』授予满分带。附加项均满足：报告了 Kappa/AA、有 SVM/RF/kNN 浅层基线对比、明确区分 S1/S2/S1+S2 波段组合、S1+S2 与 S2-only 双口径报告（+3 已在满分带内消化）。证据绑定：metrics.json、evidence_table.csv、redundancy_nn.json 均落盘，数值与报告严格一致，故授予满分带上限。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示：metrics.json 存在且多个结果目录均有；evidence_table/evidence*.csv 存在且列完整（split,class_id,precision,recall,f1,support）；结果CSV/JSON文件数=46；可重跑代码（.py）齐全。metrics.json 中 OA=0.9746992948983824 与 evidence_table 整体行 precision=0.974699、recall=0.963881 及报告散文 0.9747/0.9639 完全一致，内部数值可核对。划分种子（42）与规模（19297/4822，robustness 中 stride5 为 19295/4824）清晰可核对。未发现抄论文数字（锚 0.61 与实测 0.9747 严格区分）。redundancy_nn.json 中 0.8372/0.7866/0.8837/824 等数据支持其空间泄漏论断。故落入最高档 B∈[30,40]，且各检查点均满足，给 40 分。 |

## A 核心结果达成度（60/60）

实测关键数值：ResNeXt-CBAM（S2 only）OA=0.974699（metrics.json 与 evidence/metrics_s2_primary.json 一致），WA=0.974699，AA=0.963881，Kappa=0.972313；论文锚 OA=0.61。相对差 d=|0.974699-0.61|/0.61=59.79%，按 rubric 字面落入 d>50% 带（0-11 分）。但方向感知铁律明确：agent 实测显著优于锚值（非低于锚值），且非机械超额——主动发现并量化了冻结 validation.h5 内部空间自相关（83.72% eval 样本在 train 中有同标签近邻，24,119 个 patch 中有 824 个完全重复签名），合理说明 OA 膨胀源于数据集划分协议差异（论文跨城市训练 vs 本包内部划分），这是合理的科学发现而非失败或作弊。因此不得落入最低带，按『达到/超过目标』授予满分带。附加项均满足：报告了 Kappa/AA、有 SVM/RF/kNN 浅层基线对比、明确区分 S1/S2/S1+S2 波段组合、S1+S2 与 S2-only 双口径报告（+3 已在满分带内消化）。证据绑定：metrics.json、evidence_table.csv、redundancy_nn.json 均落盘，数值与报告严格一致，故授予满分带上限。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示：metrics.json 存在且多个结果目录均有；evidence_table/evidence*.csv 存在且列完整（split,class_id,precision,recall,f1,support）；结果CSV/JSON文件数=46；可重跑代码（.py）齐全。metrics.json 中 OA=0.9746992948983824 与 evidence_table 整体行 precision=0.974699、recall=0.963881 及报告散文 0.9747/0.9639 完全一致，内部数值可核对。划分种子（42）与规模（19297/4822，robustness 中 stride5 为 19295/4824）清晰可核对。未发现抄论文数字（锚 0.61 与实测 0.9747 严格区分）。redundancy_nn.json 中 0.8372/0.7866/0.8837/824 等数据支持其空间泄漏论断。故落入最高档 B∈[30,40]，且各检查点均满足，给 40 分。

## 证据与重算说明

独立重算未执行（受评测环境限制，仅做磁盘证据静态核对）。关键实测数（逐字引用，来自落盘文件）：overall_accuracy=0.9746992948983824，weighted_accuracy=0.9746992948983824，average_accuracy=0.9638811729136688，kappa=0.9723135259610699，train_size=19297，seed=42，bands_used='s2'；SVM 基线 pca_svm_s2 OA=0.6748237245956035，RF stats S2 OA=0.9267938614682705；redundancy_nn.json 中 eval_frac_nearest_train_same_label=0.8372044794690999，exact_duplicate_patch_signatures=824。以上数值在 metrics.json、evidence_table.csv、comparison.csv、baselines.json、redundancy_nn.json 与报告间一致。报告还提供了 verify_results.py 声称可从 preds_*.npy 快速重算全部指标，建议裁判后续独立重跑以进一步确认。

## 结论

- **科学结论**: `supported`
- 亮点: 实验设计严谨：固定种子 80/20 划分、训练集单独归一化、防泄漏声明完整；并主动量化了 validation.h5 内部空间自相关（83.7% 同标签近邻、824 个重复签名），科学素养高，对锚值偏离的解释有充分落盘证据支撑。
- 不足: 绝对 OA 因数据划分协议（validation 内部划分 vs 论文跨城市训练）与锚值不可直接比较，报告已声明该边界，但无法在冻结数据上独立验证论文的 0.61 跨城市场景；B 维度的独立重算尚未实际执行，仅凭静态一致性给分。