# PAPER_ANCHOR（私有，仅裁判/编译者可见）：2311.04765_voraus_ad

> 用途：LLM judge 判分基准。本卡为 L1（critical claim）。数值全部摘自 arXiv:2311.04765v1（§III 数据、§V 实验、Table VI、Fig 10/13），禁止臆造。

## 目标论文与协议

- Brockmann, Rudolph, Rosenhahn, Wandt (2023), "The voraus-AD Dataset for Anomaly Detection in Robot Applications"（arXiv:2311.04765v1，IEEE Transactions on Robotics）。
- 数据（§III-C，Table IV）：2,122 条 pick-and-place 样本 = 948 训练正常（PRE_A，setting=72）+ 419 测试正常 + 755 异常（12 类）；130 机器信号（78 机械 + 52 电气，6 轴 + 4 通用电气），原始 500 Hz，评估用 100 Hz；样本平均时长 ~11s。
- 协议（§V-A）：逐异常类别 AUROC（该类异常样本为正、正常测试样本为负），12 类平均作为总体比较；论文明确不推荐全体样本单条 ROC（样本数不平衡偏置）。

## 锚 A1 — 平均 AUROC（Table VI，§V-C）

| 方法 | 平均 AUROC (%) | 说明 |
|---|---|---|
| MVT-Flow（正常流，论文方法） | **93.6 ± 5.7** | 9 次运行均值±标准差 |
| HMM | 87.4 ± 5.8 | 最佳基线 |
| LSTM-VAE | 86.7 ± 10.1 | |
| CAE | 85.2 ± 9.2 | |
| GANF | 79.9 ± 12.7 | |
| PCA | 80.0 | 参数调优 |
| 1-NN | 77.5 | ℓ1 距离 |

- 出处：Table VI "Anomaly detection results on voraus-AD for MVT-Flow and other baselines measured in AUROC percentage"；§V-C "MVT-Flow outperforms all other baselines for 8 out of 12 categories and on average by a large margin of 6.2%"；摘要同款 6.2% 表述。
- 判分口径：agent 主方法（深度密度/重构类）12 类平均 AUROC 与 93.6 锚比较。

## 锚 A2 — 相对优势幅度（§V-C，由 Table VI 均值导出）

- MVT-Flow − HMM = +6.2pp；− PCA = +13.6pp；− 1-NN = +16.1pp。
- 判分口径：agent 的深度方法 vs 自己实现的 PCA/1-NN 基线，差值方向与量级。

## 锚 A3 — 逐类别 AUROC（Table VI，MVT-Flow 列）

| category_id | 名称（论文表 VI 名） | 论文 AUROC (%) |
|---|---|---|
| 0 | axis_friction（Add. Friction） | 96.6 ± 0.6 |
| 10 | motor_commutation（Miscommutation） | 99.8 ± 0.3 |
| 5 | miss_can（Misgrip can） | 95.3 ± 3.3 |
| 6 | lose_can（Losing can） | 96.2 ± 0.4 |
| 1 | axis_weight（Add. axis weight） | 94.1 ± 0.7 |
| 2 | collision_foam（Coll. foam） | 87.5 ± 1.2 |
| 3 | collision_cable（Coll. cables） | 84.7 ± 1.2 |
| 4 | collision_carton（Coll. cardboard） | 88.3 ± 1.2 |
| 7 | can_weight（Var. can weight） | 85.1 ± 1.1 |
| 8 | entangled（Cable at robot） | 100.0 ± 0.0 |
| 9 | invalid_position（Invalid grip. pos.） | 100.0 ± 0.0 |
| 11 | wobbling_station（Unstable platform） | 96.1 ± 0.7 |

## 锚 A4 — 类别特异性（Table VI + §V-C）

- miss_can（5）：1-NN/PCA/CAE/LSTM-VAE 均 100.0，HMM 71.0，MVT-Flow 95.3；§V-C "the comparatively simple approaches 1-NN and PCA can perfectly detect a misgrip of the can, but underperform on average"。
- entangled（8）/invalid_position（9）：仅 MVT-Flow 达 100.0（如 entangled 1-NN 63.0、PCA 71.6、LSTM-VAE 96.0）。
- 用途：辅助判断 claim (c) 与类别模式一致性。

## 判分对照速查（judge 用）

- A1 满分带：agent 主方法平均 AUROC 与 93.6 绝对差 ≤ 5pp；半档 ≤ 10pp；低档 ≤ 15pp；> 15pp 不达标（详见 SCORE_RUBRIC.md）。
- A2：深度方法 − PCA/1-NN 均 > 0 且主差 ≥ 3pp → 满分方向；0-3pp → 半档；≤ 0 → 需解释或判 contradicted。
- A3：≥ 6/12 类别方向一致（容易类 entangled/invalid_position/motor_commutation/axis_friction；难类 can_weight/collision_cable/collision_foam/collision_carton）。
- B 抽查字段：sample 数（2,122）、setting==72 样本数（948）、miss_can（category==5）的 n_anomaly=72 与 AUROC、平均 AUROC 重算。
