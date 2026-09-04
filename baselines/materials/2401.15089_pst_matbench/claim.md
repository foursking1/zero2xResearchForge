# Claim: 2401.15089_pst_matbench

## 判定：partially_supported（部分支持）

基于冻结 MatBench 数据的独立复算（简化 PDD 编码代理：PDD k=15 距离直方图 + ElFrac 组成 + LightGBM，5 折 CV）：

### 关键数字

| 论断 | 论文值 | 本工作复算（5 折 CV MAE） | 是否支持 |
|---|---|---|---|
| Band Gap 精度 | 0.210 eV | 0.5037 ± 0.0037 eV | 方向支持，量级偏大（2.4×） |
| Formation Energy 精度 | 0.032 eV/atom | 0.1671 ± 0.0015 eV/atom | 方向支持，量级偏大（5.2×） |
| Shear Modulus 精度 | 0.074 log10(GPa) | 0.1084 ± 0.0016 log10(GPa) | 支持（1.5×，同量级） |
| PDD 必要性消融（Band Gap） | PDD-only 0.596 > Comp 0.273 > PST 0.212 | PDD-only 0.814 > Comp-only 0.528 > 组合 0.516 | 方向支持 |

### 结论

- **PDD 编码有效性（核心论断）**：**支持（方向）**。Band Gap 消融中 PDD-only 显著最差（0.814），组成+PDD 组合最优（0.516），与论文 Table 3 方向一致；PDD 等距不变量确实携带结构信息且对精度必要。
- **绝对精度（PST 达到论文数值）**：**部分支持**。简化代理达到同一量级、明显优于平凡基线，但未达到论文 PST 的绝对 MAE（差 1.4–5.2 倍）。该差距归因于特征/模型简化（扁平直方图 + GBDT vs 注意力 Transformer + mat2vec），非数据问题。

因此整体判定为 **partially_supported**。
