# EVAL REPORT v2: 2110.14795_medmnist_v2

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1(20分): agent在split_sizes.csv和class_counts.json中准确统计了5个数据集的train/val/test规模，与TASK说明完全一致。A2(20分): 5个数据集均使用ResNet-18独立训练并输出AUC/ACC，全部完成。A3(20分): 实测test AUC分别为Blood 0.9978、Breast 0.8997、Derma 0.9302、Pneumonia 0.9701、Retina 0.7011，全部落入rubric指定区间；难度排序blood>pneumonia>derma>breast>retina与论文锚完全一致。所有数值均有metrics.json和evidence_table.csv落盘支撑，故各子项均给满分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示metrics.json、evidence_table.csv等实测证据文件齐全，且包含完整的可运行代码(train.py等)。核对evidence_table.csv与metrics.json中的AUC/ACC数值（如Blood AUC 0.9978，Retina AUC 0.7011）与report.md及claim.md中的报告数值严格一致，证据链完整且无抄数嫌疑，属于最高档[30,40]，给40分。 |

## A 核心结果达成度（60/60）

A1(20分): agent在split_sizes.csv和class_counts.json中准确统计了5个数据集的train/val/test规模，与TASK说明完全一致。A2(20分): 5个数据集均使用ResNet-18独立训练并输出AUC/ACC，全部完成。A3(20分): 实测test AUC分别为Blood 0.9978、Breast 0.8997、Derma 0.9302、Pneumonia 0.9701、Retina 0.7011，全部落入rubric指定区间；难度排序blood>pneumonia>derma>breast>retina与论文锚完全一致。所有数值均有metrics.json和evidence_table.csv落盘支撑，故各子项均给满分。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示metrics.json、evidence_table.csv等实测证据文件齐全，且包含完整的可运行代码(train.py等)。核对evidence_table.csv与metrics.json中的AUC/ACC数值（如Blood AUC 0.9978，Retina AUC 0.7011）与report.md及claim.md中的报告数值严格一致，证据链完整且无抄数嫌疑，属于最高档[30,40]，给40分。

## 证据与重算说明

独立重算未执行。关键实测数：BloodMNIST test AUC=0.9978, ACC=0.9640；RetinaMNIST test AUC=0.7011, ACC=0.4625。各数据集规模（如Blood 11959/3421）与冻结数据说明一致。所有实测数值在evidence_table.csv、metrics.json、report.md中完全对应。

## 结论

- **科学结论**: `supported`
- 亮点: 复现工作极其严谨，代码结构清晰，防泄漏设计完善，结果与论文锚值高度吻合，证据文件详实且内部数值严格一致。
- 不足: RetinaMNIST的ACC(0.4625)与论文(0.524)存在一定偏差，虽在AUC容差范围内且agent在局限中做了解释，但单一种子运行未提供方差估计。