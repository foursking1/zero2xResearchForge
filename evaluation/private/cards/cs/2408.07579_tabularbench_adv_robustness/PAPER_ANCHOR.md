# PAPER_ANCHOR（私有，仅裁判/编译者可见）：2408.07579 TabularBench — URL 数据集鲁棒性锚

> 用途：LLM judge 判分基准。禁止向作答 agent 暴露本文件。所有论文数值均从 arXiv:2408.07579v1 抽出，禁止臆造。

## 锚 A1 — URL 数据集事实（数据事实锚）

| 项 | 值 |
|---|---|
| 指标名 | URL use case 规模与划分 |
| 论文数值 | 总样本 **11,430**；特征 **63**（63 数值特征 + 1 标签）；约束数 14；类别不平衡 50/50（Table 2） |
| 出处 | Table 2（Properties of the use cases）；§3.3 数据增强说明（URL 增广 1,143,000 合成样本，本任务不使用合成数据） |
| 判分口径 | 冻结 `url.csv` 11,430 行 × 62 特征 + `is_phishing`；官方 DefaultSplitter（strata, random_state=42, test_size=0.2 两次）→ train 7,315 / val 1,829 / test 2,286。agent 报告该划分即正确 |

## 锚 A2 — 核心结果 C1：标准训练下 ID 接近但鲁棒悬殊（判 A1 维度）

| 项 | 值 |
|---|---|
| 指标名 | URL 数据集标准训练：5 种架构的 ID 精度范围 与 约束鲁棒精度范围 |
| 论文数值 | ID：**92.5–94.4**（跨度 1.9pp）；鲁棒：**8.9–58.0**（跨度 49.1pp） |
| 出处 | Table 3（Clean and robust performances；URL 行，standard 列：TabTr 93.6/8.9、RLN 94.4/10.8、VIME 92.5/49.5、STG 93.3/58.0、TabNet 93.4/11.0；XX/YY 中 XX=standard 训练） |
| 冻结协议参考值 | 按 TASK.md 协议（min-max、4 MLP、PGD-L2 ε=0.25）：ID 91.6–94.4（跨度 2.8pp）；鲁棒 12.4–50.9（跨度 38.5pp）；Pearson(ID,robust)=−0.98（参考脚本 `_judge/reference.py`） |
| 判分口径 | 结构性论断：clean 跨度 ≤5pp 且 robust 跨度 ≥15pp 即认为 C1 模式成立（数值带见 SCORE_RUBRIC） |

## 锚 A3 — 核心结果 C2：对抗训练显著提升鲁棒且干净精度保持（判 A2 维度）

| 项 | 值 |
|---|---|
| 指标名 | URL 数据集 AT 后鲁棒精度范围 与 干净精度范围；AT vs std 的鲁棒提升 |
| 论文数值 | AT 鲁棒：**56.2–91.8**（TabTr 56.7、RLN 56.2、VIME 69.8、STG 90.0、TabNet 91.8）；AT 干净：93.4–99.5；平均鲁棒提升 ≈ **+45pp**（std 均值 27.6 → AT 均值 72.9） |
| 出处 | Table 3（URL 行，adversarial 列，YY） |
| 冻结协议参考值 | FGSM-AT（ε=0.1）：AT 鲁棒 76.9–77.8（均值 77.6）；AT 干净 89.9–92.8（相对 std 均值 −1.5pp）；平均鲁棒提升 **+52.0pp**；鲁棒跨度从 38.5pp 缩到 0.8pp（AT 抹平架构差异） |
| 判分口径 | 结构性论断：平均鲁棒提升 ≥20pp 且平均干净精度下降 ≤5pp 即认为 C2 成立 |

## 锚 A4 — 上下文（不单独计分）：相关性论断

| 项 | 值 |
|---|---|
| 指标名 | ID 精度与约束鲁棒精度的 Pearson 相关（Table 10，URL 行） |
| 论文数值 | standard：0.19（p=0.26，不显著）；adversarial：0.7（p=3.6e-06，显著） |
| 出处 | Table 10 |
| 用途 | 辅助判断 agent 对"ID 与鲁棒关系"的讨论是否与论文一致；不单独计分（n 小时相关不稳定） |

## 辅助数据事实（裁判 B 维度抽查基准；均从冻结数据按 TASK.md 协议算出，非论文数值）

| 字段 | 冻结参考值 | 备注 |
|---|---|---|
| test 样本数 | 2,286 | 官方划分（strata, seed 42） |
| train/val/test | 7,315 / 1,829 / 2,286 | 官方划分 |
| std clean 范围 | 91.6–94.4%（均值 93.3） | 4 个推荐 MLP |
| std robust 范围 | 12.4–50.9%（均值 25.6） | PGD-L2 ε=0.25 |
| AT robust 范围 | 76.9–77.8%（均值 77.6） | FGSM-AT ε=0.1 |
| AT clean 范围 | 89.9–92.8%（均值 91.8） | clean 平均降 1.5pp |
| 平均鲁棒提升 | +52.0pp | AT − std（均值） |
| std robust 跨度 | 38.5pp | max−min |
| std clean 跨度 | 2.8pp | max−min |
| 正类率 | 50.0% | is_phishing |

## 判分对照速查（judge 用）

- C1 成立判据（对 agent 实测）：clean 跨度 ≤5pp 且 robust 跨度 ≥15pp → A1 满分 30（论文 1.9/49.1pp；参考 2.8/38.5pp）。
- C2 成立判据：平均鲁棒提升 ≥20pp 且平均 clean 下降 ≤5pp → A2 满分 30（论文 +45pp/≈0；参考 +52.0pp/−1.5pp）。
- B 抽查两数：(1) test 样本数 2,286；(2) 某模型 std robust（从 agent 代码+冻结数据重算，须与报告一致，相对差 ≤1e-6）。
- 若 agent 使用 z-score 或 ε=0.5：数值会系统性偏离参考带（robust 普遍更低），A 维度按实际值对照数值带判，C 维度扣"口径偏离未说明"。
