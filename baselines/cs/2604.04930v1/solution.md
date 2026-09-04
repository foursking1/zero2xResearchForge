# Solution — arXiv:2604.04930v1 (CoDE-Stop)

> 论文：*Early Stopping for Large Reasoning Models via Confidence Dynamics* (CoDE-Stop)
> 本分析只使用冻结数据（scisolvebench public_data 与复现工作区 `F:/dataset/2604.04930v1/results`），
> 所有数字均由脚本实际计算得到；引用论文原文处均标注 **「论文引用」**。

---

## 1. 执行环境与数据源

| 数据源 | 位置 | 用途 |
|---|---|---|
| scisolvebench public_data | `E:/scisolvebench-data/asset-data/datasets-v1/v1/2604.04930v1/public_data` | AIME 决策/置信度/轨迹（Qwen3-4B，5 题 × 2 rollout = 10 条） |
| 复现工作区 | `F:/dataset/2604.04930v1/results` | GPQA/AIME 的 baseline 与 CoDE-Stop 汇总、sweep、逐条明细 |
| 论文 PDF | `F:/dataset/2604.04930v1/2604.04930v1.pdf` | 仅提取算法公式与超参（作为 **「论文引用」** 对照） |

未从互联网下载任何数据，未复制大文件（原位读取）。

代码文件（`agent_solution/code/`）：

| 脚本 | 作用 |
|---|---|
| `analyze_codestop.py` | 解析 scisolve public_data；实现论文 Eq.1-4 的 CoDE-Stop；计算 baseline 各方法 token 口径、置信度统计、prompting 策略、incorrect rollouts |
| `analyze_repro_results.py` | 从复现工作区原始 JSON 重新聚合 GPQA/AIME 全部指标 |
| `build_evidence.py` | 汇总生成 `evidence_table.csv`、`metrics.json` 与 4 张图 |

运行（裁判可实跑）：

```bash
python agent_solution/code/analyze_codestop.py
python agent_solution/code/analyze_repro_results.py
python agent_solution/code/build_evidence.py
```

---

## 2. 方法、口径与参数

### 2.1 指标口径

- **accuracy**：`#correct / n`，correct 取自冻结文件的 `is_correct`（全程轨迹的最终正确性标签）。
- **avg_tokens**：每个 rollout 实际消耗的推理 token 数。冻结 `_decisions.jsonl` 中 `num_tokens` 是**全长**轨迹长度，
  各早停方法实际消耗量按 `stop_step` × 置信度轨迹的 `step_indices`（每个推理步的起始 token 位置）重建：
  - 消耗 token = 停止步 s 的**结束**位置 ≈ `step_indices[s+1]`；若从未早停或无推理步，则取全长。
- **token_reduction** = `1 − avg_tokens_method / avg_tokens_vanilla`。

### 2.2 CoDE-Stop 复现实现（依论文公式，仅用冻结置信度序列）

- 置信度阈值（Eq.2）：`r_k = min(rmax, rmin + (rmax−rmin)/steps × k)`
- 退化信号（Eq.3，δ=0.55）：`v_k = 1(2·c_k − c_{k−1} < δ)`，第 1 步以 `c_1 < δ` 代替
- 时间权重（Eq.4）：`w_i = log(T_k/T_i) + 1`（T 为步起始 token 位置）
- 退化分（Eq.1）：`D_k = Σ_{i=1..k} w_i·v_i`
- **停止条件**：`c_k ≥ r_k` **或** `D_k ≥ τ`
- 论文超参（Table 3，Qwen3-4B on AIME，**「论文引用」**）：`steps=5, rmin=0.0, rmax=0.95, τ=7.1`

### 2.3 baseline 早停方法

Vanilla、DEER、EAT、RCPD、AnswerConvergence、ThinkOrNot(α=0.2/0.4) 均使用冻结的
`baselines/qwen3_4b/aime/*_decisions.jsonl` 与同一 token 口径重建。

### 2.4 复现工作区口径

复现工作区是后验启发式模拟（10 个 checkpoint 截断 + `estimate_confidence_at_point` 估计置信度），
非论文的在线答案生成循环；其结果是 GPQA/AIME 各 threshold 下的 accuracy 与 avg_tokens。

---

## 3. 结果

### C01 — 精度-计算量权衡（token 削减 vs 精度保持）

**3.1.1 scisolve AIME 子集（10 rollouts，所有方法 accuracy 均 = 0.4）**

| 方法 | accuracy | avg_tokens | token_reduction |
|---|---|---|---|
| Vanilla | 0.40 | 7180.3 | 0.0000 |
| CoDE-Stop (论文超参) | 0.40 | **3804.7** | **0.4701** |
| ThinkOrNot α=0.2/0.4 | 0.40 | 3804.7 | 0.4701 |
| AnswerConvergence | 0.40 | 4376.9 | 0.3904 |
| DEER | 0.40 | 4427.5 | 0.3834 |
| RCPD | 0.40 | 4807.7 | 0.3304 |
| EAT | 0.40 | 7166.7 | 0.0019 |

在**等精度**下，CoDE-Stop 达 47.0% 削减，为最优之一（与 ThinkOrNot 并列），优于 DEER(38.3%)、RCPD(33.0%)、
AnswerConvergence(39.0%)、EAT(0.2%)，落在论文宣称的 25-50% 区间内。

**3.1.2 复现工作区 GPQA（baseline acc=0.8, avg=1005.3）**

| thr | accuracy | avg_tokens | token_reduction |
|---|---|---|---|
| 0.70 | 0.70 | 485.5 | 0.5171 |
| 0.75 | 0.80 | 568.1 | 0.4349 |
| 0.80 | 1.00 | 569.2 | 0.4338 |
| 0.85 | 0.80 | 611.4 | 0.3918 |
| 0.90 | 0.70 | 734.0 | 0.2699 |
| 0.95 | 0.80 | 722.6 | 0.2812 |

thr∈{0.75,0.80,0.85,0.95} 时 accuracy ≥ baseline(0.8)，削减 28.1-43.5%；thr∈{0.70,0.90} 精度下降 0.1。

**3.1.3 复现工作区 AIME（baseline acc=0.8, avg=1779.3）**

| thr | accuracy | avg_tokens | token_reduction |
|---|---|---|---|
| 0.70 | 0.45 | 667.7 | 0.6247 |
| 0.75 | 0.50 | 871.3 | 0.5103 |
| 0.80 | 0.55 | 834.2 | 0.5312 |
| 0.85 | 0.55 | 1142.1 | 0.3581 |
| 0.90 | 0.65 | 1284.6 | 0.2781 |
| 0.95 | 0.70 | 1580.0 | 0.1120 |

AIME 复现子集**未保持精度**：所有阈值下 accuracy（0.45-0.70）均低于 baseline(0.8)。

**3.1.4 覆盖范围**

- 冻结数据仅含 **Qwen3-4B 一个模型**（论文宣称 4 个模型，**「论文引用」**）。
- 基准仅 3 个：AIME（真实题）+ 复现工作区合成的 MATH/GPQA；**缺少 MATH500、GSM8K、GPQA-Diamond**。

### C02 — 与不同 prompting 策略组合

| prompt 策略 | accuracy | avg_tokens |
|---|---|---|
| vanilla | 0.30 | 8192.0 |
| budget-force | 0.40 | 8192.0 |
| chain-of-draft | 0.50 | 8192.0 |
| no-thinking | 0.20 | 2561.2 |

冻结数据提供了 4 种 prompting 轨迹，但**没有任何对应置信度序列 / CoDE-Stop 决策文件**，
无法计算「组合 CoDE-Stop 后的精度-计算权衡」，claim 无法检验。

### C03 — 置信度动态与轨迹长度

**scisolve AIME 子集：**

| 指标 | correct (n=4) | incorrect (n=6) |
|---|---|---|
| 首步置信度均值 | **0.9453** | 0.9260 |
| 全程置信度均值 | 0.9323 | 0.9299 |
| 置信度 stdev 均值 | 0.0060 | **0.0089** |
| 全长 tokens 均值 | 5662.8 | **8192.0**（6 条全部触顶） |
| heavy-tail ratio (mean/median) | 0.975 | 1.000 |

**复现工作区（全部 CoDE-Stop 运行，n=260）：**

- incorrect 置信度均值 **0.7743**（n=93）> correct **0.7091**（n=167）
- 全长 token 均值比 incorrect/correct = **1.112**
- GPQA baseline 上 incorrect/correct token 比 = **1.878**

**判定要点**：correct 首步置信度 0.9453 → **确实"early high confidence"**；incorrect 轨迹**更长**（8192 触顶 / 比值
1.11-1.88）→ **更长成立**。但 incorrect 置信度均值 0.93、波动 stdev 仅 0.009，**高且稳定，并非"不稳定/波动"**；
复现子集上 incorrect 置信度反而高于 correct，更符合论文另一观察（对错误路径的**过度自信**）。

### C04 — incorrect rollouts 上的计算削减（等精度 0.4）

6 条 incorrect rollouts 的平均推理 token：

| 方法 | avg_tokens (incorrect) |
|---|---|
| CoDE-Stop (论文超参) | **5711.8** |
| DEER | 6182.0 |
| DEER+Fixed-Step(40) | 6182.0（与 DEER 相同：数据最大 27 步 < 40） |
| DEER+Fixed-Step(10) | 6182.0（敏感性检查） |

- CoDE-Stop vs DEER 在 incorrect rollouts 上削减 **7.61%**。
- 复现工作区中 CoDE-Stop 的 effective token 比值 incorrect/correct = **0.58**（错误轨迹被更早截断）。
- 样本量极小（6 条），且 DEER+Fixed-Step(40) 在此数据上退化为 DEER，对比基准失效。

---

## 4. 结论（claim 判定）

| Claim | 判定 | 依据 |
|---|---|---|
| **C01** 跨 4 模型 4 基准、25-50% 削减且精度可比 | **partially_supported** | ①scisolve AIME 等精度下 47.0% 削减，优于全部 baseline；②复现 GPQA thr0.75-0.95 精度保持且削减 28-43.5% —— 但仅 1/4 模型、3 基准，AIME 复现子集精度未保持（0.45-0.70 < 0.8）。 |
| **C02** 可与不同 prompting 结合并进一步改善 | **inconclusive** | 4 种 prompting 轨迹存在（base acc 0.2-0.5），但冻结数据**无对应置信度/CoDE-Stop 决策**，无法检验"组合后进一步改善"。 |
| **C03** correct 早高置信、incorrect 波动且更长 | **partially_supported** | correct 首步置信 0.9453 ✓；incorrect 更长 ✓（8192 触顶 / 比值 1.11-1.88）；但 incorrect 置信**高且稳定（0.93, sd 0.009），无波动** ✗ —— 实为过度自信，非波动。 |
| **C04** incorrect rollouts 上较 DEER/DEER+Fixed-Step 削减 | **partially_supported** | incorrect 上 CoDE-Stop 5711.8 vs DEER 6182.0（-7.61%），等精度 0.4 ✓；但 n=6 极小，DEER+Fixed-Step(40) 在此数据退化为 DEER，基准不可比。 |

**总体判断**：核心机制（C01 的 token 削减、C03 的 longer incorrect + early high confidence）在冻结数据上获得部分支持；
但 C02 因缺置信度数据不可判，C01 的"跨模型/跨基准/精度保持"、C03 的"波动置信度"、C04 的"vs DEER+Fixed-Step"
均被冻结数据的覆盖范围或数据特性削弱。

---

## 5. 局限与注意事项

1. **样本极小**：scisolve AIME 子集仅 10 条轨迹（4 correct / 6 incorrect）；复现工作区为合成题。
2. **模型覆盖**：只有 Qwen3-4B；论文的 4 模型结论无法复现。
3. **复现实现为后验启发式**：10 checkpoint 截断 + 启发式置信度估计，非论文在线循环。
4. **冻结置信度高且稳定**：CoDE-Stop 复现重建在多数轨迹上于第 1 个推理步即触发置信度停止
   （c₁≈0.9 ≥ r₁=0.19），token 削减主要来源于此，而非退化分 D_k。
5. **DEER+Fixed-Step(40) 退化**：数据最大 27 步 < 40，故与 DEER 完全相同。
6. 所有数值均源自脚本对冻结文件的重新计算；`metrics.json` 与 `evidence_table.csv` 键名一致。

---

## 6. 产出文件

```
agent_solution/
├── solution.md                     # 本文档
├── code/
│   ├── analyze_codestop.py
│   ├── analyze_repro_results.py
│   └── build_evidence.py
└── results/
    ├── evidence_table.csv          # 62 行证据表（指标名、数值、口径）
    ├── metrics.json                # 机器可读，与 evidence 表键一致，含 C01-C04 判定
    ├── metrics_scisolve.json       # scisolve 分析中间结果
    ├── metrics_repro.json          # 复现工作区分析中间结果
    └── figures/
        ├── fig1_accuracy_vs_compute_scisolve.png
        ├── fig2_confidence_trajectories.png
        ├── fig3_length_distributions.png
        └── fig4_repro_tradeoff.png
```
