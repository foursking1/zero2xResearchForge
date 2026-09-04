# EVAL REPORT: 2110.14795_medmnist_v2

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判（qwen3.7-max）
- 评测时间: 2026-08-20

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1: agent报告的数据集规模（如Blood 11959/1712/3421等）与TASK说明完全一致，得20分。A2: 5个数据集均使用ResNet-18独立训练并输出AUC/ACC，全部完成，得20分。A3: agent报告test AUC分别为Blood 0.9978(≥0.97)、Breast 0.8997(≥0.85)、Derma 0.9302(≥0.86)、Pneumonia 0.9701(≥0.89)、Retina 0.7011(0.63-0.80)，全部落入rubric指定区间；难度排序blood>pneumonia>derma>breast>retina与论文锚完全一致，得20分。A总计60分。 |
| B 证据真实性 | 25 | 25 | 提交物包含完整的code/与results/目录，代码逻辑清晰。evidence_table.csv与metrics.json中明确区分了paper_auc与实测test_auc，未将论文数字当作实测。各文件（report, claim, csv, json）内部数值高度一致。因环境限制独立重算未执行，但基于证据链完整性与内部一致性，给满分25分。 |
| C 方法与报告 | 15 | 15 | C1(5分): 采用ResNet-18并适配28x28 stem，使用官方macro ovr AUC口径，方法合理。C2(5分): 代码中明确归一化统计量仅来自train，早停与学习率调度仅依赖val，test仅评估一次，防泄漏措施严密。C3(5分): report.md包含方法、结果、局限讨论及明确的supported结论标签。C总计15分。 |

## A 核心结果达成度（60/60）

A1: agent报告的数据集规模（如Blood 11959/1712/3421等）与TASK说明完全一致，得20分。A2: 5个数据集均使用ResNet-18独立训练并输出AUC/ACC，全部完成，得20分。A3: agent报告test AUC分别为Blood 0.9978(≥0.97)、Breast 0.8997(≥0.85)、Derma 0.9302(≥0.86)、Pneumonia 0.9701(≥0.89)、Retina 0.7011(0.63-0.80)，全部落入rubric指定区间；难度排序blood>pneumonia>derma>breast>retina与论文锚完全一致，得20分。A总计60分。

## B 证据真实性（25/25）

提交物包含完整的code/与results/目录，代码逻辑清晰。evidence_table.csv与metrics.json中明确区分了paper_auc与实测test_auc，未将论文数字当作实测。各文件（report, claim, csv, json）内部数值高度一致。因环境限制独立重算未执行，但基于证据链完整性与内部一致性，给满分25分。

## C 方法与报告（15/15）

C1(5分): 采用ResNet-18并适配28x28 stem，使用官方macro ovr AUC口径，方法合理。C2(5分): 代码中明确归一化统计量仅来自train，早停与学习率调度仅依赖val，test仅评估一次，防泄漏措施严密。C3(5分): report.md包含方法、结果、局限讨论及明确的supported结论标签。C总计15分。

## 证据与重算说明

独立重算未执行。抽查关键实测数值：BloodMNIST test AUC=0.9978, ACC=0.9640；RetinaMNIST test AUC=0.7011, ACC=0.4625；各数据集train/test规模（如Blood 11959/3421）与冻结数据说明一致。所有实测数值在evidence_table.csv、metrics.json、report.md和claim.md中完全对应，无抄数嫌疑。

## 结论

- **科学结论**: `supported`
- 亮点: 复现工作极其严谨，代码结构清晰，防泄漏设计完善，且对模型stem适配和AUC计算口径等细节进行了充分说明，结果与论文锚值高度吻合。
- 不足: RetinaMNIST的ACC(0.4625)与论文(0.524)存在一定偏差，虽在AUC容差范围内且agent在局限中做了解释，但单一种子运行未提供方差估计。