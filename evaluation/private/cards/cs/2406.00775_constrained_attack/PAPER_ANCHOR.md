# PAPER_ANCHOR（私有，仅裁判/编译者可见）：2406.00775_constrained_attack

> 用途：LLM judge 判分基准。本卡为 L1（critical claim，论文公开，但锚值仅本文件可见）。所有数值从 arXiv:2406.00775v1 抽出（§5 Experimental settings、Table 2/Table 3/Table 5、Algorithm 1），禁止臆造。

## 目标论文

- Simonetto, T., Ghamizi, S., Cordy, M. (2024), "Constrained Adaptive Attack: Effective Adversarial Attack Against Deep Neural Networks for Tabular Data"（arXiv:2406.00775v1，Preprint/Under review）。
- 核心论断：CAPGD（约束自适应 PGD）显著优于既有梯度攻击 CPGD/LowProFool；CAA（CAPGD+MOEVA）在 20 个设置中 17 个优于既有攻击。

## 锚 A1 — CAPGD 相对 CPGD 的优势（Table 2 URL 块，判 A1 维度）

| 项 | 值 |
|---|---|
| 指标名 | 鲁棒准确率（%，攻击后仍被正确分类或生成无效样本的干净关键类样本比例；L2，ε=0.5） |
| 论文数值（URL） | TabTransformer：Clean 93.6 / CPGD 91.9 / **CAPGD 10.9**；RLN：94.4 / 92.8 / **12.6**；TabNet：93.4 / 88.5 / **19.3**；VIME：92.5 / 90.7 / **56.3**；STG：93.3 / 93.3 / **72.6** |
| 出处 | Table 2（Robust accuracy against CAPGD and SOTA gradient attacks，URL 数据集 5 行）；§4.2 正文（"decreases the robust accuracy on URL... to as low as 10.9%"） |
| 判分口径 | agent 用本包 URL 数据训练深层模型 + 实现 CPGD/CAPGD，报鲁棒准确率对比 |

## 锚 A2 — CAA 组合攻击的效果（Table 3 URL 块，辅助/方向校验）

| 项 | 值 |
|---|---|
| 指标名 | 鲁棒准确率（CAA vs MOEVA vs CAPGD） |
| 论文数值（URL） | TabTransformer：CAPGD 10.9 / MOEVA 18.2 / **CAA 8.9**；RLN：12.6 / 23.6 / **10.8**；TabNet：19.3 / 17.5 / **11.0**；VIME：56.3 / 56.5 / **49.5**；STG：72.6 / 58.2 / **58.0** |
| 出处 | Table 3（URL 块；"CAA outperforms all existing attacks in 17 over the 20 settings"） |
| 判分口径 | 若 agent 实现了 CAA（CAPGD+搜索），检查 CAA ≤ MOEVA；否则此锚仅作背景 |

## 锚 A3 — 数据规模口径（Table 5，判 B 维度）

| 项 | 值 |
|---|---|
| 指标名 | URL 数据集规模/特征数/平衡度 |
| 论文数值 | 11,430 样本 / 63 特征 / 50-50 平衡（Table 5） |
| 出处 | Table 5 |
| 判分口径 | 冻结 url.csv 应为 11,430 行 × 64 列（63 特征 + is_phishing 标签），phishing 占比 ≈ 50% |

## 辅助数据事实（裁判 B 维度抽查基准；从冻结数据直接核验）

| 字段 | 冻结参考值 | 备注 |
|---|---|---|
| url.csv 行数/列数 | 11,430 × 64 | pandas 直接核验 |
| phishing 占比 | 50%（每类各 ~5,715） | is_phishing 列均值 ≈ 0.5 |
| 特征列顺序 | 与 url_features.csv 完全一致（length_url 为首列） | 63 特征 + 标签 |
| 每特征边界 | 扰动值须在 features.csv min/max 内 | 从冻结文件读取 |

## 判分对照速查（judge 用）

- A1 满分：≥1 个模型上 CAPGD 鲁棒准确率 ≤ CPGD − 40pp，且 CAPGD ≤ 40%（论文：91.9→10.9、92.8→12.6、88.5→19.3）。
- A2 满分：≥2 个模型上方向一致（CAPGD < CPGD）；若实现 CAA，CAA ≤ MOEVA 亦给满分参考。
- B 抽查两数：(1) url.csv 11,430×64、phishing ≈ 50%（纯数据事实）；(2) agent 报告的约束满足率（从 agent 代码+冻结约束重算，应为 ~1.0 或明确说明）。
- 容差说明：论文未开源 CAPGD/CAA 代码，模型训练与攻击实现的细节由 agent 决定 → 判分以**方向 + 量级带**为主（40pp 差距带），不要求逐值复现；ε=0.5（L2）必须遵守。