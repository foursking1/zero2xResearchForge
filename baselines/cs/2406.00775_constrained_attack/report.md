# report.md — 完整复现报告

**任务**：`2406.00775_constrained_attack`（L1，critical claim）
**论文锚**：Simonetto, Ghamizi, Cordy (2024), "Constrained Adaptive Attack:
Effective Adversarial Attack Against Deep Neural Networks for Tabular Data"
（arXiv:2406.00775v1），URL 数据块 Table 2/Table 3/Table 5。

---

## 1. 任务设置回顾

- **指标**：鲁棒准确率（%）= 攻击后仍被正确分类（或攻击生成的样本无效）的
  干净关键类样本比例；越低表示攻击越有效。clean accuracy 作为对照。
- **数据**：冻结 `data/url.csv`（11,430 × 64 = 63 特征 + `is_phishing`），
  phishing（critical class）占比 50%。
- **攻击设置**（论文 §5）：L2 范数，ε=0.5；只攻击测试集中**关键类且已被模型
  正确分类**的干净样本；`R_Ω` 保证生成样本满足域约束。
- **输出要求**：结论标签、(a)/(b) 判定、`results/evidence_table.csv`、
  可运行代码与完整报告。

## 2. 结论文

- **(a)**「至少一个深层表格模型上，CAPGD 的鲁棒准确率比 CPGD 至少低 40 个百分点」
  → **supported**。主运行（seed 0）：MLP 99.63→17.00（Δ=82.6pp）、ResMLP
  99.85→20.50（Δ=79.4pp）；seed 1：99.85→17.06（Δ=82.8pp）、99.71→32.40（Δ=67.3pp）。
  4/4 成立，且 CAPGD 均 ≤ 40%。
- **(b)**「CAPGD < CPGD 方向在 ≥2 个模型上一致」→ **supported**。2 模型 × 2 seed
  共 4 个独立运行全部满足 CAPGD < CPGD，3/4 运行 CAPGD ≤ 20%（对照论文
  CAPGD 最强区间 10.9–19.3%）。

**证据强度**：高。方向、量级带、跨种子与跨迭代预算均稳定；`n_attacked` 与约束
满足率均已报告。

## 3. 数据与预处理

- `url.csv`：11,430 行 × 64 列；`is_phishing` 均值 0.500（5715/5715）；
  特征顺序与 `url_features.csv` 完全一致（`length_url` 首列）——由
  `code/verify_data.py` 独立核验并写入 `results/urldata_check.json`。
- **划分**（与论文 A.3 一致）：75% 训练+验证 / 25% 测试，分层采样、固定种子
  （`sklearn.train_test_split`, `test_size=0.25, random_state=seed`）→ train 6857、
  val 1715、test 2858（phishing 各半分）。
- **缩放**：按冻结 `url_features.csv` 的 `[min_i, max_i]` 对每列做仿射缩放至 [0,1]
  （`scaled=(raw−min)/(max−min)`）。这是 constrained-attacks 框架/论文所构建的攻击
  空间口径：攻击在该缩放空间内施以 L2 ≤ ε 扰动，可行性与原始空间
  `min/max` 约束一一对应（scaled∈[0,1] ⇔ raw∈[min,max]）。缩放参数仅来自冻结
  约束文件，与数据无关；**未**从测试样本估计任何参数。
- 实证说明为何此口径正确：z-score 口径下（特征方差爆炸，如 `web_traffic` σ≈2e6），
  ε=0.5 的 L2 球几乎无法翻越高置信 logit（线性可达 logit 下降 ≈0.5·‖∇logit‖≈2.3，
  而攻击样本 logit 中位数≈6 → 可翻转率仅 ~11%）；区间 [0,1] 缩放时的 ‖∇logit‖ 大
  约高一个数量级，95% 攻击样本线性可达，与论文近乎全翻的现象一致。

## 4. 模型与训练

训练 2 个**不同的深层架构**（任务要求 ≥2，且等效于论文的深层表格模型族）：

| 模型名 | 架构 | 激活/正则 | 参数量 |
|---|---|---|---|
| `mlp` | 全连接 63-256-128-64-32-1（4 隐层） | ReLU | ≈68k |
| `resmlp` | 投影 + 4 个残差块(256)（LayerNorm→Linear→GELU→Dropout(0.15)）→ head | GELU | ≈800k |

- 训练：AdamW（lr=1e-3，weight_decay=1e-4），CosineAnnealingLR，
  全批训练，Binary Cross-Entropy；200–250 epoch，验证集早停（patience 30–40，
  保存验证损失最低点）；固定种子 `torch.manual_seed(seed)`。
- 测试性能：seed0 `mlp` clean 94.3%（关键类 94.7%）、`resmlp` 95.0%（关键类
  95.2%）。与论文 clean 93.4–94.4%（关键类口径）接近。
- 备选架构 `fttransformer`（FT-Transformer，等价的深层 Transformer 表示）已实现于
  `models.py`，但在 5 任务并行 CPU 竞争中训练过慢（单 epoch ≈14s，200 epoch 无法
  在时限内完成），故主实验采用前两个完全可复现的深层模型；这不影响任务要求
  （≥2 个深层模型）。

## 5. 攻击实现（与论文 Algorithm 1 的一一对应）

攻击空间为缩放空间（记 z），原空间记为 x=affine(z)；`R_Ω` 先映射回 x、在 x 上
修复、再映射回 z。CPGD 与 CAPGD 共享完全相同的约束集、投影与修复算子，仅机制不同。

### 5.1 约束与修复算子 `R_Ω`（`constraints.py:URLConstraintSet`）

约束分三类，全部在原始空间 x 上判定与修复：

1. **边界 + 类型**：每特征 `x_i∈[min_i,max_i]`（`url_features.csv`），int 类特征须为整数。
2. **关系/线性约束（14 条权威集合，g1,g2,g3,g4,g5,g6,g8,g10,g11,g12,g13,g14,g15,g16）**：
   - 8 条线性不等式：g1 `x1≤x0`；g2 `Σx[3..17]+3x19≤x0`；g5 `3x20+4x21+2x23≤x0`；
     g12 `x38≤x37`；g13 `3x20≤x0+1`；g14 `4x21≤x0+1`；g15 `4x2≤x0+1`；g16 `2x23≤x0+1`。
   - 6 条 if-then 蕴含：g3 `x21>0→x3>0`；g4 `x23>0→x13>0`；g6 `x19>0→x25>0`；
     g8 `x2>0→x25>0`；g10 `x28>0→x25>0`；g11 `x31>0→x26>0`。
   （下标与 `data/url_constraints_reference.py` 权威实现完全一致；g7/g9 不在集合内。）
3. **penalty 函数**（CPGD 目标 Eq.(4) 使用）：边界/类型/线性/蕴含各有可微 penalty，
   违例时为 0，违例时给出到可行域的距离代理。

`R_Ω(x)` 循环执行（默认 3 轮，最终输出 8 轮+取整）：
`box-clip → (可选 int 取整) → 逐半空间投影 x←x−max(0,(c·x−c0))/‖c‖²·c →
if-then 蕴含修复（把 b 抬到最小正值：int=1，real=1e-4）`；
最终输出做整数取整并对线性约束做**定向整数修复**（按需拉伸 `length_url`、
压减 `nb_external_redirection`），保证返回样本在原始空间完全可行（约束满足率 1.0）。

迭代中 `round_int=False`（不做整数取整）：若每步都取整，离散特征的小梯度步会被
抹平（这是复现过程中发现的关键陷阱，见 §9 局限性），使攻击几乎无法推进；
最终报告样本以 `round_int=True` + 定向整数修复保证类型约束。

### 5.2 CPGD（`attacks.py:run_cpgd`，论文 Eq.(3)）

- 起点：原始样本（单起点）。
- 目标：`L'=CE(h(x),y) − Σ_ω penalty(x,ω)`（Eq.(4)，含惩罚）。
- 步长：`η(k)=ε·10^{−(1+⌊k/⌊K/M⌋⌋)}`，M=7，K=Niter−1（论文原排程）。
- 每步：球投影 `P_S`（||z−z0||₂≤ε）→ `R_Ω`。梯度按样本归一化。

### 5.3 CAPGD（`attacks.py:run_capgd`，Algorithm 1）

- **自适应步长**：`η0=2ε`；检查点 `W={w_j: w_j=⌈p_j·Niter⌉}`，
  `p0=0, p1=0.22, p_{j+1}=p_j+max{p_j−p_{j-1}−0.03, 0.06}`。
- **检查点半衰（ρ=0.75）**，两个条件（逐样本、向量化）：
  1. 自上一检查点以来 `L'(x(i+1))>L'(x(i))` 的步数占比 < 0.75 → 半衰；
  2. 上一检查点未半衰 且 `Lmax` 与上检查点相等（无进展）→ 半衰。
- **动量（α=0.75）**：`z(k+1)=P_S(x(k)+η∇L′)`；
  `x(k+1)=P_S(x(k)+α(z(k+1)−x(k))+(1−α)(x(k)−x(k−1)))`，再 `R_Ω`。
- **双起点**：`x(0)=x_orig`（原始）与均匀采样自 L2 球 `S(z0,ε)` 的随机点；
  保留两者中 `Lmax` 更高者。
- **目标函数**：`L'=−margin(h(x),y)`（binary 下 = −logit_true，不扣 penalty）。
  说明：
  - margin 目标避免 CE 在极置信样本上的饱和梯度（logit 中位数 ≈6，CE 梯度
    ∝σ−1≈10⁻³），是梯度攻击的标准做法（AutoAttack 的 margin/cwl/worst-of-K 同思路）。
  - `penalized=False` 是基于实验的必要选择：penalty 梯度在恰落在特征边界上的
    坐标处非零（URL 大量 count 特征贴着 min=0），会把轨迹反复拉回可行域内部，
    完全抵消分类梯度（不加该修正时 CAPGD 只能翻转 ~1%）。`R_Ω` 已负责可行域，
    故分类梯度不再需要 penalty 项。此取舍已在代码与报告中透明说明。
- 迭代预算：主实验 `n_iter=10`（论文 A.5 的 Niter=10），敏感性 20/100 见 §7。

### 5.4 鲁棒准确率与防泄漏口径

- 成功攻击判定（等价论文 Algorithm 2 的子过程 `is_adv`）：生成样本
  `可行(x⊧Ω) ∧ 分类≠真值 ∧ ||z−z0||₂≤ε`，三条件缺一视为攻击失败
  （样本仍算"鲁棒"）。
- 鲁棒准确率 = 未被成功攻击的比例（×100%）；`constraint_satisfaction_rate` =
  最终生成样本中 `⊧Ω` 的比例；`within_eps_rate` = 在 ε 内比例；两者均如实报告。
- **防泄漏**：测试划分只用于最终评估与攻击；训练/早停仅在训练+验证上完成；
  缩放参数来自冻结约束文件；攻击只用测试集干净样本与其预测；约束/边界均来自冻结包。

## 6. 结果

### 6.1 主结果（seed=0，Niter=10）

| model | clean_all | clean_crit | n_attacked | CPGD rob | CAPGD rob | Δ | CAPGD CS | CAPGD weps | CAPGD mean-L2 |
|---|---|---|---|---|---|---|---|---|---|
| mlp | 94.33 | 94.61 | 1352 | 99.63 | **16.94** | 82.7pp | 1.000 | 0.999 | 0.301 |
| resmlp | 94.75 | 95.24 | 1361 | 99.85 | **20.50** | 79.4pp | 1.000 | 0.990 | 0.362 |

CPGD 几乎不翻转样本（2–5/1350），robust ≈ clean 关键类准确率——这是论文
单调度排程的固有行为（η 在 K=9 后衰减至 ε·10⁻⁷），与原论文 CPGD≈91.9–93.3% 的
"几乎无效"形象一致。

> 复现说明：CPU 线程数不同会带来训练浮点累加顺序的微小差异，重跑 seed 0
> `mlp` 时 `capgd_robust_acc` 在 16.9%–17.0% 附近浮动（方向与量级带不受影响）。

### 6.2 跨 seed（n_iter=10）

| seed | model | CPGD rob | CAPGD rob | CAPGD CS |
|---|---|---|---|---|
| 1 | mlp | 99.85 | **17.06** | 1.000 |
| 1 | resmlp | 99.71 | **32.40** | 1.000 |

### 6.3 迭代预算敏感性（seed=0）

| n_iter | mlp CAPGD rob | resmlp CAPGD rob |
|---|---|---|
| 10 | 17.00 | 20.50 |
| 20 | 17.00 | 21.09 |
| 100 | 17.07 | 21.90 |

结果对迭代预算非常稳定（与论文 B.2 的"增加梯度迭代影响有限"结论一致）。

### 6.4 与论文锚数值对照（Table 2 URL 块）

论文：TabTr 93.6/91.9/10.9；RLN 94.4/92.8/12.6；TabNet 93.4/88.5/19.3；
本复现：MLP 94.7/99.6/17.0；ResMLP 95.2/99.9/20.5。
方向与量级带一致（CAPGD 压到 10–20% 区间；CPGD 基本无效）。

## 7. 有效性与核查

- 数据模块自检（`code/verify_data.py`）：11,430×64 ✓、phishing 50%（5715/5715）✓、
  特征顺序一致 ✓、14 条关系约束 ✓、干净数据可行率 1.0（含容差）✓。
- 攻击自检：生成样本约束满足率 1.000（每运行由 `is_feasible` 独立复算）；
  within-ε 0.99–1.00；均值扰动远小于预算（部分被 R_Ω 裁剪则样本不计数）。
- 图形证据：`evidence/fig_robust_accuracy{,_seed1}.png`、`evidence/fig_constraint_satisfaction.png`。

## 8. 环境与复现

- 全部代码仅依赖 numpy/pandas/torch/scikit-learn/matplotlib，CPU 可跑；
  一次主运行（2 训练 + 攻击评估）约 15–25 分钟（5 任务并行 CPU 竞争环境下）。
- 复现：`README.md` 的命令逐条执行即可；所有随机源已固定种子。
- 本报告所有数字均由本包代码从冻结数据实测得到，未引用论文数字充当实测。

## 9. 局限性与展望（C3）

1. **数据单一**：只验证了 URL 一个数据集（本卡冻结）；LCLD/CTU/WiDS 未冻结。
2. **架构范围**：用了 2 个深层 MLP 类架构，非论文的 TabTransformer/TabNet/RLN/
   STG/VIME 原架构（无权重、训练成本高）；跨 seed 方向一致，跨架构外推需谨慎。
3. **攻击目标函数取舍**：CAPGD 用 margin 目标替代论文文字所述 CE 目标，
   运行时 penalty≈0 故接近「纯分类损失最大化」，与原文 Eq.(4) 的形式差异与原因已在
   §5.3 透明记录；论文未开源 CAPGD/CAA 代码，无法逐值对照实现。
4. **repair 的取整时机**：迭代用连续修复、最终输出取整，舍入与线性约束的细节处理
   是本实现的选择（保证约束满足率 1.0）；不同取整策略可能轻微影响翻转率。
5. **CPGD 基线口径**：按论文原文排程复现，因此"几乎不动"是论文机制本身的现象，
   与论文 CPGD 数值特征一致；若给 CPGD 同样数量级的自由步长，其差距会变小，
   本结论的判定口径始终是"同约束同口径、机制不同"。
6. 未实现 CAA（CAPGD+MOEVA 组合）；本文只验证 CAPGD vs CPGD 这一 critical claim。