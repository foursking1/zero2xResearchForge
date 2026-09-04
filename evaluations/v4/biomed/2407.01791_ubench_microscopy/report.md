# EVAL REPORT v3: 2407.01791_ubench_microscopy

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v4（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 80.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 40.0 | 60 | A1（粗粒度）：Agent报告最优模型coarse准确率为100.0%，相对论文锚值62.6%的相对差为59.7%，大于50%，落入“严重偏离”区间，得5分。A2（细粒度）：Agent报告ResNet-18 kNN细粒度准确率为58.6%，严格落入Rubric规定的39%-65%满分区间，得20分。A3（挣扎论断）：Agent模型coarse均~100%，不满足“均<80%”条件，但结论标签partially_supported与证据（fine<70%挣扎，coarse因分片捷径饱和）高度一致，满足“结论标签与证据一致”，得15分。A总分40。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示metrics.json与evidence_table.csv等实测证据文件齐全，证据等级为2。抽查evidence_table.csv中vit_base_patch16_224_linear_probe coarse accuracy=1.0、n_items=18250，与metrics.json及报告散文严格一致。代码结构完整，论文锚值与实测数值严格区分，无抄袭或测试段泄漏。给40分。 |

## A 核心结果达成度（40.0/60）

A1（粗粒度）：Agent报告最优模型coarse准确率为100.0%，相对论文锚值62.6%的相对差为59.7%，大于50%，落入“严重偏离”区间，得5分。A2（细粒度）：Agent报告ResNet-18 kNN细粒度准确率为58.6%，严格落入Rubric规定的39%-65%满分区间，得20分。A3（挣扎论断）：Agent模型coarse均~100%，不满足“均<80%”条件，但结论标签partially_supported与证据（fine<70%挣扎，coarse因分片捷径饱和）高度一致，满足“结论标签与证据一致”，得15分。A总分40。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示metrics.json与evidence_table.csv等实测证据文件齐全，证据等级为2。抽查evidence_table.csv中vit_base_patch16_224_linear_probe coarse accuracy=1.0、n_items=18250，与metrics.json及报告散文严格一致。代码结构完整，论文锚值与实测数值严格区分，无抄袭或测试段泄漏。给40分。

## 证据与重算说明

独立重算未执行。关键实测数：evidence_table.csv中vit LP coarse=1.0, fine=0.81836；resnet18 knn fine=0.58603。metrics.json中closed_vqa_questions=21900, coarse_n_items=18250, fine_n_items=3650。数值在报告、CSV、JSON间完全一致，证据链完整。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 诚实且深刻地分析了单分片粗粒度标签与数据集强相关导致的“捷径”饱和问题，结论判定逻辑严密；代码与证据链完整，论文锚值与实测区分清晰。
- 不足: 受限于离线无VLM权重，仅能使用ImageNet预训练特征加LP/kNN作为代理，与论文GPT-4o的生成式VLM评测口径存在本质差异，导致粗粒度数值严重偏离论文锚值。