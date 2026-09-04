# PAPER_ANCHOR: 2501.02144_gen_discovery_baselines（私有，禁止写入 TASK.md）

目标论文：Szymanski & Bartel, "Establishing baselines for generative discovery of inorganic crystals", arXiv:2501.02144 (2025)。以下锚均从论文正文提取（PDF 提取 + 官方仓库 README leaderboard 交叉核对），禁止臆造。

## 核心锚（可从冻结数据重算——裁判抽查路径）

### A. 中位分解能 ΔEd（med），单位 meV/atom —— 出处：Sec "Stability and novelty" / Table 1
| 方法 | 论文值 (meV/atom) | 冻结数据重算值（2026-08-13 校验） | 容差 |
|---|---|---|---|
| Random | 409 | 410 | ±10 meV/atom |
| Ion-Exchange | 85 | 85 | ±5 |
| CrystaLLM | 442 | 442 | ±10 |
| CDVAE | 207 | 207 | ±5 |
| FTCP | 205 | 206 | ±5（舍入差） |
| MatterGen | 188 | 188 | ±5 |
口径：500 个 novel 材料 Ed（eV/atom，CSV 直接读取）的样本中位数 ×1000。冻结 CSV 重算与论文 Table 1 完全一致（FTCP 舍入差 1）。

### B. 稳定性率（Ed ≤ 0 的占比 %）—— 出处：Table 1
| 方法 | 论文值 | 冻结数据重算值 | 容差 |
|---|---|---|---|
| Random | 1.4% | 1.4% | ±1.0 pp |
| Ion-Exchange | 9.2% | 9.2% | ±1.0 pp |
| CrystaLLM | 2.4% | 2.4% | ±1.0 pp |
| CDVAE | 1.8% | 1.8% | ±1.0 pp |
| FTCP | 2.0% | 2.0% | ±1.0 pp |
| MatterGen | 3.0% | 3.0% | ±1.0 pp |
口径：Ed ≤ 0 计数 / 500。与论文完全一致。

## 上下文锚（论文结论；冻结数据无法直接重算，需 MP/AFLOW 全集或重跑筛选——不进入抽查主路径）

### C. 新颖性率 / 新原型率 —— 出处：Table 1
- 新颖性率（不在 MP 的比例，需全集计数）：Random 98.6%、Ion-Exchange 72.4%、CrystaLLM 98.2%、CDVAE 96.0%、FTCP 38.2%、MatterGen 91.8%。
- Novel prototype rate（AFLOW 无法索引的结构占比）：CDVAE 8.2% 最高；其余生成模型 0–7.2%；两个基线 0%。
- 结论锚：生成模型独有的"新结构框架"能力（prototype novelty > 0），基线为 0%；新颖性-稳定性反向权衡。

### D. 属性定向 —— 出处：Sec "Generating materials with targeted properties" / Figure 3 & 4
- 带隙目标 3 eV（±0.5 eV 命中率，500 novel/方法）：Random 11.2%；Random+CGCNN 过滤 21.4%；Ion-Exchange 37.2%；FTCP 61.4%（最优）。
- 金属占比：Random 30.2% → CGCNN 过滤后 18.8%；Ion-Exchange 5.6%。
- 体模量 ≥300 GPa 命中率：Random 3.0%；+CGCNN 过滤 15.4%；Ion-Exchange 8.6%；FTCP 9.2%。

### E. CHGNet 稳定性筛选 —— 出处：Sec "Stability and novelty" / Figure 2 右
- 筛选后稳定性率：Ion-Exchange 15.2%、Random 7.6%、CrystaLLM 17.0%、FTCP 22.4%、MatterGen/CDVAE 3.8–8.8%；CDF 80% 阈值：IonX ~100 meV/atom vs CrystaLLM/Random >600 meV/atom。

## 锚使用说明
- 判分抽查（SCORE_RUBRIC B 部分）以 **A（中位 ΔEd）与 B（稳定性率）** 为主：裁判运行提交代码从冻结 CSV 重算并对照上表。
- C/D/E 用于判定结论方向（A2/A3 部分），数值本身不可从冻结数据重算，不按数值精确匹配扣分，只按方向与排序判定。