# PAPER_ANCHOR（私有）：2604.15560 ExoNet

来源：arXiv:2604.15560v3（Islam, 2026）Abstract、§III.A（数据口径）、§IV（结果）；作者 GitHub README "Key Results" 表与 Zenodo 19708949 目录。全部数值摘自论文，禁止臆造。

## 锚 A1 — KOI 二分类判别力（核心结果锚）

| 项 | 值 |
|---|---|
| 指标名 | KOI 二分类（CONFIRMED vs FALSE POSITIVE）test AUC / accuracy；validation AUC |
| 论文数值 | **test AUC = 0.9549**；validation AUC = 0.9487；accuracy = 86.3% |
| 出处 | Abstract（"achieves a validation AUC of 0.9487 and a test AUC of 0.9549, with 86.3% classification accuracy"）；GitHub README Key Results 表 |
| 定义口径 | 训练集：Exoplanet Archive `CUMULATIVE` 表，CONFIRMED=1/FP=0/CANDIDATE 剔除，按 kepoi_name 去重，7,585 样本（2,746+4,839，1:1.76）；模态 = 相位折叠光变（全局+局部 1001 bins）+ 8 恒星参数（period/depth/radius/Teq/Teff/logg/[Fe/H]）；1D CNN+8头MHA+残差融合 |
| 容差 | A 维度主判分：agent 在冻结 KOI 目录（特征版）上报告的 AUC 与 0.9549 相对差 ≤10% 满分；≤30% 半满；>30% 0 分（见 SCORE_RUBRIC） |

## 锚 A2 — TESS 迁移高置信计数（次要结果锚 + B 维度抽查基准）

| 项 | 值 |
|---|---|
| 指标名 | 未见 TESS PC 候选上的高置信计数 |
| 论文数值 | 推断集 4,720 个 PC 候选 → **1,754 个 ≥70% 高置信**；其中 **1,098 个 ≥85%**；**52 个 HZ（200–400K）**；**6 个 rocky（Rp<1.6R⊕）HZ**；top 候选 TOI-5728.01（94.2%）、TOI-6716.01（92.2%） |
| 出处 | Abstract（"yields 1,754 high-confidence signals (≥70%), of which 1,098 surpass the 85% ... Fifty-two reside in the habitable-zone temperature range of 200–400 K; among these, six have radii below 1.6 R⊕"）；GitHub README Key Results |
| 定义口径 | 发布目录 `exonet_candidates.csv`（冻结，1,754 行 = ≥70% 集）；HZ = eq_temp_K ∈ [200,400]；rocky = radius_earth < 1.6；阈值 0.70 / 0.85 |
| 容差 | 冻结目录逐项重算：≥70%=1754、≥85%=1098、HZ=52、rocky HZ=6（已核对一致）。B 维度抽查：agent 必须从冻结目录重算这些计数且与论文一致；A2（20 分）比较 agent 自己分类器在冻结 TOI 上的高置信计数与论文计数，相对差 ≤10% 满分 / ≤30% 半满 |

## 锚 A3 — 校准温度

| 项 | 值 |
|---|---|
| 指标名 | 温度缩放因子 T*（post-hoc Temperature Scaling） |
| 论文数值 | **T* = 1.573** |
| 出处 | Abstract（"post-hoc Temperature Scaling (T*=1.573)"）；GitHub README（models/temperature.json） |
| 定义口径 | 对 logits 除以 T 使概率校准；论文未公开模型权重（README 称权重在 Zenodo，本包未含） |
| 容差 | 本数据不可直接重算 T*（无 logits/权重）；判定为"校准声明在冻结数据上的可检验性"分析（C 维度），非数值锚 |

## 辅助事实（冻结数据重算，裁判 B 维度抽查用）

| 字段 | 冻结值 | 说明 |
|---|---|---|
| KOI 人口 | 9,564 行；CONFIRMED 2,747 / FP 4,839 / CANDIDATE 1,978；去重后无重复 kepoi_name | 论文 7,585 vs 冻结 7,586（+1，快照漂移） |
| TESS PC 人口 | 4,927（论文 4,720，+207 快照漂移） | 冻结 `tess_toi_pc.csv` |
| 发布目录计数 | ≥70% 1,754；≥85% 1,098；HZ 52；rocky HZ 6 | 冻结 `exonet_candidates.csv`，已核对 |