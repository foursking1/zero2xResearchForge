# 论文锚：2604.13897_molcryst_mlips

> 用途：LLM judge 判分基准（私有）。数值来自 arXiv:2604.13897（2026），禁止篡改。

## 锚清单

| # | 指标 | 论文数值 | 出处 | 定义口径 | 容差 |
|---|---|---|---|---|---|
| 1 | 体系数 | 9 个分子晶体体系（Benzamide/Benzoic acid/Coumarin/Durene/Isonicotinamide/Nicotinic acid/Niacinamide/Pyrazinamide/Resorcinol） | Abstract | 体系列表 | 精确 |
| 2 | 能量 MAE | 0.141 kJ·mol⁻¹·atom⁻¹（跨体系平均） | Abstract | 能量 MAE | ±0.02 |
| 3 | 力 MAE | 0.648 kJ·mol⁻¹·Å⁻¹（跨体系平均） | Abstract | 力 MAE | ±0.1 |
| 4 | 基础模型 | MACE-MH-1（omol head）微调 | Abstract | 架构 | 参照 |
| 5 | 多晶型 ΔE | Durene 0.09 → Resorcinol 4.64 kJ/mol | Section（Table） | 单体间能量差 | 参照 |
| 6 | 多晶型分辨 | 仅微调模型分辨多晶型能量景观（3 个 SOTA 基础模型失败） | Abstract/Section | 方向 | 方向 |
| 7 | MD 稳定性 | NVE 能量守恒（漂移 ~10⁻⁷ 量级）；P2 序参数/RDF 完整 | Abstract/Section | 量级 | 量级 |
| 8 | 数据规模 | HF 仓库 10 体系 train/valid h5 + 10 权重 | HF 仓库 | 计数 | 精确（冻结数据核验） |

## 备注
- 主论断：MACE-MH-1 微调模型可高精度（0.141/0.648 kJ/mol）描述分子晶体并分辨多晶型能量景观。
- 判分提示：以「h5 数据统计 + 体系映射 + 能量/力量级」为主判据；完整模型评估为加分项（需 MACE/GPU），允许仅完成数据层验证并声明。
