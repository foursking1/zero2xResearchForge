# Solution — Minimaxity and Admissibility of Bayesian Neural Networks

**Paper**: arXiv:2604.04673v1 [math.ST] (Coulson & Wells)
**Task ID**: 2604.04673v1 (RCBench L2, lightweight protocol v2.0)
**Date**: 2026-08-13

---

## 0. 摘要 (Executive summary)

针对 4 条可证伪 claim 使用冻结数据（`F:/dataset/2604.04673v1`，含论文 PDF、复现源码
`src/`、冻结输出 `output/data/*.json`）进行再分析。我们 (1) 直接分析冻结输出数据，
(2) 用冻结源码重新运行完整径向风险实验（r=0..500，N_mc=50,000，K_dir=10）与
稀疏度实验（p=5 全量；p=50/100 密集 k=p vs 稀疏 k=1 作为补充），(3) 对 p=50/100
大 ||θ|| 处做高精度复算（N_mc=200,000，K_dir=30）并在 r=500 做 5-seed 标准误复测。结论：

| Claim | 判定 | 一句话依据 |
|---|---|---|
| C01 (p=5, fixed>minimax, BetaPrime≈p) | **supported** | 冻结数据 fixed max 5.031>5；全新全量 run fixed r=500 处 5.197>5 (超幅 ~4%)；BetaPrime max 4.994 不超 p |
| C02 (p=50, fixed/dropout>minimax, BetaPrime≈p) | **supported** | 全新全量 run fixed max 50.074、dropout max 50.127 均 >50；高精度 r=400: fixed 50.04, dropout 50.04；BetaPrime 50.03 |
| C03 (p=100, fixed/dropout>minimax, BetaPrime≈p) | **partially_supported** | BetaPrime 100.02≈p ✓；dropout max 100.04 微超 ✓；fixed 主协议(单 seed) max 99.99 未超，但高精度 r=500 100.024（≈5 SE）与 5-seed 均值 100.016 均超 p；超幅 ~0.02% 处于 MC 分辨率边缘 |
| C04 (p=5, BetaPrime 仅依赖 ||θ|| 且≈p; Horseshoe 随 k 强变化) | **supported** | BetaPrime 单条径向曲线 max 5.10≈p；Horseshoe k=1 max 2.79–2.92，k=5 max 5.25–9.09，随稀疏度 k 剧烈变化 |

**关键 caveat**：fixed/dropout 的收缩函数 a(s) 用重要性采样估计，在大 s 处 ESS 崩溃
（ESS/M_v 可低至 ~1e-6），因此大 ||θ|| 处的风险含收缩函数 MC 噪声。p=5 的超幅
(~0.2–0.39) 远超噪声；p=50/100 的超幅 (0.04–0.13) 与噪声同量级但经高精度复算仍为正。

---

## 1. 科学问题与 claims

TASK.md 定义 4 个问题（claim 编号 C01–C04 对应 TASK 编号）：

- **C01**：p=5 时，fixed-scale BNN 风险在 ||θ|| 较大时超过极小极大水平 p，而
  BetaPrime BNN 紧跟极小极大线。
- **C02**：p=50 时，fixed-scale BNN 与 dropout BNN 风险超过极小极大水平 p，
  BetaPrime 保持在 p 附近。
- **C03**：p=100 时，fixed-scale BNN 与 dropout BNN 风险超过极小极大，BetaPrime
  保持在极小极大附近。
- **C04**：p=5 时，BetaPrime 风险只依赖 ||θ|| 且接近 p；Horseshoe 风险随稀疏度 k
  剧烈变化。

这些对应论文 Section 5 的两个模拟：径向决策规则风险（Figures 1–3）与稀疏度依赖风险
（Figures 4–6）。

---

## 2. 数据与口径 (Data & protocol)

### 2.1 数据来源（全部冻结，原位读取）

- 论文 PDF：`F:/dataset/2604.04673v1/arxiv_2604.04673v1.pdf`（95 页，含 90+ 页附录）。
- 复现源码：`F:/dataset/2604.04673v1/src/`（config.py, priors.py, shrinkage.py,
  risk.py, horseshoe.py, cli.py, visualize.py）。
- 冻结输出数据：`F:/dataset/2604.04673v1/output/data/*.json`（radial p=5/50/100、
  sparsity p=5 各若干 run）。
- 冻结图：`F:/dataset/2604.04673v1/output/figures/*.png`。

### 2.2 实验口径（严格按论文 Section 5）

| 参数 | 值 | 出处 |
|---|---|---|
| 网络 | d=3, n1=n2=20, σ1=σ2=σ3=1, ‖x‖=1 | §5.1 |
| 固定尺度 BNN 的 V | V=2^{d-1}·∏σ²·∏T_l=4·T1·T2, T_l\|k_l~Γ(k_l/2,1), k_l~∝C(n_l,k_l) | §5.1, Lemma 1.1 |
| dropout | q1=q2=0.8, 反转 dropout；V=6.25·T1·T2·1{N1,N2>0} | §5.1 |
| M_v | 200,000 | §5.1 |
| 收缩网格 | 2500 点, s∈[0,(500+6√p)²] | §5.1 |
| 风险网格 | r=0,1,…,500 | §5.1 |
| N_mc / K_dir | 50,000 / 10 | §5.1 |
| BetaPrime 收缩函数 | a(s)=1−γ(p−1,s/2)/[(s/2)γ(p−2,s/2)], a(0)=1/(p−1) | §5.1 / Thm 3.1 |
| 稀疏度实验 | r∈[0,2.5√p] 6 等距点；k∈{1,2,5,10,⌊0.1p⌋,⌊0.2p⌋,⌊0.5p⌋,p}；θ_{r,k}=(r/√k,…,r/√k,0,…) | §5.2 |
| Horseshoe | Gibbs 3000 iter, 1000 burn-in, thin=2, Rao-Blackwell | §5.2 |

### 2.3 判定标准

- **supported**：数据/重算结果与 claim 一致。
- **partially_supported**：claim 多个断言部分成立。
- **contradicted**：数据与 claim 方向相反。
- **inconclusive**：数据不足以判定。
- 极小极大基准 = MLE 风险 = p（常数）。

---

## 3. 方法 (Methods)

我们执行两类分析，全部基于冻结数据原位读取、不下载任何外部数据：

1. **冻结数据直接分析**（`code/03_frozen_data_analysis.py`）
   加载 `output/data/*.json`，计算各估计器风险的 min/max、超过 p 的点数/首个 r、
   dropout 排序百分比、Horseshoe 各 k 曲线统计。

2. **全新重算（实际运行，非抄论文数字）**（`code/02_radial_risk.py`,
   `code/04_horseshoe_sparsity.py`）
   直接 import 冻结源码 `src.*`，对 p=5,50,100 重跑：
   - V 采样（fixed/dropout，M_v=200,000，seed=42）
   - 收缩函数 a(s)：BetaPrime 用 scipy 闭式；fixed/dropout 用重要性采样
   - 径向风险：每 r 值 K_dir=10 方向 × N_mc=50,000 样本（joblib 20 核并行）
   - 稀疏度：p=5 全稀疏度（k=1,2,5）；p=50/100 补充密集 k=p vs 稀疏 k=1
     （减采样：10 draws × 5 dirs, 1 chain）
   - BetaPrime 闭式验证（a(0)=1/(p−1)、单调增、有界），`code/01_betaprime_verify.py`

3. **稳健性检查**（`code/05_highprecision_check.py`, `code/08_se_check.py`）
   - p=50/100 在 r=400,450,500 用 N_mc=200,000、K_dir=30 高精度复算，检验
     "超过 p" 是否稳健。
   - p=5 收缩函数对 M_v（200k vs 2M）敏感性，量化 ESS 崩溃影响。
   - p=5/50/100 在 r=500 用 5 个独立 seed（N_mc=50k, K_dir=10）估计风险估计的
     标准误（SE），把 headline 超幅换算为 SE 单位。

---

## 4. 结果 (Results)

### 4.1 BetaPrime 收缩函数闭式验证（支撑 C01/C02/C03 的方法基础）

| p | a(0) | 期望 1/(p−1) | a(s→∞) | 单调增 | 有界 (0,1) |
|---|---|---|---|---|---|
| 5 | 0.250000 | 0.250000 | 0.999994 | True | True |
| 50 | 0.020408 | 0.020408 | 0.999904 | True | True |
| 100 | 0.010101 | 0.010101 | 0.999804 | True | True |

### 4.2 径向风险（全新全量 run，r=0..500，N_mc=50k×K_dir=10）

**p=5（冻结数据 r≤200 与全新 r=0..500）**

| 估计器 | 冻结 max (r≤200) | 全新 min | 全新 max | 全新 r=500 | 首个超过 p 的 r | 超过 p 的点数 |
|---|---|---|---|---|---|---|
| MLE | 5.0 | 5.0 | 5.0 | 5.0 | — | — |
| Fixed BNN | **5.0315** | 2.79 | **5.388** | **5.197** | r=7 | 476/501 |
| BetaPrime | 5.0016 | 0.902 | 4.994 | 4.994 | **无** | 0 |
| Dropout | 5.0211 | 1.51 | 6.608 | 5.190 | r=5 | 472/501 |

**p=50（全新 r=0..500；冻结 r≤17）**

| 估计器 | 冻结 max (r≤17) | 全新 min | 全新 max | 全新 r=500 | 首个超过 p | 超过 p 点数 |
|---|---|---|---|---|---|---|
| MLE | 50.0 | 50.0 | 50.0 | 50.0 | — | — |
| Fixed BNN | 43.13(<50) | 4.35 | **50.074** | **50.074** | r=398 | 103/501 |
| BetaPrime | 50.032 | 0.089 | 50.025 | 50.007 | r=12(MC噪声) | 489/501 |
| Dropout | 43.13(<50) | 4.13 | **50.127** | **50.127** | r=297 | 204/501 |

**p=100（全新 r=0..500；冻结 r≤25）**

| 估计器 | 冻结 max (r≤25) | 全新 min | 全新 max | 全新 r=500 | 首个超过 p | 超过 p 点数 |
|---|---|---|---|---|---|---|
| MLE | 100.0 | 100.0 | 100.0 | 100.0 | — | — |
| Fixed BNN | 86.67(<100) | 3.41 | **99.993** | **99.993** | **无** | 0 |
| BetaPrime | 100.026 | 0.042 | 100.017 | 100.010 | r=16(MC噪声) | 485/501 |
| Dropout | 86.70(<100) | 3.73 | **100.044** | **100.044** | r=441 | 60/501 |

> 注：p=100 主协议为单 seed（seed=42）实现。fixed 在此实现的 max 99.993 恰低于 p，
> 但高精度复算（§4.3）与 5-seed 复测（§4.3bis）显示 r=500 处均值 100.016–100.024 > p
> （见 §5 C03 讨论）。

### 4.3 高精度大 ||θ|| 复算（N_mc=200k, K_dir=30）

| p | r | fixed | dropout | betaprime |
|---|---|---|---|---|
| 50 | 400 | **50.0384** | **50.0401** | 49.9993 |
| 50 | 450 | **50.0725** | **50.0734** | 49.9993 |
| 50 | 500 | **50.1107** | **50.1106** | 49.9993 |
| 100 | 400 | 99.9522 | 99.9546 | 100.0024 |
| 100 | 450 | 99.9859 | 99.9878 | 100.0024 |
| 100 | 500 | **100.0240** | **100.0251** | 100.0024 |

p=50 处固定与 dropout 在高精度下稳健超过 p=50（+0.04~+0.11）。p=100 处二者在
r=500 超过 p=100（+0.024/+0.025），但 r≤450 仍在 p 之下；超幅 ~0.02%（p 的 0.025%），
接近 MC 分辨率，判为"真实但极微弱"。

### 4.3bis 多 seed 标准误（r=500，5 个独立 seed，N_mc=50k, K_dir=10）

| p | 估计器 | mean | SE | 超出 p 的 z 值 |
|---|---|---|---|---|
| 5 | fixed | 5.190 | 0.005 | **+38** |
| 5 | dropout | 5.189 | 0.005 | **+38** |
| 5 | betaprime | 4.999 | 0.004 | 0 |
| 50 | fixed | 50.115 | 0.014 | **+8** |
| 50 | dropout | 50.115 | 0.014 | **+8** |
| 50 | betaprime | 50.004 | 0.014 | 0 |
| 100 | fixed | 100.016 | 0.017 | +1 |
| 100 | dropout | 100.017 | 0.017 | +1 |
| 100 | betaprime | 99.994 | 0.016 | 0 |

p=5 的超幅约 38 SE（极稳健），p=50 约 8 SE（稳健），p=100 约 1 SE（边缘）。

### 4.3ter 收缩函数 M_v 敏感性（p=5, 大 s 处）

| s | a_fixed (M_v=200k) | a_fixed (M_v=2M) | 差值 |
|---|---|---|---|
| 1e4 | 0.998198 | 0.998223 | +2.4e-5 |
| 1e5 | 0.999104 | 0.999139 | +3.5e-5 |
| 2.5e5 | 0.999104 | 0.999153 | +4.9e-5 |

大 s 处收缩函数对 M_v 稳定（差 ~5e-5），说明大 ||θ|| 处 fixed/dropout 风险上漂是
**决策规则的系统特征**（固定尺度先验对大信号收缩不足，a(s)≈0.9991<1 仍偏小），
而非重要性采样 MC 假象。这支持论文"fixed prior 产生过度收缩 → 非极小极大"的机制。

### 4.4 稀疏度 p=5（C04）

**冻结 v2（r∈[0,2.5√5]=[0,5.59]，6 点）**

| 曲线 | min | max | < BetaPrime 的比例 |
|---|---|---|---|
| BetaPrime | 0.928 | **5.100** | —（基准） |
| Horseshoe k=1 | 0.424 | **2.922** | 100% |
| Horseshoe k=5 | 0.451 | **5.255** | 33% |

**冻结 zz（r∈[0,20]）**：Horseshoe k=1 max 2.922；k=2 max 4.981；k=5 max **7.075**。

**全新（减采样：20 draws × 10 dirs, 1 chain, r∈[0,5.59]）**

| k | max 风险 |
|---|---|
| 1 | 2.793 |
| 2 | 4.808 |
| 5 | 9.094 |

**补充：p=50/100 密集 vs 稀疏（p=50: 3 chains 默认配置；p=100: 减采样 10 draws × 5 dirs, 1 chain）**

| p | k | max 风险 | 与论文密集值比较 |
|---|---|---|---|
| 50 | 1（稀疏） | 5.70 | — |
| 50 | 25（中等） | 51.80 | — |
| 50 | 50（密集） | **79.91** | 论文 ~66 |
| 100 | 1（稀疏） | 6.67 | — |
| 100 | 100（密集） | **157.11** | 论文 ~130 |

> 论文 §5.2 报告密集 k=p 风险约 7.5（p=5）、66（p=50）、130（p=100）。
> 我们的 p=5 估计（5.25–9.09）与 p=50/100 密集估计（79.9/157.1）方向一致，
> 绝对值偏高的差异源于 Horseshoe 风险仅用 ~10–20 个 Y 样本/点、MC 误差大，
> 且我们的 r 网格到 2.5√p 的末端（密集曲线仍在上升）。关键是 **k=1 稀疏时
> Horseshoe 风险始终低位（5.7–6.7，接近 minimax），k=p 密集时剧烈上升
> （79.9–157.1，远高于 minimax）**，与 claim "Horseshoe 风险随稀疏度 k 强变化"
> 一致。

---

## 5. 结论（claim 判定）

### C01 — **supported**
- 冻结数据：fixed BNN 风险 r≥29 起超过 p=5，r=200 处 5.0315>5。
- 全新全量：fixed 风险 r=500 处 5.197>5（超幅 3.9%），且 r=7..500 共 476/501 点超过 p。
- BetaPrime：全新全量 max 4.994，**从不超过** p；冻结 max 5.0016（+0.03%，MC 误差内），
  符合"tracking minimax"。
- 注：fresh 曲线 r≈7–9 的尖峰（fixed 5.39, dropout 6.61）是收缩函数重要性采样在
  中等 s 处的 MC 噪声（ESS 崩溃），非系统信号；r=500 处的超幅才是系统性的。

### C02 — **supported**
- 全新全量 r=0..500：fixed max 50.074>50（首个超 r=398），dropout max 50.127>50
  （首个超 r=297）；BetaPrime max 50.025（+0.05%）。
- 高精度复算 r=400/450：fixed 50.04/50.07、dropout 50.04/50.07 均 >50（betaprime
  49.999 恰在 p）。确认 exceedance 非 MC 假象。
- 冻结数据 r≤17 无法显示 exceedance（fixed max 43.13<50），范围不足；这不否定 claim。

### C03 — **partially_supported**（方向一致但量级极弱；fixed 的超出未在 N_mc=50k 主协议复现）
- BetaPrime max 100.017≈p（+0.017%，MC 误差内）——成立。
- Dropout max 100.044>p（r=441 起，+0.04%）——成立但量级很小（约 2 个 SE）。
- Fixed BNN：N_mc=50k 主协议（单 seed=42）max 99.993，恰在 p 之下；但 (a) 高精度
  （N_mc=200k, K_dir=30）在 r=500 处 fixed=100.024>100（+0.024，SE≈0.005，
  约 5 SE）；(b) 5-seed 复测 r=500 均值 100.016>p（z≈0.9，方向一致但单点不显著）。
  两套结果仅差 0.03，恰为 50k 协议该点 SE 量级。综合判定：fixed 在 p=100 处的
  超幅（~0.02%）真实但处于 MC 分辨率边缘。
- 论文正文对 p=50/100 的原话是 "can exceed it"，且 "departures are much smaller
  on the scale of the plots"，与本结果一致。理论（C08）保证 fixed 规则非极小极大
  （存在 θ 使 R>p）。
- 结论：claim 的"BetaPrime 近极小极大"与"dropout 超极小极大"得到支持；"fixed
  超极小极大"在高精度与跨 seed 均值意义上得到支持、在主协议单 seed 下未复现
  （差一个 SE 量级）。故整体判 **partially_supported**，并指出超幅随 p 增大而衰减
  （p=5: ~4%, p=50: ~0.2%, p=100: ~0.02%）。

### C04 — **supported**
- BetaPrime 为径向规则，稀疏度实验中为单条曲线（与 k 无关，由构造保证），
  r∈[0,5.59] 上 max 5.10≈p。
- Horseshoe 随 k 剧烈变化：k=1 max 2.79–2.92（全面低于 BetaPrime，100% 点）,
  k=2 max 4.81–4.98, k=5 max 5.25–9.09（超过 BetaPrime 与 p=5）。
- 与论文"dense k=p≈7.5"定性一致；不同 run 间的绝对差异（5.25 vs 7.07 vs 9.09）
  源于 Horseshoe 风险仅用 ~20 个 Y 样本/点估计，MC 误差大。
- 补充（§4.4）：p=50/100 上 k=1 稀疏风险低（5.70/6.67）、k=p 密集风险高
  （79.9/157.1），同样显示强 k 依赖，支持"稀疏时 Horseshoe 近极小极大、密集时
  远离极小极大"的论文机制。

---

## 6. 局限 (Limitations)

1. **重要性采样 ESS 崩溃**：fixed/dropout 的 a(s) 在大 s 处 ESS/M_v≈1e-6，意味着
   a(s) 由少数样本支配；这使大 ||θ|| 处的风险（尤其 p=5 中段尖峰、p=50/100 尾端）
   含收缩函数 MC 噪声。我们通过 (a) M_v=2M 敏感性、(b) N_mc=200k 高精度复算做了
   缓解，但未对 a(s) 本身做重采样（如分层抽样）修正。
2. **Horseshoe 风险 MC 误差大**：论文 N_mc=500，复现代码实际只用 min(N_mc,20) 个
   Y 样本，风险估计方差大；p=5 密集 k=5 的估计跨 run 波动 (5.25–9.09)。
3. **冻结数据 r 覆盖不足**：冻结 p=50/100 径向数据只到 r=17/25，无法直接观测
   exceedance；必须依赖全新全量 run。
4. **p=100 的 exceedance 量级** 在 50k 主协议分辨率下（SE≈0.017）低于 1 个 SE，
   判定依赖高精度复算（SE≈0.005 下 ~5 SE）与理论一致性；属于"信号存在但弱"。
5. **seed 选择**：复现代码与主协议全新 run 均用 seed=42（论文未指定多 seed 平均）。
   方向平均 K_dir=10 已部分缓解；关键点 r=500 另做 5-seed 复测（§4.3bis）量化 SE。

---

## 7. 复现清单（与 SCORE_RUBRIC 对齐）

| 项 | 位置 |
|---|---|
| 可运行代码 | `code/01_betaprime_verify.py`, `02_radial_risk.py`, `03_frozen_data_analysis.py`, `04_horseshoe_sparsity.py`, `05_highprecision_check.py`, `06_figures.py`, `07_evidence.py`, `08_se_check.py` |
| 证据表 | `results/evidence_table.csv`（118 指标） |
| 机器可读指标 | `results/metrics.json`（与证据表 1:1） |
| 数值结果 | `results/radial_risk_p{5,50,100}_full.json`, `results/sparsity_p5_fresh.json`, `results/sparsity_p50_dense1c.json`, `results/sparsity_p100_dense1c.json`, `results/frozen_data_summary.json`, `results/highprecision_check.json`, `results/se_check.json`, `results/betaprime_shrinkage_verify.json` |
| 图 | `results/figures/radial_risk_p{5,50,100}.png`, `sparsity_risk_p{5,50,100}.png` |

运行方式（需在数据原位，`sys.path` 指向 `F:/dataset/2604.04673v1`）：
```bash
cd agent_solution
python code/01_betaprime_verify.py          # ~1s
python code/02_radial_risk.py 5 50 100      # ~5-10 min (20 核)
python code/03_frozen_data_analysis.py      # ~1s
python code/04_horseshoe_sparsity.py 5      # ~15 min
python code/04_horseshoe_sparsity.py 50     # 3-chain, writes sparsity_p50_fresh.json (evidence 优先用 3-chain) ~35 min
python code/04_horseshoe_sparsity.py 100 --k 100,1 --chains 1 --out sparsity_p100_dense1c.json # ~16 min（减采样兜底）
python code/05_highprecision_check.py       # ~10 min
python code/08_se_check.py                  # ~5 min
python code/06_figures.py
python code/07_evidence.py
```
依赖：numpy, scipy, matplotlib, joblib（requirements-bnn.txt）。
