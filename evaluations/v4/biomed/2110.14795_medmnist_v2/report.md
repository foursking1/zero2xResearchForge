# EVAL REPORT v3: 2110.14795_medmnist_v2

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 90.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 50.0 | 60 | A1数据规模统计完全正确；A2五个数据集均独立完成训练；A3实测AUC（Blood 0.9978, Breast 0.8997, Derma 0.9302, Pneumonia 0.9701, Retina 0.7011）全部落入Rubric成功区间，难度排序与论文一致。但Pneumonia偏差2.76%、Retina偏差2.21%落入2%-10%梯度带，依据从严给分铁律，未能全部精确命中(≤2%)，故A维度总分定为50分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示证据等级为2（齐全自洽）。包含metrics.json、evidence_table.csv、split_sizes.csv及class_counts.json等详实校验证据，且提供完整可运行代码，内部数值高度自洽，无抄数嫌疑，授予满分40分。 |

## A 核心结果达成度（50.0/60）

A1数据规模统计完全正确；A2五个数据集均独立完成训练；A3实测AUC（Blood 0.9978, Breast 0.8997, Derma 0.9302, Pneumonia 0.9701, Retina 0.7011）全部落入Rubric成功区间，难度排序与论文一致。但Pneumonia偏差2.76%、Retina偏差2.21%落入2%-10%梯度带，依据从严给分铁律，未能全部精确命中(≤2%)，故A维度总分定为50分。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示证据等级为2（齐全自洽）。包含metrics.json、evidence_table.csv、split_sizes.csv及class_counts.json等详实校验证据，且提供完整可运行代码，内部数值高度自洽，无抄数嫌疑，授予满分40分。

## 证据与重算说明

独立重算未执行。关键实测数：BloodMNIST test AUC=0.9978, ACC=0.9640；RetinaMNIST test AUC=0.7011, ACC=0.4625。各数据集规模与冻结数据说明一致，所有实测数值在evidence_table.csv、metrics.json、report.md中完全对应。

## 结论

- **科学结论**: `supported`
- 亮点: 复现工作极其严谨，代码结构清晰，防泄漏设计完善，证据文件详实且内部数值严格一致，难度排序完美复现。
- 不足: Pneumonia和Retina的AUC与论文锚值偏差略超2%（分别为2.76%和2.21%），且单一种子运行未提供方差估计。