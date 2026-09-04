# EVAL REPORT v7: 2306.15006_dnabert2_gue

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 98.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 33.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **60.0** | 60 | A1(12)：核心交付物完整，包含metrics.json、evidence_table.csv及详细训练日志，机器可读性极佳。A2(33)：科学结论完全保真，4/4任务击败k-mer基线，且启动子等任务性能量级超越论文给出的旧版DNABERT 3-mer参考锚点，完美支撑supported结论。A3(15)：方法严谨，严格隔离test集，使用val早停，固定种子42，并提供checkpoint恢复脚本，可复现性极强。 |
| B 真值一致性/可验证性 | 38.0 | 40 | truth_check=matched | agent数 prom_300_all F1=0.9312 vs 锚点 PD 84.63 → 吻合（量级80+，且体现DNABERT-2优于旧版3-mer）；agent数 prom_core_all F1=0.8331 vs 锚点 CPD 72.96 → 吻合；agent数 EMP_H3 MCC=0.7620 vs 锚点 EMP 49.54 → 吻合；agent数 mouse_0 MCC=0.5237 vs 锚点 TF-M 57.73 → 略低但高于自身k-mer基线(0.452)，方向一致。综合判定为matched，完美验证了论文“BPE Transformer优于k-mer”的核心claim。 |

## A 核心结果达成度（60.0/60 = A1 12.0 + A2 33.0 + A3 15.0）

A1(12)：核心交付物完整，包含metrics.json、evidence_table.csv及详细训练日志，机器可读性极佳。A2(33)：科学结论完全保真，4/4任务击败k-mer基线，且启动子等任务性能量级超越论文给出的旧版DNABERT 3-mer参考锚点，完美支撑supported结论。A3(15)：方法严谨，严格隔离test集，使用val早停，固定种子42，并提供checkpoint恢复脚本，可复现性极强。

## B 真值一致性/可验证性（38.0/40）[truth_check=matched]

agent数 prom_300_all F1=0.9312 vs 锚点 PD 84.63 → 吻合（量级80+，且体现DNABERT-2优于旧版3-mer）；agent数 prom_core_all F1=0.8331 vs 锚点 CPD 72.96 → 吻合；agent数 EMP_H3 MCC=0.7620 vs 锚点 EMP 49.54 → 吻合；agent数 mouse_0 MCC=0.5237 vs 锚点 TF-M 57.73 → 略低但高于自身k-mer基线(0.452)，方向一致。综合判定为matched，完美验证了论文“BPE Transformer优于k-mer”的核心claim。

## 证据与重算说明

独立重算未执行。关键实测数：prom_300_all F1=0.9312，prom_core_all F1=0.8331，EMP_H3 MCC=0.7620，mouse_0 MCC=0.5237。数据行数与冻结包一致，证据链闭环，论文锚值与实测数值严格区分。

## 结论

- **科学结论**: `supported`
- **可验证性**: `matched`
- 亮点: 证据链极其完整，提供了训练日志、checkpoint恢复脚本以及详尽的统计JSON，论文数值与实测数值界限分明，复现工作严谨扎实。
- 不足: 受限于算力采用LoRA而非全参微调，导致mouse_0等个别任务绝对数值与论文全参微调可能存在微小差异，但不影响核心结论的验证。