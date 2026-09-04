# EVAL REPORT v7: 2407.01791_ubench_microscopy

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 63.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 14.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **41.0** | 60 | A1(12): 核心交付物完整，包含代码、报告、evidence_table.csv和metrics.json，机器可读结果齐全。A2(14): 结论判定为partially_supported，细粒度复现了挣扎效应，粗粒度因分片捷径饱和；受限于partially_supported结论硬上限（A2≤15），给予14分以认可其深刻的科学分析与效应复现。A3(15): 采用GroupKFold防图像级泄漏，选项mask符合Closed-VQA口径，方法严谨可复现。 |
| B 真值一致性/可验证性 | 22.0 | 40 | truth_check=diverged | agent数 coarse=100.0% vs 锚点 62.6% → 严重偏离（因单分片数据捷径导致饱和）；agent数 fine(kNN)=58.6%~67.6% vs 锚点 51.7% → 数值偏离（相对差13%~30%），但定性方向一致（均<70%体现挣扎）；agent数 fine(LP)=75.8%~81.8% vs 锚点 51.7% → 明显偏离。因实测数值与论文真值存在显著偏离，truth_check判定为diverged。Agent诚实报告了偏离并给出了深刻的数据集分析，故在diverged区间内给予中上分数22分。 |

## A 核心结果达成度（41.0/60 = A1 12.0 + A2 14.0 + A3 15.0）

A1(12): 核心交付物完整，包含代码、报告、evidence_table.csv和metrics.json，机器可读结果齐全。A2(14): 结论判定为partially_supported，细粒度复现了挣扎效应，粗粒度因分片捷径饱和；受限于partially_supported结论硬上限（A2≤15），给予14分以认可其深刻的科学分析与效应复现。A3(15): 采用GroupKFold防图像级泄漏，选项mask符合Closed-VQA口径，方法严谨可复现。

## B 真值一致性/可验证性（22.0/40）[truth_check=diverged]

agent数 coarse=100.0% vs 锚点 62.6% → 严重偏离（因单分片数据捷径导致饱和）；agent数 fine(kNN)=58.6%~67.6% vs 锚点 51.7% → 数值偏离（相对差13%~30%），但定性方向一致（均<70%体现挣扎）；agent数 fine(LP)=75.8%~81.8% vs 锚点 51.7% → 明显偏离。因实测数值与论文真值存在显著偏离，truth_check判定为diverged。Agent诚实报告了偏离并给出了深刻的数据集分析，故在diverged区间内给予中上分数22分。

## 证据与重算说明

独立重算未执行。关键实测数：evidence_table.csv中vit_base_patch16_224_knn fine=0.67562，resnet18_knn fine=0.58603，coarse均接近1.0；metrics.json中closed_vqa_questions=21900。数值在报告、CSV、JSON间完全一致，证据链完整。

## 结论

- **科学结论**: `partially_supported`
- **可验证性**: `diverged`
- 亮点: 诚实且深刻地分析了单分片粗粒度标签与数据集强相关导致的“捷径”饱和问题，证据链完整，防泄漏交叉验证方法严谨。
- 不足: 受限于离线环境无VLM权重，仅能使用ImageNet预训练特征加LP/kNN作为代理，导致粗粒度数值严重偏离论文锚值，无法直接验证GPT-4o级别的生成式VLM表现。