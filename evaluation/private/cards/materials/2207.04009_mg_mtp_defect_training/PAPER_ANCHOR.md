# 论文锚：2207.04009_mg_mtp_defect_training

> 用途：LLM judge 判分基准（私有）。数值来自 arXiv:2207.04009（2023），禁止篡改。

## 锚清单

| # | 指标 | 论文数值 | 出处 | 定义口径 | 容差 |
|---|---|---|---|---|---|
| 1 | 数据集 | Everything 与 Everything±Shear 两套训练集 | Section II/III | 训练集构成 | 精确（冻结数据核验） |
| 2 | 构型来源 | Random-SPG 随机晶体结构（1–10 Mg/晶胞）+ 体积/单轴应变 + 声子 | Section II | 采样策略 | 参照 |
| 3 | DFT 收敛 | 能量收敛 0.6 meV/atom（均值）、6.4 meV/atom（最大）；力 7×10⁻⁵ eV/Å | Section II | 收敛误差 | 参照 |
| 4 | 平面波参数 | PAW/PBE；截断 550 eV（验证集 687.5 eV）；37×37×37 k 点（验证） | Section II | 计算参数 | 参照 |
| 5 | MTP 训练 RMSE | 最优配置能量 ~10 meV/atom 量级；随 level/cutoff 提升而降低 | Figure 4 | 能量 RMSE | 量级 |
| 6 | 经典势对照 | MTP 比 EAM/MEAM 类经典势低 1–2 个数量级 | Figure 4 | RMSE 对比 | 数量级 |
| 7 | 缺陷迁移性 | 无缺陷训练结构；空位/间隙/晶界/位错描述准确；bcc Mg 声子+弹性正确复现 | Section III/Appendix | 迁移性 | 方向 |
| 8 | 训练协议 | 全量数据拟合、报告训练误差（不用 hold-out） | Section II | 协议 | 参照 |

## 备注
- 主论断：物理驱动的系统性训练集（无缺陷结构、无主动学习）能产生可迁移的 Mg 缺陷 ML 势。
- 判分提示：以「数据统计 + 收敛参数核实 + 迁移性方向性讨论」为主判据；MTP 拟合为加分项，允许仅完成数据层验证。
