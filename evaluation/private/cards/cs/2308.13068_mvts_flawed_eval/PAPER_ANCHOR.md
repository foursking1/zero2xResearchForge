# PAPER_ANCHOR（私有，仅裁判/编译者可见）：2308.13068（目标论文隐藏）

> 用途：LLM judge 判分基准。本卡为 L2（RCBench 对齐），目标论文不向 agent 公开。所有论文数值均从 arXiv:2308.13068v2 抽出（PAGE 2/5/13-14），禁止臆造。

## 目标论文（隐藏）

- Sehili, E. & Zhang, Z. (2024/2023), "Multivariate Time Series Anomaly Detection: Fancy Algorithms and Flawed Evaluation Methodology"（arXiv:2308.13068）
- 核心论断：(1) point-adjust 协议存在根本缺陷，随机猜测可系统性超越所有已开发算法；(2) 简单 PCA 基线（+ 简单预处理/后处理）在逐点 F1 上胜过许多近期 DL 方法。

## 锚 A1 — 随机猜测 × point-adjust 的可操纵性（判 A1 维度）

| 项 | 值 |
|---|---|
| 指标名 | 随机选点（α=1000）标为异常在 point-adjust 协议下的平均 F1（F1pa） |
| 论文数值 | SWaT/Wadi ≈ **0.95**；PSM ≈ **0.98**（"using this procedure with α = 1000 yielded an average F1pa score of about 0.95 for SWaT and Wadi datasets and 0.98 for PSM. These scores are higher than the ones obtained using elaborate DL-based pipelines."） |
| 出处 | §3.1（Point-adjust: a Non-protocol...），正文第 6-7 页 |
| 判分口径 | agent 用本包数据实现随机猜测（固定 α≈1% 或 α=1000 点，≥10 次重复取均值），报 F1pa 与逐点 F1；对比论文量级 |

## 锚 A2 — PCA 简单基线 vs DL 方法（判 A2 维度，Table 1）

| 项 | 值 |
|---|---|
| 指标名 | 逐点 F1（最优阈值口径） |
| 论文数值 | **PCA**：SWaT **0.810** / Wadi 0.374 / PSM **0.538**；**AT（AnomalyTransformer）**：SWaT 0.214 / Wadi 0.108 / PSM 0.434；**NCAD**：SWaT 0.217 / Wadi 0.114 / PSM 0.429；**GDN**：SWaT 0.821 / Wadi 0.567 / PSM 0.594 |
| 出处 | Table 1（点-wise F1 列；阈值=最优逐点 F1 口径，表注明确） |
| 判分口径 | agent 实现的简单基线（如 PCA 重建误差）与深度方法在本包 SWaT/PSM 上的逐点 F1 相对大小关系 |

## 锚 A3 — 深度方法在非 point-adjust 协议下崩塌（辅助，判 A3 维度）

| 项 | 值 |
|---|---|
| 指标名 | 事件级 F1（F1E，含 FAR 惩罚） |
| 论文数值 | AT：SWaT/Wadi/PSM F1E = 0.000/0.000/0.000；NCAD：0.002/0.003/0.000；GDN：0.478/0.485/0.096；PCA：0.555/0.608/0.200 |
| 出处 | Table 1（F1E 列）+ §4.2 正文（"algorithms developed by exclusively targeting high point-adjust scores fail to distinguish themselves from a random guess when challenged with other protocols"） |
| 判分口径 | agent 若实现事件级/含 FAR 的协议，观察深度方法在该协议下的表现；不强求复现数值，重在看跨协议结论 |

## 辅助数据事实（裁判 B 维度抽查基准；从冻结数据直接核验）

| 字段 | 冻结参考值 | 备注 |
|---|---|---|
| PSM 测试段异常比例 | 27.76%（24,381 / 87,841） | 论文 Table 1 注：27.76% ✓ |
| SWaT 测试段异常比例 | 12.14%（54,626 / 449,919） | 论文 11.98%（标签重建口径差异，±0.2pp 内） |
| SWaT 通道数 / PSM 通道数 | 51 / 26 | npy/csv 形状 |
| SWaT 测试样本数 | 449,919 | npy 第一维 |
| PSM 测试样本数 | 87,841 | csv 行数 |

## 判分对照速查（judge 用）

- A1 满分：随机猜测 F1pa ≥ 0.85 且 F1pa − F1pointwise ≥ 0.4（至少一个数据集；论文 0.95/0.98 vs 逐点 ~0.01-0.02）。
- A2 满分：简单基线逐点 F1 ≥ 深度方法逐点 F1（至少一个数据集成立，两个数据集均报告）。
- A3 满分：报告跨协议 F1 差异/排序变化 + 四档标签与证据一致。
- B 抽查两数：(1) PSM 测试异常比例 27.76%；(2) 随机猜测的逐点 F1（应 ≈ 0.01-0.02 量级，从 agent 代码+冻结数据重算）。
- 若 agent 未做随机猜测或未用逐点协议 → A 对应维度按零分带。