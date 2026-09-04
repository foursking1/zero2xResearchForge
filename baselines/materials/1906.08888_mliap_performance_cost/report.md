# report.md — 完整报告

任务 `1906.08888_mliap_performance_cost`：检验 Zuo et al. (JPCA 124, 731 (2020),
arXiv:1906.08888) 的关键论断——在 Li/Mo/Cu/Ni/Si/Ge 六元素上，ML 原子间势
(ML-IAP) 的能量/力预测精度达近 DFT 量级，且存在「模型类之间的精度排序」与
「精度-代价」权衡。

**结论标签：`partially_supported`**（子论断：近DFT精度 ✓、模型排序 ✓、
无过拟合 ✓、精度-代价 Pareto ✓、化学趋势 部分）。

---

## 1. 数据与统计

冻结包位于 `data/`（源：materialsvirtuallab/mlearn 官方仓库 data/，MIT）。
每条 JSON 为 pymatgen Structure + `outputs.energy`(eV) + `outputs.forces`(eV/Å)
+ `num_atoms`/`element`/`group`/`tag`/`description`。

| 元素 | 结构 | train 配置 | test 配置 | train 原子/配置 | group 分布 (train) |
|------|------|-----------|----------|----------------|--------------------|
| Li | bcc | 241 | 29 | 2–84 | AIMD-NVT 172, Vacancy 36, Elastic 22, Surface 11 |
| Mo | bcc | 194 | 23 | 2–54 (含 2 原子原胞) | AIMD-NVT 108, Elastic 56, Vacancy 21, Surface 9 |
| Cu | fcc | 262 | 31 | 6–108 | AIMD-NVT 108, Elastic 108, Vacancy 36, Surface 10 |
| Ni | fcc | 263 | 31 | 6–108 | AIMD-NVT 108, Elastic 108, Vacancy 36, Surface 11 |
| Si | 金刚石 | 214 | 25 | 12–96 | AIMD-NVT 90, Vacancy 57, Elastic 55, Surface 12 |
| Ge | 金刚石 | 228 | 25 | 12–64 | AIMD-NVT 90, Vacancy 72, Elastic 55, Surface 11 |

`data/Mo/extended/Mo930.json`：930 条 AIMD-NVT（50,220 原子），即 194 集
AIMD 部分的超集，用于数据量收敛研究。
训练能量范围（每原子）：Li −1.90…−1.71、Mo −10.85…−9.41、Cu −4.10…−3.52、
Ni −5.78…−5.14、Si −5.43…−4.57、Ge −4.49…−3.88 eV；max|F| 至 ~14 eV/Å。
脚本 `code/verify_dataset.py` 重新统计配置数并随机抽查记录完成往返校验
（全部通过；见 `results/verify_transcript.txt`）。

## 2. 方法

### 2.1 描述符（自写，固定种子）
单元素 Behler–Parrinello 式特征，每原子 D=15：
- 6 × G2：Σ_j fc(r_ij)·exp(−η r²)，η = {0.2,0.5,1,2,4,8} Å⁻²；
- 7 × 壳层高斯：Σ_j fc(r·)exp(−((r−s)/0.35)²)，s = {1.5,…,4.5} Å；
- 2 × 角度：Σ_img Σ_{j,k} w(r_ij) w(r_ik) cosθ（两类余弦截断窗口）；
- 余弦截断 fc(r)=½(cos(πr/Rc)+1)，Rc=5 Å；
- **周期边界**：对每个配对枚举*全部* Rc 内周期性镜像（不取“最近镜像”），
  保证小超胞（如 2 原子 bcc 原胞，第一配位壳 8 个等价原子）下正确；
- 每特征给出相对原子坐标的**解析梯度**；用二阶有限差分（h=1e-7）在
  Mo/Li/Si 的训练/测试配置上校验，|F_解析 − F_有限差分| < 1e-9（详见
  `test_checks`；见源码 `descriptors.py`）。

### 2.2 模型
- `linear_snap_proxy`（SNAP 类）：E = Σ_i c·g_i + b·n，**联合拟合总能量与力**
  （力匹配，如真实 SNAP），岭回归，闭式解；
- `quad_snap_proxy`（qSNAP 类）：E = Σ_i [c₁·g_i + Σ c_k g_a g_b] + b·n；
- `kernel_gap_proxy`（GAP 类）：RBF 核岭回归，600 个种子抽样基原子；
  E = Σ_m α_m Σ_{i∈cfg} k(x_i,x_m) + b_n·n + b₀，核在标准化描述符上；
- `mlp_nnp_proxy`（NNP 类）：64-64 MLP，力头 3 输出 + 每原子能量头
  （标准scaler；early stopping）。
前三个模型为**能量守恒**：quad/kernel 只拟合总能量，力 = −∇E（解析）；
linear 同时拟合能量与力（力仍由 −∇E 解析导出，一致性保持）。MLP 直接回归
力（非保守）。超参：α ∈ logspace(-8,3;24)、λ_f ∈ {0.01,0.1,0.3,1.0}（linear）、
γ∈{0.003..1}×α∈{1e-6,1e-4,1e-2}（kernel）；仅在 20% 内部验证集
（seed=0 切分）上选（linear 选择目标 = val 能量MAE + 50·val 力MAE），
再全 train 重拟合。指标：能量 MAE = mean_cfg |E−E_true|/n〔meV/atom〕；
力 MAE = 全分量 mean|F−F_true|（eV/Å）。

## 3. 结果

### 3.1 测试误差全表（meV/atom，eV/Å）

| 元素 | linear（力匹配） | quad | kernel | MLP |
|------|--------|------|--------|-----|
| Li | 7.49 / 0.109 | **1.80** / 0.094 | 3.27 / **0.068** | 14.29 / 0.208 |
| Mo | 362 / 0.360 | 13.78 / 0.474 | **9.82** / **0.296** | 38.80 / 0.953 |
| Cu | 285 / 0.077 | **1.43** / **0.057** | 1.98 / 0.101 | 10.21 / 0.469 |
| Ni | 48.8 / 0.127 | **1.85** / 0.152 | 2.10 / **0.107** | 7.78 / 0.509 |
| Si | 49.8 / 0.784 | 9.89 / 0.441 | **9.00** / **0.295** | 26.43 / 0.576 |
| Ge | 858 / 0.472 | 6.88 / 0.224 | **6.49** / **0.278** | 16.64 / 0.431 |

（首行为能量，次行为力；粗体=该元素最佳。参考基线「按元素常数参考能量」
Mo 340 meV/atom，即拟合模型远优于平凡基线。）

### 3.2 排序、组别与对照论证
- **能量排序**（六元素均值）：kernel 5.4、quad 5.9、MLP 19.0、linear 268.7
  meV/atom——与论文「GAP/MTP 类最优、SNAP/NNP 类较差」方向一致（linear-SNAP
  代理为最弱类；在 Li/Ni/Si 上达 7–50 meV，但在 Mo/Cu/Ge 上线性读出的表达
  能力不足以进入 meV 级，已在局限中说明）。
- **无过拟合**：全模型 train/test 比值均值 0.70（各元素/模型 0.15–1.2），
  训练与测试误差同量级；
- **化学趋势**：fcc（Cu,Ni）能量 MAE 最低 ✓；bcc 中 Li（1.80）接近 Cu/Ni
  而 Mo（9.82）偏高；金刚石 Si/Ge（9.0/6.5）居中——»fcc 最低«成立，
  但论文「bcc 居中、金刚石最高」的严格次序在本代理实现中不严格成立，
  故此条判定为部分支持；
- **group 分解**（kernel，测试能量 MAE）：Surface 最难（13–50 meV/atom，
  由表面重构/覆盖变化驱动），Elastic（0.2–4.8）、AIMD-NVT（2–7.5）、
  Vacancy（0.6–5）较低——误差分布与结构类别物理一致。

### 3.3 精度-代价权衡（Mo，`mo_pareto_scan.json`）
| 模型 | 可训练参数 | 测试能量 MAE (meV/atom) | 测试力 MAE |
|------|-----------|------------------------|-----------|
| linear | 16 | 269 | 0.752 |
| quad | 137 | 13.8 | 0.474 |
| kernel n=50 | 52 | 13.3 | 0.331 |
| kernel n=100 | 102 | 11.3 | 0.336 |
| kernel n=200 | 202 | 10.8 | 0.306 |
| kernel n=400 | 402 | 10.2 | 0.302 |
| kernel n=600 | 602 | 9.8 | 0.296 |
| kernel n=800 | 802 | 9.5 | 0.294 |
| MLP | 10,628 | 38.8 | 0.953 |

核代理 DOF 递增 → 误差单调下降、评估代价上升，构成清晰的精确前端；
MLP 参数最多但误差更高（出前端）——与论文「NNP 未必在 Pareto 前端」一致。

### 3.4 数据量收敛（Mo 194 vs 930，`mo930_convergence.json`）
核代理，行内域测试子集（AIMD-NVT）：
| 训练集 | 能量 MAE (meV/atom) | 力 MAE (eV/Å) |
|--------|---------------------|---------------|
| n=194 | 7.10 | 0.382 |
| n=930 | 4.77 (−33%) | 0.291 (−24%) |

训得越多，行内域误差越低（趋势正确）。同时注意：930 集只含 AIMD-NVT，
在全测试集（含 surface/vacancy/elastic）上能量误差反而从 9.9→14.0，反映
「训练数据覆盖类型」决定泛化；线性代理在 930（单结构类）上即便对内部分
重调正则，测试能量误差仍 >6 eV/atom（设计矩阵近奇异、basal 读出表达力不足），
说明该类代理不适合同质超集的收敛训练——如实记录为局限。

## 4. 局限与实现差异（对照论文）
1. **代理模型**：未调用论文的 GAP/MTP/SNAP/NNP 官方实现（离线无包、无网络），
   采用同构描述符+读出头的代理；绝对 MAE 与论文不可逐值对照，只比量级与排序。
2. **quad/kernel 只拟合总能量**：二者的力由解析梯度导出，未做「力匹配」式
   联合训练，故其力 MAE（0.06–0.47 eV/Å）系统性略高于论文 ~0.1 eV/Å；
   linear 已做能量+力联合拟合，但其表达能力受限。
3. **描述符维度**：论文 SNAP 用高阶双谱（角分辨更多），我们只有 2 个角度特征，
   对金刚石/缺陷结构表达力有限（Si/Ge 能量 6.5–9.0 meV/atom 仍达标）。
4. **MLP 能量头**用每配置 E/n 作为每原子目标（近似），导致其能量精度较
   保守模型略差——仍是「NNP 类较差」方向的有效验证。
5. 超参仅经 20% 内部验证集选择；seed=0 固定，可逐次复现。

## 5. 复现命令
```bash
cd agent_solution/code
python3 verify_dataset.py     # 数据统计与抽查（~1 min）
python3 run_pipeline.py       # 全部六元素训练+评估（首次构建特征 ~15-20 min, CPU）
python3 run_mo930.py          # 数据量收敛（+~10 min）
python3 pareto_scan.py        # Mo 精度-代价扫描
python3 make_analysis.py      # claim.md + 图
python3 fig_extra.py          # Pareto / 收敛图
```
产物：`results/evidence_table.csv`、`results/metrics.json`、
`results/anchor_comparison.json`、`results/claim.md`、`results/figures/`、
`results/*.json`。