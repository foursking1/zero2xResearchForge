# 论文锚（私有）：1801.10193_deepdta

> 用途：LLM judge 判分基准。本卡为 L2（目标论文隐藏）；数值从 arXiv:1801.10193v2 抽出（Öztürk et al., Bioinformatics 2018, doi:10.1093/bioinformatics/bty593），禁止臆造。

## 目标论文与协议
- 论文：Öztürk, Özgür, and Ozkirimli, "DeepDTA: deep drug-target binding affinity prediction"（arXiv:1801.10193）。
- 协议：双 CNN（药物 SMILES 字符编码 + 蛋白序列字符编码）拼接 + 全连接回归；5 折交叉验证（官方 fold_setting1）；指标 CI + MSE。
- 数据：Davis（68 药物 × 442 蛋白）、KIBA（2,111 药物 × 229 蛋白，118 万对）。

## 锚 A1 — 数据集与协议（判数据正确性）
| 项 | 值 |
|---|---|
| Davis 规模 | 68 药物 / 442 蛋白 / ~30,056 对 |
| KIBA 规模 | 2,111 药物 / 229 蛋白 / ~118,254 对 |
| 划分 | 5 折（fold_setting1），test 每折 1/5 |
| 指标 | CI（Concordance Index）+ MSE |
| 出处 | §Data sets / Table 1 |

## 锚 A2 — 核心结果（Table 3/4，判 Q1-Q3 模式）
| 发现 | 论文数值 | 出处 |
|---|---|---|
| Davis：DeepDTA（CNN-CNN） | CI 0.878±0.004、MSE 0.261 | Table 3 |
| Davis：SimBoost 基线 | CI 0.872、MSE 0.282 | Table 3 |
| Davis：KronRLS 基线 | CI 0.871、MSE 0.379 | Table 3 |
| KIBA：DeepDTA（CNN-CNN） | CI 0.863±0.002、MSE 0.194 | Table 4 |
| KIBA：SimBoost 基线 | CI 0.836、MSE 0.222 | Table 4 |
| KIBA：KronRLS 基线 | CI 0.782、MSE 0.411 | Table 4 |
| 主论断 | 序列深度模型达到/超过相似度基线；在更大数据集（KIBA）上提升更显著（CI 0.836→0.863 vs Davis 0.872→0.878） | §Results |

## 判分对照速查
- A1 满分：数据事实正确（68/442、2111/229、亲和力方向、5 折）。
- A2 满分：agent 在冻结数据上独立实现深度模型 + 基线，深度模型 CI 不低于基线（Davis、KIBA 至少一个显著占优），且方向与论文一致。
- 容差：绝对 CI 受实现影响（±0.05 内判方向一致）；「深度 ≥ 基线」为主判据；KIBA 上相对优势 ≥ Davis 为加分模式。
- B 抽查：从冻结数据重算 Davis 对数量（68×442）与 KIBA 矩阵非空对数量；重跑 agent 代码核对某折 CI。
