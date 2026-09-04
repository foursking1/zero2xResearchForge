# EVAL REPORT v2: 2407.01791_ubench_microscopy

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1: Agent报告最优粗粒度accuracy为100.0%（ViT LP），相对论文62.6%偏离较大，但Agent在报告中主动发现并深刻分析了单分片粗粒度标签与数据集强相关的“捷径/数据泄漏”问题，属于合理科学发现，触发方向感知规则，给满分20分。A2: Agent报告ResNet-18 kNN细粒度accuracy为58.6%，严格落入Rubric规定的39%-65%满分区间，给20分。A3: Agent结论标签为partially_supported，与细粒度<70%挣扎、粗粒度因分片捷径饱和的实测证据高度一致，逻辑严密，给20分。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘扫描显示metrics.json、evidence_table.csv等实测证据文件齐全。抽查evidence_table.csv中vit_base_patch16_224_linear_probe coarse accuracy=1.0、n_items=18250，与metrics.json及报告散文严格一致。代码结构完整，论文锚值与实测数值严格区分，无抄袭或测试段泄漏。给满分40分。 |

## A 核心结果达成度（60/60）

A1: Agent报告最优粗粒度accuracy为100.0%（ViT LP），相对论文62.6%偏离较大，但Agent在报告中主动发现并深刻分析了单分片粗粒度标签与数据集强相关的“捷径/数据泄漏”问题，属于合理科学发现，触发方向感知规则，给满分20分。A2: Agent报告ResNet-18 kNN细粒度accuracy为58.6%，严格落入Rubric规定的39%-65%满分区间，给20分。A3: Agent结论标签为partially_supported，与细粒度<70%挣扎、粗粒度因分片捷径饱和的实测证据高度一致，逻辑严密，给20分。

## B 证据真实性/实际复现（40/40）

磁盘扫描显示metrics.json、evidence_table.csv等实测证据文件齐全。抽查evidence_table.csv中vit_base_patch16_224_linear_probe coarse accuracy=1.0、n_items=18250，与metrics.json及报告散文严格一致。代码结构完整，论文锚值与实测数值严格区分，无抄袭或测试段泄漏。给满分40分。

## 证据与重算说明

独立重算未执行。关键实测数：evidence_table.csv中vit LP coarse=1.0, fine=0.81836；resnet18 knn fine=0.58603。metrics.json中closed_vqa_questions=21900, coarse_n_items=18250, fine_n_items=3650。数值在报告、CSV、JSON间完全一致，证据链完整。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 诚实且深刻地分析了单分片粗粒度标签与数据集强相关导致的“捷径”饱和问题，结论判定逻辑严密；代码与证据链完整，论文锚值与实测区分清晰。
- 不足: 受限于离线无VLM权重，仅能使用ImageNet预训练特征加LP/kNN作为代理，与论文GPT-4o的生成式VLM评测口径存在本质差异。