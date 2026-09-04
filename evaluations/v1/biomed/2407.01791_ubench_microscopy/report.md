# EVAL REPORT: 2407.01791_ubench_microscopy

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判（qwen3.7-max）
- 评测时间: 2026-08-20

## 总分: 80.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 40.0 | 60 | A1: agent 报告最优模型 coarse=100.0%；rubric band 表：[相对差≤25%→20分]，[相对差≤50%→10分]，[严重偏离→0-5分]；100.0% 相对论文 62.6% 的相对差为 59.7%，大于 50%，落入严重偏离区间 → 5分。A2: agent 报告 ResNet-18 kNN fine=58.6%；rubric band 表：[39%-65%→20分]；58.6% 落入该满分区间 → 20分（注：ViT LP 81.8% 偏离，但 kNN 作为零样本代理落入满分带，予以认可）。A3: agent 模型 coarse 均 ~100%，不满足“均<80%”条件；但结论标签 partially_supported 与证据（fine<70% 挣扎，coarse 因分片捷径饱和）高度一致，满足“结论标签与证据一致” → 15分。A总分=40。 |
| B 证据真实性 | 25 | 25 | 提交物齐全，包含 code/ 与 results/。抽查 evidence_table.csv 中 vit_base_patch16_224_linear_probe coarse accuracy=1.0，metrics.json 中 n_items (coarse=18250, fine=3650) 均存在且内部一致。论文数值与实测严格区分，未将论文数字冒充实测。独立重算未执行。给满分 25。 |
| C 方法与报告 | 15 | 15 | C1(5分)：方法合理，采用冻结感知编码器+LP/kNN 作为代理，符合无 GPU 环境设定；C2(5分)：诚实性极佳，明确指出单分片 coarse 标签与数据集强相关导致 100% 饱和的“捷径”问题，不冒充全量；C3(5分)：报告结构完整，局限分析深刻。C总分=15。 |

## A 核心结果达成度（40.0/60）

A1: agent 报告最优模型 coarse=100.0%；rubric band 表：[相对差≤25%→20分]，[相对差≤50%→10分]，[严重偏离→0-5分]；100.0% 相对论文 62.6% 的相对差为 59.7%，大于 50%，落入严重偏离区间 → 5分。A2: agent 报告 ResNet-18 kNN fine=58.6%；rubric band 表：[39%-65%→20分]；58.6% 落入该满分区间 → 20分（注：ViT LP 81.8% 偏离，但 kNN 作为零样本代理落入满分带，予以认可）。A3: agent 模型 coarse 均 ~100%，不满足“均<80%”条件；但结论标签 partially_supported 与证据（fine<70% 挣扎，coarse 因分片捷径饱和）高度一致，满足“结论标签与证据一致” → 15分。A总分=40。

## B 证据真实性（25/25）

提交物齐全，包含 code/ 与 results/。抽查 evidence_table.csv 中 vit_base_patch16_224_linear_probe coarse accuracy=1.0，metrics.json 中 n_items (coarse=18250, fine=3650) 均存在且内部一致。论文数值与实测严格区分，未将论文数字冒充实测。独立重算未执行。给满分 25。

## C 方法与报告（15/15）

C1(5分)：方法合理，采用冻结感知编码器+LP/kNN 作为代理，符合无 GPU 环境设定；C2(5分)：诚实性极佳，明确指出单分片 coarse 标签与数据集强相关导致 100% 饱和的“捷径”问题，不冒充全量；C3(5分)：报告结构完整，局限分析深刻。C总分=15。

## 证据与重算说明

独立重算未执行。抽查关键实测数：evidence_table.csv 中 vit_base_patch16_224_linear_probe coarse=1.0, fine=0.81836；resnet18_knn fine=0.58603。metrics.json 中 closed_vqa_questions=21900, coarse_n_items=18250, fine_n_items=3650。数值在 report、claim、csv、json 间完全一致。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 诚实且深刻地分析了单分片粗粒度标签与数据集强相关导致的“捷径”饱和问题，结论判定 partially_supported 逻辑严密；代码与证据链完整，论文锚值与实测区分清晰。
- 不足: 受限于离线无 VLM 权重，仅能使用 ImageNet 预训练特征加 LP/kNN 作为代理，与论文 GPT-4o 的生成式 VLM 评测口径存在本质差异，导致粗粒度数值严重偏离论文锚值。