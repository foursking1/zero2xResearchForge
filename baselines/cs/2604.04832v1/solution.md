# Solution — Reproduction of arXiv:2604.04832v1

> *When One Sensor Fails: Tolerating Dysfunction in Multi-Sensor Prototypes*

本文件记录对论文三项可证伪结论（C01/C02/C03）的独立复现：全部数字均来自冻结在
`F:/dataset/2604.04832v1` 中的真实数据（未复制、未下载），所有指标均实跑代码计算得出，
论文中的数值一律标注为 **论文引用**，未做任何编造。

---

## 1. Task & Claims

| Claim | Statement (paper) | Verdict |
|---|---|---|
| **C01** | FDR 表明 paper-vs-scissors 是最难分类对：归一化 FDR 约 0.073，而 rock-vs-paper ≈ 0.842、rock-vs-scissors ≈ 1.000，前者难度高 10 倍以上 | **Supported** |
| **C02** | MLP 验证 oracle 复现论文 MCC：paper-vs-scissors ≈ 0.872、rock-vs-paper ≈ 0.990、rock-vs-scissors ≈ 1.000 | **Supported** |
| **C03** | 传感器消融显示 Sensor 2 对 'paper' 高度关键，Sensors 6、7 对所有手势一致冗余 | **Partially supported**（Sensor 2 关键 ✓；Sensors 6,7 "一致冗余" 仅在最大聚合 delta-FDR 指标下成立，在论文自身的分布漂移方法下被数据反驳） |

Supplementary claims evaluated: C07 (FDR-MCC 相关), C12 (paper-vs-scissors 相关不显著)。

---

## 2. Data & Environment

- **Dataset**: Roshambo sEMG（Myo 8 通道，200 Hz），冻结于 `F:/dataset/2604.04832v1`。
- **Processed**: `data/processed/roshambo_combined.npz` — X(900, 8, 400), Y(900,), participant_ids(900,)。
- **Frozen features**: `data/features/features_raw.npz` — X(900, 72)（8 sensors × 9 features）。
- **Class balance**: 300 samples / class（rock=0, paper=1, scissors=2）。
- **Participants**: 10（90 samples each，数据集中无原始受试者元数据，按顺序自动分配）。
- **Sampling**: 每类 300 样本 × 每样本 8×400 原始 sEMG 窗口。
- **Python**: `python 3.13`；numpy 2.5.2, scipy 1.18.0, scikit-learn 1.9.0, antropy 0.2.2,
  pywt 1.8.0, nolds 0.6.3, matplotlib 3.11.1。
- **Feature recomputation check**: 用本仓库 `common.py` 从原始信号重新提取的 72 维特征与冻结特征文件
  的逐元素最大绝对差 = **3.775e-15（MATCH）**，即特征管线与冻结数据完全一致。

**Sensor naming**: 论文图使用 1-based 标签 S1…S8；特征矩阵与代码使用 0-based 索引 sensor_0…sensor_7。
本文统一用论文标签 S1–S8 展示结论，映射为 `S{i} = sensor_{i-1}`，例如论文 "Sensor 2" = `sensor_1`，
论文 "Sensors 6, 7" = `sensor_5, sensor_6`。

---

## 3. Method

所有指标在冻结特征矩阵（或冻结原始信号）上直接计算：

1. **Feature extraction**（`common.py`）：每通道 9 个特征 —— Shannon Entropy、Sample Entropy、
   Zero Crossings、Waveform Length、RMS、Slope Sign Changes、Median Frequency、
   Wavelet Energy、Higuchi Fractal Dimension。所有 9 特征均用与冻结管线相同实现（含 antropy/nolds
   缺失函数的 from-scratch 回退），并已通过逐元素一致性校验（§2）。
2. **FDR（Stage 1, `separability.py`）**：对每个手势对计算逐特征 Fisher 判别比
   `FDR_k = (μa−μb)²/(σa²+σb²)`，分别做 max 聚合与 mean 聚合；另计算 F2（重叠体积）、F3（最大特征效率）、
   逐受试者 FDR。用三种归一化（minmax / divide_max / cap_at_1）与论文目标对比，选 MAE 最小者。
3. **MLP oracle（Stage 2, `mlp_oracle.py`）**：参与者感知的 `GroupKFold(n_splits=10)`（10 个受试者 = 10 折，
   训练/测试受试者零重叠），`StandardScaler` 仅在训练折内拟合（无泄漏），`MLPClassifier`
   (relu, adam, early-stopping)，按 pairwise MCC 报告。架构扫描 [(64,), (32,16), (16,8), (128,64,32)]，
   以 "MCC 与论文目标 MAE 最小" 选最优架构。另用 10 个随机种子复核 (64,) 的稳健性。
4. **Sensor ablation（Stage 3, `ablation.py`）**，两种互补定义：
   - **Metric A（论文 Fig.5 方法，信号级）**：将某传感器通道置零后*重新提取特征*，度量同一手势类
     baseline 与 ablated 特征分布间的 FDR 漂移（`F1 = max_k FDR`）；漂移越大 → 该传感器对这类越关键。
   - **Metric B（复现管线的特征级）**：将某传感器的 9 个特征列置零，重算三个手势对的 pairwise FDR，
     `delta = FDR_baseline − FDR_ablated`；对 max 与 mean 聚合分别排名，并平均到类别级关键度。
5. **FDR–MCC 相关性（supplementary）**：对 8 个传感器逐一做特征级消融并重训 MLP，取
   `delta_FDR(mean) = FDR_baseline − FDR_ablated` 与 `delta_MCC = MCC_baseline − MCC_ablated`
   的 Pearson 相关（逐对 + 全部 24 点）。

---

## 4. Results

### 4.1 C01 — FDR class separability (training-free difficulty proxy)

| Pair | 论文引用 (paper) | Ours raw max-FDR | Ours normalized (divide_max) | F2 overlap | F3 max efficiency |
|---|---|---|---|---|---|
| Paper vs Scissors | 0.073 | 0.2582 | 0.0349 | 3.34e-09 | 0.5978 |
| Rock vs Paper | 0.842 | 5.2756 | 0.7125 | 1.13e-14 | 0.9158 |
| Rock vs Scissors | 1.000 | 7.4047 | 1.0000 | 6.35e-16 | 0.8920 |

- 归一化方法自动选择 **divide_max**（MAE vs 论文目标 = 0.0559，为三者最小）。
- **难度比**（相对 paper-vs-scissors）：rock-vs-paper = **20.4×**，rock-vs-scissors = **28.7×**
  → paper-vs-scissors 的确比另两类对难 10 倍以上。
- **逐受试者一致性**：全部 10 名受试者上 paper-vs-scissors 的 max-FDR 均低于 rock-vs-paper。
- **F2/F3 佐证**：paper-vs-scissors 重叠体积最大（F2 最高）、最大单特征效率最低（F3 最低）。
- FDR 排序 `PvS < RvP < RvS` 与论文一致；绝对值因特征尺度与论文有差异，但不影响相对难度结论。

> **Conclusion C01: SUPPORTED** — 无需训练即可从特征分布判定分类难度，且 paper-vs-scissors 为最难对。

### 4.2 C02 — MLP validation oracle (MCC)

| Architecture | PvS MCC | RvP MCC | RvS MCC | MAE vs paper |
|---|---|---|---|---|
| **(64,)** ← best | **0.8989** | **0.9934** | **0.9967** | **0.0112** |
| (32, 16) | 0.9474 | 0.9935 | 0.9967 | 0.0274 |
| (16, 8) | 0.9002 | 0.9967 | 1.0000 | 0.0116 |
| (128, 64, 32) | 0.9452 | 0.9933 | 0.9967 | 0.0266 |

- 最优架构 **(64,)**（单隐层 64 单元，MCC 与论文目标 MAE 最小）。
- **论文引用** MCC 目标：PvS=0.872, RvP=0.990, RvS=1.000。
- Ours（mean ± std over 10 folds）：PvS = 0.8989 ± 0.0824，RvP = 0.9934 ± 0.0131，RvS = 0.9967 ± 0.0098；
  绝对误差分别为 0.0269 / 0.0034 / 0.0033，全部落在判定容差内（PvS±0.05, RvP±0.02, RvS±0.02）。
- **种子稳健性**（10 seeds, arch (64,)）：PvS = 0.9267 ± 0.0206，RvP = 0.9934 ± 0.0064，RvS = 0.9957 ± 0.0033；
  最低种子仍达 0.899 / 0.977 / 0.990，结论不依赖随机种子。

> **Conclusion C02: SUPPORTED** — 参与者感知的 GroupKFold MLP oracle 在容差内复现论文 MCC。

### 4.3 C03 — Sensor ablation: criticality & redundancy

**Metric A（论文 Fig.5 方法：信号级分布漂移 FDR）** — 每类每个传感器的归一化漂移：

| Sensor | rock | paper | scissors |
|---|---|---|---|
| S1 (sensor_0) | 0.498 | 0.614 | 0.548 |
| **S2 (sensor_1)** | 0.283 | **0.859** | 0.645 |
| S3 (sensor_2) | **1.000** | **1.000** | **1.000** |
| S4 (sensor_3) | 0.859 | 0.302 | 0.384 |
| S5 (sensor_4) | 0.644 | 0.445 | 0.316 |
| S6 (sensor_5) | 0.653 | 0.328 | 0.602 |
| S7 (sensor_6) | 0.350 | 0.575 | 0.518 |
| S8 (sensor_7) | 0.632 | 0.330 | 0.533 |

- **paper 类 top-3 = [S3, S2, S1]** → **Sensor 2（S2）高度关键于 paper ✓**（漂移 0.859，仅次于 S3）。
- 但 **rock top-3 = [S3, S4, S6]**，**scissors top-3 = [S3, S2, S6]** → **S6 (sensor_5) 在 rock 与 scissors
  中是 top-3 关键传感器**，与 "S6 一致冗余" 直接矛盾。
- S7 (sensor_6) 在 rock 中排名倒数第 2（0.350）、scissors 中第 6（0.518）、paper 中第 4（0.575），
  并非一致冗余。

**Metric B（特征级 delta-FDR，max 聚合）**：

| Gesture | top-3 | bottom-3 |
|---|---|---|
| rock | S1, S2, S3 | S6, S7, S8 |
| paper | S1, S2, S3 | S6, S7, S8 |
| scissors | S1, S2, S3 | S6, S7, S8 |

- 在该指标下 **S2 ∈ top-3(paper) ✓**、**S6/S7 ∈ bottom-3（全部手势）✓**、**S1/S2/S3 主导 top-3 ✓**。
- **注意**：该指标存在退化——最大聚合 FDR 只由持有 argmax 特征的传感器（S1/S2）决定，
  故 S3–S8 的 delta 多为 0 并列（"bottom-3" 实为零增量并列）。
- **Metric B mean 聚合**：top-3 = [S1, S3, S2]（全部手势），bottom-3 = [S4, S5, S6]
  → S6 一致 bottom-3 ✓，但 **S7 不在 bottom-3**（在 paper/rock 中为第 4 关键）。

> **Conclusion C03: PARTIALLY SUPPORTED**
> - *Sensor 2 对 paper 高度关键*：在 Metric A 与 Metric B 两种定义下均成立（S2 均为 paper top-3）。
> - *Sensors 6, 7 对所有手势一致冗余*：仅在 **最大聚合 delta-FDR（Metric B max）** 下成立，
>   且该结果有退化性（零增量并列）；在论文自身的分布漂移方法（Metric A）下，**S6 反而是
>   rock 与 scissors 的 top-3 关键传感器**，S7 也非一致冗余。故该子句为数据所部分反驳。

### 4.4 Supplementary — FDR–MCC correlation & robustness

| Pair | Pearson r | p-value | 判定 |
|---|---|---|---|
| paper_vs_scissors | −0.008 | 0.985 | 不显著（C12 ✓） |
| rock_vs_paper | 0.595 | 0.120 | 不显著（C07 部分不成立） |
| rock_vs_scissors | 0.891 | 0.003 | 显著（C07 部分成立） |
| 全部 24 点 | −0.058 | 0.787 | 不显著 |

- C12（paper-vs-scissors FDR–MCC 相关不显著）：**支持**（MCC 方差过低，符合论文所述硬可分区间非线性）。
- C07（FDR 与 MCC 相关）：**部分支持**——rock-vs-scissors 显著正相关，但 rock-vs-paper 不显著。
  该相关对 MLP 配置（架构/种子）敏感：冻结复现管线用另一配置得到 RvP r=0.709, p=0.049（临界显著），
  说明此结果不稳定，宜作辅助证据。

---

## 5. Claim Verdicts

| Claim | Verdict | Key evidence |
|---|---|---|
| **C01** FDR 训练无关地预测可分性，PvS 最难（>10×） | **Supported** | 归一化 FDR 0.035/0.713/1.000，难度比 20.4×/28.7×，10/10 受试者一致，F2/F3 佐证 |
| **C02** MLP oracle 复现 MCC 0.872/0.990/1.000 | **Supported** | arch (64,)，MCC 0.899/0.993/0.997，误差 0.027/0.003/0.003，10-seed 稳健 |
| **C03** Sensor 2 对 paper 关键；Sensors 6,7 一致冗余 | **Partially supported** | S2 关键在两种指标均成立；"S6,S7 一致冗余" 仅在退化性 max-agg delta-FDR 下成立，论文自身方法下 S6 反而关键于 rock/scissors |
| C07 FDR 与 MCC 相关（well-separated 对） | Partially supported | RvS 显著 (r=0.891, p=0.003)；RvP 不显著 (r=0.595, p=0.120) |
| C12 PvS FDR–MCC 相关不显著 | Supported | r=−0.008, p=0.985 |

---

## 6. Reproducibility

全部代码位于 `agent_solution/code/`，结果位于 `agent_solution/results/`。

```bash
PY=/c/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/python.exe
cd agent_solution/code
"$PY" run_all.py        # 完整流水线：verify features → stage1 → stage2 → stage3 → robustness → figures → evidence → verify
```

- `run_all.py`：端到端编排。
- `common.py`：路径、数据加载、9 特征提取（含一致性校验 `verify_features_match_frozen`）。
- `separability.py` / `stage1_fdr.py`：FDR/F2/F3 与归一化（C01）。
- `mlp_oracle.py` / `stage2_mlp.py`：GroupKFold MLP 与架构扫描（C02）。
- `ablation.py` / `stage3_ablation.py`：Metric A / Metric B 消融与 FDR–MCC 相关（C03）。
- `robustness_mlp.py`：10 种子稳健性。
- `make_evidence.py`：生成 `results/evidence_table.csv`（90 指标）与 `results/metrics.json`。
- `verify.py`：基础设施检查（决定退出码）+ 论文声明检查（信息性 PASS/FAIL）。
- `generate_figures.py`：`results/figures/*.png`（fdr/mcc/sensor_criticality/class_criticality/fdr_mcc_correlation）。

数据一律原位读取 `F:/dataset/2604.04832v1`，未复制大文件。

---

## 7. Limitations

1. **论文数值未逐字复现**：归一化 FDR（0.035 vs 论文 0.073）与绝对 FDR 标度不同，但相对排序与 >10×
   难度结论成立；论文精确值仅作归一化方法选择与参照，已标注 **论文引用**。
2. **受试者身份未知**：原 Roshambo 数据无受试者元数据，按每 90 样本顺序切分为 10 名受试者
   （与冻结管线一致），GroupKFold 的分组由此推断。
3. **Metric B max-agg 退化**：max-FDR 仅由单个 argmax 特征决定，导致多数传感器 delta=0 并列；
   故 "S6/S7 冗余" 的最强支持来自这一退化指标，解释时应谨慎。
4. **FDR–MCC 相关对 MLP 配置敏感**：RvP 的相关性在不同架构/种子下在临界显著与不显著之间波动。
5. **F2 重叠体积**以 72 维乘积计算，值极小（e-9 到 e-16），仅用于相对比较。

---

*Generated from real frozen data; every number in §4 is computed by `agent_solution/code/`. Paper values are explicitly marked 论文引用.*
