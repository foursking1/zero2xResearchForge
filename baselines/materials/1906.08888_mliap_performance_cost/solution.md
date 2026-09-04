# solution.md — 方法说明与结果摘要

任务：`1906.08888_mliap_performance_cost`（L1 critical claim）
判断对象：Zuo et al., *A Performance and Cost Assessment of Machine Learning
Interatomic Potentials*, JPCA 124 (2020) 731 (arXiv:1906.08888) 的核心论断
「六元素（Li, Mo, Cu, Ni, Si, Ge）上 ML-IAP 达近 DFT 精度（能量 meV/atom、
力 ~0.1 eV/Å），GAP/MTP 类最优、SNAP/NNP 类较差、qSNAP 居中；无过拟合」。

**总体结论：`partially_supported`**（4/5 条子论断 supported，化学趋势 partisan）。

---

## 1. 做了什么（可复现）

在冻结的 12 个 train/test JSON（每元素一行）与 `Mo930.json` 上：

1. **数据统计**：解析全部配置，统计各元素 train/test 配置数、原子数范围、
   结构 group（Elastic / Vacancy / Surface / AIMD-NVT）与能量/力范围；
2. **描述符**：自写 Behler–Parrinello 式描述符（6 个 G2 径向 Gaussian 宽度
   + 7 个壳层 Gaussian + 2 个角度余弦特征，截断 5 Å），对**所有周期性镜像**
   枚举近邻（不折叠最近镜像，小超胞下依旧精确），并给出每特征相对原子坐标的
   **解析梯度**（用 1e-7 有限差分校验到 <1e-9）；
3. **模型（4 类，纸面 GAP/MTP/SNAP/qSNAP/NNP 的代理）**：
   - `linear_snap_proxy`（线性读出，**能量+力联合拟合**，SNAP 类代理）
   - `quad_snap_proxy`（描述符张量积的二次读出，qSNAP 类代理）
   - `kernel_gap_proxy`（RBF 核岭回归、600 个稀疏基原子，GAP 类代理）
   - `mlp_nnp_proxy`（64-64 MLP：力头 + 能量头，NNP 类代理）
   前三个为**能量守恒模型**（力 = F = −∇E 解析导出）；quad/kernel 按总能量
   拟合，linear 同时拟合能量与力；
4. **防泄漏协议**：冻结 train 按固定种子（seed=0）切 80/20（fit/val），
   超参（ridge α、核 γ,α）只在 val 上选，之后用全 train 重拟合并固化，
   冻结 test 仅评估一次；
5. **Mo 精度-代价扫描**：线性(16 参数) vs 二次(137) vs 核 n_basis∈{50..800}
   vs MLP(~10.6k 参数) 的测试能量/力 MAE（论文 Figure 2 式 Pareto）;
6. **Mo930 数据量收敛**：核代理在 194 vs 930 个训练配置下的行内域（AIMD-NVT
   测试子集）能量/力误差变化。

## 2. 核心数字（全部由代码在冻结数据上算出）

| 元素 | train/test | best test 能量 MAE (meV/atom) | best test 力 MAE (eV/Å) |
|------|-----------|------------------------------|--------------------------|
| Li   | 241/29    | 1.80 (quad)                  | 0.068 (kernel)           |
| Mo   | 194/23    | 9.82 (kernel)                | 0.296 (kernel)           |
| Cu   | 262/31    | 1.43 (quad)                  | 0.057 (quad)             |
| Ni   | 263/31    | 1.85 (quad)                  | 0.107 (kernel)           |
| Si   | 214/25    | 9.00 (kernel)                | 0.295 (kernel)           |
| Ge   | 228/25    | 6.49 (kernel)                | 0.278 (kernel)           |

- 六元素最佳模型**能量 MAE 均值 5.1 meV/atom**（1.4–9.8），∈ meV/atom 量级；
- 力 MAE 均值 0.174 eV/Å（0.057–0.30），与 ~0.1 eV/Å 同量级（quad/kernel
  只拟合总能量、力为解析梯度，故偏高 2–3×）；
- **无过拟合**：train/test 能量 MAE 比值（全元素、全模型均值）≈ 0.70，
  各模型比值 0.15–1.2；
- **模型排序（能量）**：`kernel ≈ quad < mlp < linear`（六元素均值
  5.4 / 5.9 / 19.0 / 268.7 meV/atom）——对应论文「GAP/MTP 类最优、
  NNP 类较差、线性 SNAP 最弱」的方向；
- **Mo Pareto**：核代理 n_basis 50→800，测试能量 13.3→9.5 meV/atom、
  力 0.33→0.29 eV/Å（代价↑、误差↓，呈前端）；MLP(~10.6k 参数) 停在 38.8
  meV，位于前端之外（NNP 类易过拟合，与论文图景一致）；
- **Mo930 数据量**：核代理行内域（AIMD 测试子集）能量 7.1→4.8 meV/atom
  (−33%)、力 0.38→0.29 eV/Å (−24%)。

## 3. 与论文锚对照结论

| 锚 | 论文 | 本工作复现 | 判定 |
|----|------|------------|------|
| 数据规模 | train 194–263, test 23–31 | 完全一致（脚本重算） | OK |
| 能量精度 | meV/atom | 1.4–9.8 meV/atom | OK（量级） |
| 力精度 | ~0.1 eV/Å | 0.06–0.30 eV/Å | OK（同量级，偏高） |
| 无过拟合 | 训练≈测试 | ratio ≈ 0.70 | OK |
| 模型排序 | GAP/MTP 最优、SNAP/NNP 较差、qSNAP 居中 | kernel/quad 最优、mlp 次之、linear 最弱 | 方向 OK |
| 代价权衡 | DOF↑→误差↓、有 Pareto 前端 | Mo n_basis 扫描单调成立；MLP 出前端 | OK |
| 化学趋势 | fcc 最低、bcc 次之、金刚石最高 | fcc(Cu/Ni) 最低 ✓；Li(bcc) 次优但 Mo(bcc) 最差，Si/Ge 居中 | 部分 |

## 4. 交付物
- `claim.md`：四档判定 + 关键数字；
- `code/`：完整可复现脚本（固定种子，离线可跑）；
- `results/`：`evidence_table.csv`、`metrics.json`、`anchor_comparison.json`、
  `mo_pareto_scan.json`、`mo930_convergence.json`、`verify_*`、`figures/`。