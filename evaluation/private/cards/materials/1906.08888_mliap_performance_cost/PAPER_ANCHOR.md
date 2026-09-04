# 论文锚：1906.08888_mliap_performance_cost

> 用途：LLM judge 判分基准（私有）。数值来自 arXiv:1906.08888（J. Phys. Chem. A 124, 731 (2020)），禁止篡改。

## 锚清单

| # | 指标 | 论文数值 | 出处 | 定义口径 | 容差 |
|---|---|---|---|---|---|
| 1 | 元素集 | Li, Mo, Cu, Ni, Si, Ge（六元素） | Abstract/Section II | 元素列表 | 精确 |
| 2 | 划分 | 90% 训练 / 10% 测试（同采样协议） | Section II | 比例 | 参照（冻结数据为准） |
| 3 | 数据规模 | 每元素 train ~200–260 结构，test ~23–31 | 冻结 JSON（仓库 data/） | 配置数 | 精确（冻结数据核验） |
| 4 | 能量精度 | 各 ML-IAP 能量 MAE 达 meV/atom 量级（GAP/MTP 最低；SNAP/NNP 最高） | Section III/Figure 3 | 能量 MAE | 量级 |
| 5 | 力精度 | 力 MAE ~0.1 eV/Å 量级；Cu/Ni/Li 最低、Mo 与金刚石半导体较高 | Section III/Figure 3 | 力 MAE | 量级 |
| 6 | 无过拟合 | 训练与测试误差相近 | Section III | 误差对比 | 方向 |
| 7 | 精度-代价 | 自由度 ↑ → 误差 ↓、代价 ↑；Pareto 前沿（Mo 系统） | Figure 2 | 权衡方向 | 方向 |
| 8 | 化学趋势 | fcc（Cu/Ni）能量 MAE 最低、bcc（Li/Mo）次之、金刚石（Si/Ge）最高 | Section III | 排序 | 方向 |

## 备注
- 主论断：ML-IAP 在六元素上达近 DFT 精度（meV/atom 与 ~0.1 eV/Å），GAP/MTP 类最优、SNAP/NNP 类较差、qSNAP 居中；无过拟合。
- 判分提示：以「能量 MAE meV/atom 量级 + 力 MAE ~0.1 eV/Å 量级 + 训练≈测试」为主判据；绝对数值受实现影响，不强求与论文逐点一致。
