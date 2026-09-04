# CALIBRATION（私有）：2602.13288_cloud_telemetry_ad

> **自测执行：待评测阶段执行（本批次跳过）**。本卡不包含实测分数；以下仅为设计目标与校准杠杆。

## 1. 设计目标区间

- 层级：L1（critical claim）→ 目标区间 **40–50（±10）**。
- 预期强 agent 画像：用冻结 NAB + Microsoft 数据实现 ≥3 模型（GRU + 一个深度模型 + Isolation Forest），按 70/30 时间切分 + 训练-only 似然校准 + NAB 归一化评分，报告 5 个 Microsoft 含异常子组与 6 个 NAB 含异常子组的 per-model NAB 分，回答 claim (a)/(b)。
- 给方向提示（协议/模型/指标/防泄漏）但不给逐步代码 → 中等偏难难度（需自实现深度模型 + NAB 评分）。

## 2. 校准杠杆（如评测阶段偏差时使用）

- **A1/A2 满分带**是主要杠杆：
  - 若强 agent 得分 > 55（偏易）：收紧 A1（要求覆盖全部 5 个含异常子组 × 4 模型，且 GRU 全正判定含排序证据）；收紧 A2（要求 ≥5 个子组、归属架构数 =4）。
  - 若强 agent 得分 < 30（偏难）：放宽 A1（只要求 GRU 在 ≥3 子组为正且为唯一全正，或允许只实现 GRU+IF）；放宽 A2（覆盖 3 个子组即可）；或允许用论文 Table IV 参数范围网格搜索替代 100 次贝叶斯校准。
- **锚容差**：Table III 的 Microsoft/NAB per-model NAB 分真实有出处；NAB 分对似然窗口/校准高度敏感 → 判分以**正负号 + 排序/归属**为主（|Δ|≥15 才判显著偏离），不要求逐值复现。
- **数据口径**：只冻结 NAB + Microsoft（真实遥测，MIT 系许可）；Exathlon（合成）与 IBM（超高维）不冻结；Microsoft 子组名与论文 Table III 一一对应。

## 3. rubric 定稿说明

- A=60（A1 claim(a) 30 + A2 claim(b) 30）、B=25（冻结数据事实计数 + 重跑 agent 代码重算某子组 GRU NAB 分）、C=15（预处理/切分/校准/NAB 评分实现/防泄漏/结论）。
- L1 给方向提示；GRU 与基线必须同一协议同口径比较。
- 数据：冻结真实 NAB（Numenta，MIT 系）+ Microsoft Cloud Monitoring（Microsoft，MIT），SHA-256 固定。