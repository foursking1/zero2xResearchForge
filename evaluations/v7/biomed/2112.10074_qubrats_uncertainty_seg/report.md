# EVAL REPORT v7: 2112.10074_qubrats_uncertainty_seg

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 98.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 33.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **60.0** | 60 | A1：核心交付物（claim.md, metrics.json, evidence_table.csv等）完整产出，且均为机器可读格式，得12分。A2：在替代数据集上精确实现了论文公式，并充分验证了“排名解耦”与“过滤有效性”两大核心方向性论断，结论supported且有扎实数据支撑，得33分。A3：采用患者级固定划分防止数据泄漏，提供独立复核脚本verify.py，方法严谨可复现，得15分。 |
| B 真值一致性/可验证性 | 38.0 | 40 | truth_check=matched | 1. 公式锚点：agent实测det_s2 WT的AUC1=0.8619, AUC2=0.1085, AUC3=0.1322，代入公式得score=0.8737，与论文Eq.1公式精确吻合。2. 排名解耦锚点：论文真值“SCAN QU-BraTS #1 / 分割 #4”（方向性），agent实测WT上det_s2 score第1但DSC第5，方向性吻合。3. 阈值演示锚点：论文真值“阈值τ降低→过滤更多FP/FN”，agent实测mcd_s0 WT在τ从100降至25时DSC从0.80升至0.95，FTP/FTN低位，方向性吻合。4. 背景真值处理：agent在metrics.json中正确列出论文真值（166例，NRS 0.14）作为对照，未混入实测，处理严谨。 |

## A 核心结果达成度（60.0/60 = A1 12.0 + A2 33.0 + A3 15.0）

A1：核心交付物（claim.md, metrics.json, evidence_table.csv等）完整产出，且均为机器可读格式，得12分。A2：在替代数据集上精确实现了论文公式，并充分验证了“排名解耦”与“过滤有效性”两大核心方向性论断，结论supported且有扎实数据支撑，得33分。A3：采用患者级固定划分防止数据泄漏，提供独立复核脚本verify.py，方法严谨可复现，得15分。

## B 真值一致性/可验证性（38.0/40）[truth_check=matched]

1. 公式锚点：agent实测det_s2 WT的AUC1=0.8619, AUC2=0.1085, AUC3=0.1322，代入公式得score=0.8737，与论文Eq.1公式精确吻合。2. 排名解耦锚点：论文真值“SCAN QU-BraTS #1 / 分割 #4”（方向性），agent实测WT上det_s2 score第1但DSC第5，方向性吻合。3. 阈值演示锚点：论文真值“阈值τ降低→过滤更多FP/FN”，agent实测mcd_s0 WT在τ从100降至25时DSC从0.80升至0.95，FTP/FTN低位，方向性吻合。4. 背景真值处理：agent在metrics.json中正确列出论文真值（166例，NRS 0.14）作为对照，未混入实测，处理严谨。

## 证据与重算说明

独立重算未执行。关键实测数抽查：evidence_table.csv中det_s2 WT score=0.8737 (AUC1=0.8619, AUC2=0.1085, AUC3=0.1322)，公式验算一致；threshold_means.csv中mcd_s0 WT τ=75时dsc=0.8562, ftp=0.1057, ftn=0.0182，多源文件交叉验证自洽。

## 结论

- **科学结论**: `supported`
- **可验证性**: `matched`
- 亮点: 实验设计严谨，完美区分了替代数据的实测值与论文背景真值，引入随机不确定性消融对照证明score度量信息量，证据链完整且高度自洽。
- 不足: 受限于10例单模态替代数据，ET/TC绝对分割精度较低，但方向性结论稳健，不构成实质扣分。