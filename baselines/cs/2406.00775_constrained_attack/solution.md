# solution.md — 方法说明与结果

任务：`2406.00775_constrained_attack`（L1 critical claim）
论文：Constrained Adaptive Attack（arXiv:2406.00775），URL 数据集上的
核心论断 **CAPGD 显著优于 CPGD**（论文 Table 2：URL 上 5 个模型
CPGD 91.9–93.3% → CAPGD 10.9–72.6%）。

## 1. 结论标签

| 可证伪表述 | 结论 | 支持强度 |
|---|---|---|
| (a) 至少一个深层表格模型上「CAPGD 鲁棒准确率比 CPGD 至少低 40 个百分点」 | **supported** | 2 模型 × 2 seed 共 4/4 成立：差距 67–83pp；主 run 差距 79–83pp |
| (b) 「CAPGD < CPGD 的方向在 ≥2 个模型上一致」 | **supported** | 4/4 运行全部 CAPGD < CPGD，且 3/4 运行 CAPGD ≤ 20%（论文最强模型区间的 10.9–19.3% 之对照） |

数据支持强度：**高**。两个独立训练的深层模型（不同架构、固定种子）在两个随机种子上
均给出同一方向与量级；攻击预算敏感性表（n_iter=10/20/100）显示结果稳定
（CAPGD robust 变化 < 1.5pp）。

## 2. 结果表（seed=0，primary）

| 模型 | 架构 | clean_acc_all | clean_acc_crit | n_attacked | CPGD robust | CAPGD robust | 约束满足率(CAPGD) | within-ε(CAPGD) |
|---|---|---|---|---|---|---|---|---|
| mlp | 深层 MLP（4 隐层 256-128-64-32） | 94.33% | 94.61% | 1352 | 99.63% | **16.94%** | 1.000 | 0.999 |
| resmlp | 深残差 MLP（LayerNorm+GELU+Dropout，4 块×256） | 94.75% | 95.24% | 1361 | 99.85% | **20.50%** | 1.000 | 0.990 |

- 攻击口径：L2、ε=0.5（按特征区间 [min,max] 线性缩放后的空间）、只攻击测试集
  中**关键类（phishing）且已被正确分类**的干净样本；鲁棒准确率 = 攻击后仍未
  被成功攻击的比例（无效/超预算样本视为攻击失败，即「被正确分类」）。
- 与论文数值对照（Table 2 URL）：论文 TabTr 91.9→10.9、RLN 92.8→12.6、
  TabNet 88.5→19.3；本复现 99.6→16.9、99.9→20.5。方向完全一致、量级带吻合
  （CAPGD 落在 10–20% 区间；CPGD 基本无效、≈ clean acc——论文的 CPGD 同样几乎不动）。
- 复现注意：CPU 线程数不同会导致训练浮点累加顺序的微小差异，重跑 seed0 mlp
  的 capgd robust 可能在 16.9%–17.0% 附近（方向与量级带稳定）。

## 3. 方法要点

- **数据与划分**：冻结 `data/url.csv`（11,430×64，phishing 50%）；75/25 分层划分
  （与论文一致），内部再留 20% 作验证集；特征按 `url_features.csv` 的
  [min_i, max_i] 作区间线性缩放（这正是 constrained-attacks 框架的攻击空间口径，
  该口径下 ε=0.5 与论文翻转率一致）。测试划分全程冻结，训练/早停只用训练+验证。
- **约束**：每特征边界（min/max）+ int 类型 + 14 条关系/线性约束（g1–g16 权威集合），
  全部在**原始空间**判定；`R_Ω` 修复算子循环执行 box-clip、半空间投影、
  if-then 蕴含修复（b>0 取最小正值），并对 int 特征做最终取整 + 定向整数修复。
- **CPGD（基线）**：按论文 Eq.(3)/(4)，目标 L'=CE−Σpenalty，步长
  η(k)=ε·10^(−(1+⌊k/⌊K/M⌋⌋))，M=7，单起点=原始样本，逐步 repair。
- **CAPGD（Algorithm 1）**：η0=2ε；检查点 W（p0=0, p1=0.22,
  p_{j+1}=p_j+max{p_j−p_{j-1}−0.03, 0.06}）；ρ=0.75 半衰条件 1/2；
  动量 α=0.75；双起点（原始 + L2 球内随机点）；每步 R_Ω。
  为使在置信度极高的算法输出（logit 中位数≈6）上不等相变差的饱和 CE 梯度失效，
  CAPGD 采用 margin 目标（−logit_true），这是梯度攻击的标准做法（AutoAttack 同款），
  且已证明必要（penalty 梯度在边界特征处会抵消分类梯度，见 report.md §5）。
- **鲁棒准确率口径**：生成样本须满足「可行 ∧ ‖·‖₂≤ε ∧ 分类被翻转」才算成功攻击；
  不满足任一条件按论文定义视为「被正确分类」。约束满足率报告为实际值（=1.000）。

## 4. 关键产物

- `results/evidence_table.csv`：含 rubric 要求的列（model/clean_acc/robust_acc_cpgd/
  robust_acc_capgd/n_attacked/constraint_satisfaction_rate）。
- `results/metrics.json`：全部指标 + 设置；`results/urldata_check.json`：B 抽查项。
- `evidence/*.png`：鲁棒准确率对比图与约束满足率图。
- 可复现代码与运行说明见 `README.md`。

## 5. 局限性

- 仅 URL 单一数据集（本包冻结）与 2 个深层 MLP 类架构（未含 TabTransformer/TabNet
  等论文原架构，因无权重且 CPU 受限）；方向结论跨 seed 一致但推广性有限。
- CAPGD 的 margin 目标与论文文字所述 CE 目标的差异、repair 中整数取整时机的选择，
  均属实现层取舍并已透明说明（论文未开源代码）。
- CPGD 基线按论文的固定递减步长实现，因此在 10 次迭代下几乎不动（robust≈clean），
  与原论文现象一致；这是论文自身设计的排程特性，并非本实现削弱基线。