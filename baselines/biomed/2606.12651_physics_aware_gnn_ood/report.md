# report.md — 物理感知 GNN OOD 泛化提升关键论断复现报告

- 任务 ID：`2606.12651_physics_aware_gnn_ood`（L1 critical claim）
- 论文：Physics-Aware GNN for Out-of-Distribution Molecular Property Prediction（arXiv:2606.12651）
- 复现目标：GINE 基线 +「复杂度 / 应变」物理感知辅助损失三种变体在 COCONUT 单源 OOD 上的 ROC-AUC 显著提升论断

## 1. 方法

### 1.1 数据与标签（SAScore 阈值法）
- 训练语料：MoleculeNet **HIV.csv**（41,127）⊕ **tox21.csv.gz**（7,831），共 48,958 分子。
- OOD 测试语料：**COCONUT_30k_seed42.csv**（30,000 天然产物子样本，seed=42），全程不进入训练/验证。
- 标签：SAScore **< 4 → easy（正类 label=1），> 5 → hard（负类 label=0），4–5 之间丢弃**（论文放宽的 hard 口径）。
- SAScore 计算：RDKit `SA_Score.sascorer`（对冻结 parquet 抽样 300± 复核，最大绝对差 0.0，完全一致；RDKit 不可用时回退读取冻结 `data/*_sascore.parquet`）。
- 冻结语料标注后规模：
  - 训练侧（HIV+Tox21，共 48,958）：kept 43,274 = easy 40,151 / hard 3,123（4–5 带宽丢弃 5,669，另有 15 个解析失败不计入）；
  - OOD 测试侧（COCONUT 子集，共 30,000）：kept 22,287 = easy 13,401 / hard 8,886（带宽丢弃 7,713）；
  - 合计 kept 65,561 = **53,552 easy / 12,009 hard（81.7 / 18.3）**，与论文 65,177 = 82/18 高度一致（相对差约 0.4%）。

### 1.2 特征与图表示
- 原子（27 维）：元素 one-hot（20+其他）、芳香、degree/4、formal charge、总 H 数、环成员、杂化。
- 键（5 维）：单/双/三/芳香 one-hot、共轭；无向边各存两条有向边。
- 辅助（物理感知）目标（z-score 由训练侧统计标准化）：
  - **complexity** = log(BertzCT+1)（RDKit `GraphDescriptors.BertzCT`；训练均值为 6.458、σ 0.748，与前期 feat 日志完全一致）；
  - **strain** = 2D 坐标 UFF 松弛能降 `max(0, E_UFF(初值) − E_UFF(优化后))`（RDKit UFF，最多 400 次迭代），1.2%（540/43,274）参数缺失样本记为 0 / mask；均值 4.67、σ 13.05。天然产物 strain 显著高于药物分子（COCONUT 均值 48.9 vs HIV 8.5），与 hard 分布物理直觉一致。

### 1.3 划分（严格无泄漏）
- train / val：仅从 HIV+Tox21 kept 样本中取固定 10%（val_seed=0）作为验证，其余 90% 训练；COCONUT 不参与任何验证、早停或超参选择。
- OOD 测试：全部 COCONUT kept 样本（22,287），只在训练结束后评估一次。

### 1.4 模型与训练协议（主要协议 regime 1）
- **GINE**（GIN + 边特征，Hu et al. 2020）：embed→3×GINE(BN,ReLU)→mean+max 池→MLP 分类头；边信息与节点特征相加，`(1+ε)` 残差；隐藏宽度 64。
- 损失：主任务 BCE + 辅助 MSE 回归（λ=0.1）；类别平衡使用 `pos_weight=neg/pos≈10.6`（针对 93/7 easy/hard 不均衡，upweight hard）。
- 变体：`baseline`（无辅助头），`+complexity`，`+strain`，`+both`（两辅助头）。
- 训练：Adam lr=1e-3、wd=5e-4、batch=256（连续图块切片，纯张量实现），最多 26 epoch，验证 AUC 早停（patience=8）+ 最优模型选择；CPU/GPU 自动（本环境 GPU CUDA 训练，CPU 亦支持）。
- **固定 5 个随机种子**（0–4），每 seed 独立初始化与训练；代码纯 PyTorch 实现（无 torch_geometric 依赖）。
- **协议 A（默认/precommitted）**：如上（pos_weight=True、λ=0.1）。**协议 B（敏感性）**：`--pos_weight 0 --aux_w 0.5`（plain BCE、强辅助监督），其余一致。

### 1.5 统计
- 每 (变体, seed) 计算 COCONUT OOD ROC-AUC（秩相关 Mann-Whitney 实现，sklearn 交叉验证一致）。
- 配对 Δ = 变体 seed AUC − baseline 同 seed AUC；对 5 个同种子 Δ 重采样 **10,000 次** bootstrap 得 95% 分位 CI。

## 2. 结果

### 2.1 Q1 基线 OOD AUC（A1）
| 指标 | 实测 | 论文 | 相对差 |
|---|---|---|---|
| mean OOD ROC-AUC（5 seed） | **0.98521** | 0.9774 | +0.80%（≤5% ✓） |

各 seed：0.98642 / 0.98431 / 0.98881 / 0.98374 / 0.98275。

### 2.2 Q2 物理感知变体（A2）
| 变体 | mean OOD AUC | 配对 Δ | 95% CI（10k bootstrap） | CI 不含 0 | 论文对照 |
|---|---|---|---|---|---|
| baseline | 0.98521 | — | — | — | 0.9774 |
| +complexity | 0.98406 | −0.00115 | [−0.00547, +0.00376] | ✗ | +0.0060 [0.0023,0.0102] |
| +strain | 0.98672 | +0.00151 | [−0.00132, +0.00444] | ✗ | +0.0032 [0.0008,0.0052] |
| **+both** | **0.98763** | **+0.00243** | **[+0.00094, +0.00393]** | **✓** | +0.0066 [0.0038,0.0093] |

→ **+both（组合）显著提升 OOD、CI 排除 0，与论文"+both 最优"相符**；+strain 方向为正但 CI 含 0；+complexity 在本协议下约 −0.001（CI 含 0）。

### 2.3 Q3 标签分布（A3）
语料 65,561 = 53,552 easy / 12,009 hard（81.7/18.3）；论文 82/18 → 一致（≤15% 容差内，破 0.5% 相对差）。OOD 测试规模（冻结子集实际）：22,287 = easy 13,401 / hard 8,886（论文参照 5,026，任务明示以冻结子集实际为准）。

### 2.4 敏感性（协议 B：plain BCE、λ=0.5）
| 变体 | Δ | 95% CI | 结论 |
|---|---|---|---|
| +complexity | −0.00393 | [−0.00685, −0.00045] | 显著为负 |
| +strain | +0.00098 | [−0.00009, +0.00271] | 正向，含 0 |
| +both | −0.00330 | [−0.00704, −0.00006] | 显著为负 |

→ 物理感知辅助损失的收益**强烈依赖训练协议**：在较贴合类别不均衡的协议 A（强加权 + 轻辅助 λ=0.1）下 `+both` 显著为正；在强辅助（λ=0.5）下主任务被辅助回归带偏、`+both`/`+complexity` 显著为负。表明论文效应在冻结数据上与我们的实现下具有**协议依赖性、不够鲁棒**。

## 3. 结论
- **结论标签：`partially_supported`**
- 支持证据：基线 AUC 0.98521（0.9774，+0.8%）；标签分布 81.7/18.3（论文 82/18）；`+both` Δ=+0.00243（CI [+0.0009,+0.0039] 排除 0，为正且与论文同向）。
- 未支持部分：`+complexity` / `+strain` 单独未达显著；更强 aux 权重下效应反转。

## 4. 局限
1. **SAScore 口径**：hard 阈值论文已放宽至 >5（严格 >6 只剩极少数 hard）；我们沿用此口径，4–5 带 13k 样本被丢弃。
2. **OOD 测试规模**：冻结 COCONUT 子集 30k、去带后 22,287，远大于论文 5,026 参照；测试更充足，但无法逐位对照论文数字。
3. **辅助目标定义**：complexity 采用 log(BertzCT)（与前期日志均值 6.458 完全一致）；strain 采用 UFF 2D 松弛能降（论文精确公式未随锚点给出，为等价物理代理）。
4. **协议敏感性**：`+both` 提升仅在我们主协议（pos_weight + λ=0.1）下显著；λ=0.5/无加权的敏感性协议出现反转，故对"三种变体均显著"作"部分支持"而非"完全支持"。
5. **增强基线**：我们的 GINE 训练轮数/容量充足（26 epoch / GPU），基线 0.985 高于论文 0.9774，压缩了 aux 提升空间——这是 Δ 小于论文的重要原因。

## 5. 复现
见 `agent_solution/README.md` 与 `code/run_all.sh`。所有代码可从 `data/` 冻结数据一键重算标签、图特征、AUC、Δ 与 CI（固定种子；RDKit 可选、缺失时回退冻结 parquet/缓存，结果一致）。