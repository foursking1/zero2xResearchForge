# 论文锚：2401.15089_pst_matbench

> 用途：LLM judge 判分基准（私有）。数值来自 arXiv:2401.15089（Sci. Rep. 14, 10132 (2024)），禁止篡改。

## 锚清单

| # | 指标 | 论文数值（5 折 CV MAE） | 出处 | 定义口径 | 容差 |
|---|---|---|---|---|---|
| 1 | Formation Energy | 0.032 ± 0.0003 eV/atom（PST）；CrabNet 0.086；coGN 0.021 | Table 1 | 5 折 CV MAE | ±0.01 |
| 2 | Band Gap | 0.210 ± 0.002 eV（PST）；CrabNet 0.266；coGN 0.156 | Table 1 | 5 折 CV MAE | ±0.03 |
| 3 | Shear Modulus | 0.074 ± 0.001 log10(GPa)；coGN 0.069 | Table 1 | 5 折 CV MAE | ±0.01 |
| 4 | Bulk Modulus | 0.056 ± 0.003 log10(GPa)；coGN 0.053 | Table 1 | 5 折 CV MAE | ±0.01 |
| 5 | Refractive Index | 0.290 ± 0.078；coGN 0.309 | Table 1 | 5 折 CV MAE | ±0.05 |
| 6 | Phonon Peak | 29.40 ± 1.40 1/cm；coGN 29.71 | Table 1 | 5 折 CV MAE | ±3 |
| 7 | Exfoliation Energy | 31.15 ± 9.57 meV/atom；coGN 37.16 | Table 1 | 5 折 CV MAE | ±4 |
| 8 | Perovskites FE | 0.030 ± 0.001 eV/cell；CrabNet 0.406 | Table 1 | 5 折 CV MAE | ±0.005 |
| 9 | PDD 必要性（Band Gap） | PST 0.212 vs Composition-only 0.273 vs PDD-only 0.596 | Table 3 | MAE（eV） | 方向 |
| 10 | PDD 权重 | No weights 0.278 → PST 0.212（Band Gap） | Table 4 | MAE（eV） | 方向 |
| 11 | 训练成本 | PST 250 epochs；预测比 coGN 快约 5 倍 | Table 2/Section 3 | 相对 | 参照 |

## 备注
- 主论断：PDD 等距不变量 + Transformer（PST）在 MatBench 上达到与 GNN 相当的精度（部分属性更优），且训练/推理更快。
- 判分提示：以「≥3 属性 MAE 量级 + PDD 消融方向」为主判据；完整 PST 复现成本高，允许简化模型（特征=Ridge/GBDT 或轻量注意力）并在 report 声明。
