# CALIBRATION（私有）：2406.00775_constrained_attack

> **自测执行：待评测阶段执行（本批次跳过）**。本卡不包含实测分数；以下仅为设计目标与校准杠杆。

## 1. 设计目标区间

- 层级：L1（critical claim）→ 目标区间 **40–50（±10）**。
- 预期强 agent 画像：用冻结 URL 数据训练 ≥2 个深层表格模型，按 Algorithm 1 实现 CPGD/CAPGD（含 repair 算子与约束），报鲁棒准确率与约束满足率，回答 claim (a)/(b)。
- 给方向提示（指标/数据/约束/攻击设置）但不给逐步代码 → 中等难度。

## 2. 校准杠杆（如评测阶段偏差时使用）

- **A1/A2 满分带**是主要杠杆：
  - 若强 agent 得分 > 55（偏易）：收紧 A1（要求 ≥2 个模型 CAPGD ≤ CPGD − 40pp 且 CAPGD ≤ 20%）、A2（要求实现 CAA 或至少报告 MOEVA 对照）。
  - 若强 agent 得分 < 30（偏难）：放宽 A1（CAPGD ≤ CPGD − 20pp 即满分带）、允许只用 1 个模型、或允许简化约束集（只做边界约束，明确声明）。
- **锚容差**：Table 2/3 的 URL 数值（CPGD 88.5–93.3 → CAPGD 10.9–72.6；CAA 8.9–58.0）真实有出处；论文未开源 CAPGD/CAA 代码 → 判分以**方向 + 量级带**为主（40pp 差距带），不要求逐值复现。
- **数据口径**：只冻结 URL（LCLD/CTU-13 体积大、WIDS 为医学数据未冻结）；锚点全部取 URL 块；ε=0.5（L2）、关键类=phishing 必须遵守。

## 3. rubric 定稿说明

- A=60（A1 CAPGD vs CPGD 40pp 差距带 35 + A2 跨模型方向一致性 25）、B=25（url.csv 规模/占比 + 约束满足率重算）、C=15（攻击实现与 Algorithm 1 对应/约束处理/防泄漏/结论）。
- L1 给方向提示；CPGD 与 CAPGD 必须同约束集同口径对比。
- 数据：冻结真实 URL（ISCX-URL2016，TabularBench HF 镜像，MIT），SHA-256 固定。