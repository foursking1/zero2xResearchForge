# solution.md — Pensieve 符号性质验证复现（2604.04914v1）

> 论文：*Analyzing Symbolic Properties for DRL Agents in Systems and Networking*
> （Proc. ACM Meas. Anal. Comput. Syst., Vol. 10, No. 2, Article 29, June 2026; arXiv 2604.04914v1）
>
> 本报告只使用冻结数据（`F:\dataset\2604.04914v1`，原位读取），所有指标均由实际运行的代码计算产生。
> 引用论文中的数值一律标注 **论文引用**；凡由本项目计算得到的数值标注 **计算值**（可在 `results/` 与 `code/` 中复算）。

---

## 1. 任务与结论速览

| Claim | 判定 | 一句话依据 |
|---|---|---|
| C01 Pensieve Capacity Utilization heatmaps（MIP/CROWN，跨 checkpoint 与模型大小） | **partially_supported** | 冻结数据无 checkpoint；可在现有 small/mid/big 三个模型上重现"模型×查询"热图，MIP 与 CROWN 后端行为与论文定性一致但分辨率受限 |
| C02 π^128 与 π^64 奖励曲线几乎一致（4× 参数量差异） | **inconclusive** | 冻结数据无训练/奖励曲线，且公开 ONNX 模型（48 输入）与论文架构（25 输入、H=128/64）不匹配，无法验证 |
| C03 CROWN 与 MIP 后端查询执行时间存在显著差异 | **partially_supported** | 计算值：两种后端在 20s 预算下行为不同（CROWN 可短时解析部分查询，MIP 全部触顶超时），但分辨率受时间预算限制 |
| C04 Rebuffering Avoidance 与 Robustness 聚合结果 | **partially_supported** | 可在现有模型上给出 safe/unsafe/unknown 聚合堆叠图；无 checkpoint/coverage 数据，无法复现论文图 6 的全维度 |

详细证据见 §3、§4，证据表见 `results/evidence_table.csv`，机器可读指标见 `results/metrics.json`。

---

## 2. 数据、方法、口径

### 2.1 数据（冻结，原位读取）

- 数据根目录：`F:\dataset\2604.04914v1\data\official\applications\pensieve\`
- 模型：`model/onnx/pensieve_{small,mid,big}_simple.onnx`（3 个公开 checkpoint，ReLU 分类器）。
- 查询集：`capacity_utilization_input100.csv`（6 查询）、`rebuffering_avoidance_input100.csv`（6 查询）、`robustness_input100.csv`（12 查询），共 **24 个查询**。
- 所有查询均为 **input100**（100% coverage，ε=0.01，d=3），与论文 6.3 节所述"每单调性属性 6 查询、robustness 12 查询"的数量一致（论文引用：图 4 下方脚注列出 6 个无效输出对；6.3 节给出 6/6/12 的查询数）。
- 论文图 4/6 中的 checkpoint（ckpt 0–15）、coverage 60/80/100%、训练奖励曲线：**冻结数据中不存在**。

### 2.2 模型提取与验证

从 ONNX 图（输入 `1×6×8`=48 维，逐特征 embedding → concat → ReLU → FC(H) → ReLU → FC(6)）提取精确的序贯 ReLU 网络：

```
h0 = (mask ? relu : id)(W0 x + b0)      # W0: 48 -> {768,2048,2048}
h1 = relu(W1 h0 + b1)                    # hidden {128,128,256}
y  = W2 h1 + b2                          # 6 logits
```

- 提取方式：将 ONNX 中所有 `Relu` 替换为 `Identity` 后，在 x=0 与 48 个基向量上精确求值，恢复第一隐藏块仿射映射 (W0, b0)；W1/b1、W2/b2 直接读取 `Gemm` 初值；`mask` 通过 Relu 输出的传递闭包判定（concat 中未过 ReLU 的通道保持恒等）。
- 验证：与 onnxruntime 在随机输入上对比，最大绝对差 ≤ 2e-4（float32 精度水平）。`validate_net()` 在 `code/pensieve_verify/model.py`。

**模型参数量（计算值）：**

| 模型 | n_in | 第一隐藏块神经元数 | 共享隐藏层 | 总参数量 | 相对 small |
|---|---|---|---|---|---|
| small | 48 | 768（其中 640 过 ReLU） | 128 | 136,838 | 1.00× |
| mid | 48 | 2048（其中 1920 过 ReLU） | 128 | 363,398 | 2.66× |
| big | 48 | 2048（其中 1920 过 ReLU） | 256 | 626,438 | 4.58× |

论文引用：论文称 π^128 有 103,174 参数、π^64 有 27,142 参数（约 4× 差异），且输入为 25 维。
**结论：公开 ONNX 模型与论文所述架构不一致**（输入 48 而非 25；无 H=64 模型；small/mid 共享隐藏层 128，参数比 2.66× 而非 4×）。

### 2.3 查询解析与语义

VNN-LIB 查询定义 96 维比较输入 `u = [x; s]`（x=48 维基线状态，s=48 维扰动/增量），输出 12 维 `[f(x); f(x+s)]`。
输出约束形如 `Y_lhs ≤ Y_rhs`，表示 argmax 在扰动后不得从较高 bitrate 跳到较低 bitrate（超过 d=3 级）。
解析器 `parse_vnnlib()` 对 24 个查询全部解析成功；每个查询的 box 中非退化的变化维数为 26–48 维（a3_b0 为 26 维，robustness 查询更多）。
查询"违规"判定：存在 u ∈ box 使**所有** `Y_lhs ≤ Y_rhs` 同时成立（即 max-margin ≤ 0）。

### 2.4 验证后端（本项目实现，`code/pensieve_verify/`）

| 后端 | 原理 | 结果语义 |
|---|---|---|
| `heuristic` | 随机采样 + 差分进化（differential_evolution）+ CMA-ES（可选）最小化 max-margin | `unsafe`=找到确切反例（前向精确求值，certified）；`not_found`=未找到（无保证） |
| `mip` | 比较网络编码为 MILP（big-M ReLU 编码），HiGHS（scipy.optimize.milp）求解可行性 | `unsafe`=找到反例（可行解，witness 已用精确前向验证）；`safe`=不可行（安全）；`unknown`=超时/数值失败 |
| `crown_bab` | IBP 区间传播 + CROWN 线性松弛 + 输入 box 二分 B&B；预检查含 box 采样与 DE 攻击 | `unsafe`=反例；`safe`=全部子盒证伪；`unknown`=超时 |

关键参数：MIP 与 CROWN-BaB 单查询预算 **20 s**（论文用 600 s / Gurobi 28 线程 / Alpha-Beta-CROWN，论文引用）；heuristic 随机 4000 + DE(maxiter 60, popsize 12)，CMA 关闭。硬件：本项目在 Windows 11 / x86-64 单进程 CPU 上运行。

**MIP 编码正确性**：开发中修复了一处 big-M ReLU 编码符号错误（`h - z - l·d ≤ -l` 而非 `≤ l`），并用已知反例做约束行检查（6,078 行约束 0 违例）与精确前向 witness 校验；另将约束矩阵改为稀疏以适配 mid/big 模型（dense 需 1.15 GB）。

### 2.5 运行方式

```bash
cd code
# 实际运行命令（本次使用 20s 预算；完整 216 个后端运行约 1 小时）
python run_analysis.py --mip-timeout 20 --crown-timeout 20
# 结果追加写入 ../results/analysis_results.jsonl（共 216 条：3 模型 × 24 查询 × 3 后端）
python make_figures.py      # 生成 results/figures/*.png
python make_evidence.py     # 生成 results/evidence_table.csv（113 行）与 results/metrics.json（114 键）
```

---

## 3. 结果

### 3.1 Capacity Utilization（C01）

论文图 4 的热图轴为"checkpoint（ckpt 0–15）× 查询"，并对比模型大小与 MIP/CROWN 两种后端。冻结数据无 checkpoint，因此本项目在可复现的轴（**模型大小 × 查询**）上给出 MIP 与 CROWN 两个热图（`results/figures/fig_c01_capacity_heatmap_mip.png` / `_crown.png`）。capacity utilization 共 6 查询，结果如下（计算值，`results/analysis_results.jsonl`）：

| 模型 | MIP 解析数 | CROWN 解析数 | CROWN 解析的查询 |
|---|---|---|---|
| small | 0 / 6 | 1 / 6 | a3_b0 → **unsafe**（1.67 s） |
| mid | 0 / 6 | 0 / 6 | — |
| big | 0 / 6 | 0 / 6 | — |

- MIP 后端对全部 18 个（模型 × 查询）单元在 20 s 预算内均**不可行判定失败**（status=unknown，全部触顶）。
- CROWN 后端只在 small × a3_b0 上于 1.67 s 内找到一个**经精确前向验证的违规反例**（max-margin ≤ 0），其余 17 个单元超时。
- 定性趋势与论文一致：查询在 100% coverage 下对两种形式化后端都极难；small 模型上存在可被形式化证明的违规，而 mid/big 模型上没有任何查询能在预算内解析。但论文图 4 的"模型大小→热图更绿/更红"的具体模式无法跨 checkpoint 复现，分辨率受限于只有 3 个模型与 20 s 预算。
- **判定：partially_supported。**

### 3.2 训练奖励曲线（C02）

- 冻结数据中不存在任何训练过程数据：无 reward 序列、无 checkpoint 权重（`model/onnx/` 仅有 3 个最终推理模型）、无训练日志。
- 公开 ONNX 模型的参数量（small 136,838 / mid 363,398 / big 626,438）与论文所述 π^128（103,174）和 π^64（27,142）均不相等，且输入维数（48 vs 25）与共享隐藏层（128/128/256）均不匹配论文架构。
- 因此无法构造"H=128 与 H=64 奖励曲线几乎一致（4× 参数差异）"的验证。
- **判定：inconclusive（数据不可得）。** 相关证据 `training_reward_data_present = false`（`metrics.json`）。

### 3.3 查询执行时间（C03）

论文（论文引用）报告 CROWN 与 MIP 两种后端在查询执行时间上存在显著差异，且预算为 600 s（Gurobi 28 线程 / Alpha-Beta-CROWN）。本项目在 **20 s 预算**下对全部 72 个（模型 × 查询）对测量了两种后端的墙钟时间（计算值，`results/figures/fig_c03_exec_time_boxplot.png`，`metrics.json` 中 `C03__exec_time_*`）：

| 模型 | MIP 中位数 (s) | MIP 均值 (s) | CROWN 中位数 (s) | CROWN 均值 (s) | CROWN 最短 (s) |
|---|---|---|---|---|---|
| small | 20.73 | 20.83 | 20.03 | 18.52 | **1.67** |
| mid | 21.12 | 21.32 | 20.08 | 20.08 | 20.00 |
| big | 34.62 | 33.99 | 20.08 | 20.11 | 20.00 |

- **MIP（HiGHS/scipy.milp）**：72/72 个查询全部触顶 20 s 预算（big 模型上 HiGHS 还会在超时后额外滞留 12–21 s 才返回，故中位数达 34.6 s），解析数 0/72。
- **CROWN-BaB**：small 上有 2 个查询在预算内快速解析（capacity a3_b0：1.67 s；robustness a0_b3：2.05 s，均找到反例），其余 70/72 触顶。
- **差异的定性证据**：两种后端行为确实不同——CROWN 对少量 small 查询可"秒级"解析，MIP 则从未在预算内解析任何查询；模型越大越难（mid/big 全部触顶）。但绝大多数查询都在 20 s 触顶，无法观测到真实的求解完成时间，因此论文所述的"执行时间数量级差异"（在 600 s 预算下）在本项目无法定量复现，只能给出"差异存在但被预算截断"的定性支持。
- **判定：partially_supported。**

### 3.4 Rebuffering Avoidance 与 Robustness（C04）

论文图 6 的聚合堆叠图轴为 checkpoint（ckpt 0–15）× coverage（60/80/100%）。冻结数据只有 coverage=100%（`input100`）下的最终模型，因此给出**单 coverage 下的三引擎聚合堆叠图**（`results/figures/fig_c04_stacked_bars.png`）。聚合规则：任一后端 `unsafe` → unsafe；任一后端 `safe` → safe；否则 unknown（计算值）。

| 属性（查询数） | small | mid | big |
|---|---|---|---|
| capacity_utilization (6) | 1 unsafe / 5 unknown | 6 unknown | 6 unknown |
| rebuffering_avoidance (6) | 6 unknown | 6 unknown | 6 unknown |
| robustness (12) | 2 unsafe / 10 unknown | 12 unknown | 12 unknown |
| **合计 (24)** | **3 unsafe / 21 unknown** | **0 / 24 unknown** | **0 / 24 unknown** |

- **Rebuffering avoidance**：全部 18 个（模型 × 查询）单元均为 unknown——本项目任何引擎都既不能证明安全、也找不到反例。这与论文图 6 中 rebuffering 列在 100% coverage 下大量 unknown 的定性一致（论文引用），但论文中该属性低 coverage 下有较多 safe/unsafe 单元，本项目无法复现（无 60/80% coverage 数据）。
- **Robustness**：small 上 2 个查询（a0_b3、a3_b0）找到反例（unsafe），其余 unknown；mid/big 全部 unknown。模型越小越可能出现可证明的违规，与论文"较小模型更易解析"的趋势一致（论文引用）。
- 论文图 6 的 checkpoint × coverage 全维度无法复现，故**判定：partially_supported**（堆叠图结构可给出，但缺两个关键轴）。

### 3.5 补充指标（R08/R09 风格）

论文引用：论文称 π^128 被解析的查询中约 60% 仅由一个引擎判定（另一个超时）、较小模型（π^64）的 unknown 结果约少 45%。
本项目在可用模型上的对应统计（论文风格，口径见 `make_evidence.py`，`metrics.json` 中 `C03/C04__*`）：

| 指标（计算值） | small | mid | big |
|---|---|---|---|
| 由至少一个形式化引擎（MIP+CROWN）解析的查询数 | 2 / 24 | 0 / 24 | 0 / 24 |
| 被解析查询中仅一个引擎判定占比 | 100%（2/2） | —（无可解析查询） | — |
| 三引擎联合 unknown 查询数 | 21 | 24 | 24 |
| small 相对 larger 的 unknown 减少 | — | 12.5% | 12.5% |

论文的 60% 与 45% 无法在本项目定量复现：形式化引擎在 20 s 预算下解析率极低（2/72），且可用模型并非论文的 π^64/π^128。仅能给出同方向参考：small（最接近"较小模型"）的 unknown 确实少于 mid/big，且被解析查询全部只由一个引擎判定。**以上不作为论文数值的复现。**

---

## 4. Claim 判定与依据

| Claim | 判定 | 证据与依据 |
|---|---|---|
| **C01** Capacity Utilization 热图（MIP/CROWN × checkpoint × 模型大小） | **partially_supported** | 冻结数据无 checkpoint，只能在 3 个模型上重现"模型 × 查询"热图（`fig_c01_capacity_heatmap_{mip,crown}.png`）。MIP 对 18 个单元 0 解析；CROWN 仅解析 small×a3_b0（1.67 s，unsafe）。"100% coverage 下形式化解析极难、小模型相对更易解析"的定性一致，但 checkpoint 轴缺失。 |
| **C02** π^128 与 π^64 奖励曲线几乎一致（4× 参数差异） | **inconclusive** | 冻结数据无任何训练/奖励曲线（`training_reward_data_present=false`）；公开 ONNX 模型（48 输入、参数 136,838/363,398/626,438）与论文架构（25 输入、H=128/64、103,174/27,142 参数）不匹配，无 H=64 模型。无法构造验证。 |
| **C03** CROWN 与 MIP 执行时间存在显著差异 | **partially_supported** | 计算值：20 s 预算下 MIP 解析 0/72、CROWN 解析 2/72（small 上 1.67 s / 2.05 s 秒级解析），big 模型 MIP 中位数 34.6 s。行为差异定性存在，但绝大多数查询触顶超时，无法观测真实完成时间，故"差异幅度"不可定量复现。 |
| **C04** Rebuffering Avoidance 与 Robustness 聚合结果 | **partially_supported** | 计算值：单 coverage=100% 下三引擎聚合堆叠图可给出（`fig_c04_stacked_bars.png`）：small 3 unsafe/21 unknown，mid 与 big 全 unknown；Rebuffering 全部 unknown。与论文图 6 在 100% coverage 下 unknown 为主的定性一致，但 checkpoint × coverage 两轴无法复现。 |

**总体结论**：四个 claim 均无直接矛盾证据，但在冻结数据（无 checkpoint、无 reward 曲线、无低 coverage、公开模型与论文架构不符）与受限求解预算（20 s 单进程 vs 论文 600 s/Gurobi/Alpha-Beta-CROWN）下，最多只能给到**部分支持**；C02 因数据不可得而无法判定。

## 5. 局限与说明

1. **数据不可得维度**：论文图 4/6 依赖 checkpoint（ckpt 0–15）与 coverage（60/80/100%），图 4(c) 依赖训练奖励曲线；冻结数据只有 100% coverage（`input100`）下的 3 个最终模型与 24 个查询。这些维度无法在本任务中复现，故相关 claim 只能给部分支持/无法判定。
2. **后端能力差异**：论文使用 Gurobi（28 线程）与 Alpha-Beta-CROWN（VNN-COMP 冠军）且每查询预算 600s；本项目使用单进程 scipy/HiGHS MIP 与自研 CROWN/IBP 分支定界，预算 20s。因此"unknown 比例偏高"主要反映求解器/预算差异，不等于论文结论被否定。
3. **模型不匹配**：公开 ONNX 模型（48 输入、嵌入 768/2048、共享隐藏 128/128/256）与论文描述的 π^128/π^64（25 输入、H=128/64）不一致；本文所有结果仅对现有 3 个模型成立。
4. **反例的 certified 语义**：heuristic 与 crown_bab 的 unsafe 反例均经精确前向求值验证（max-margin ≤ 0，浮点容差 1e-9）；MIP 的 unsafe 反例额外用精确前向复核。`not_found`/`unknown` 不构成安全证明。
5. **MIP 编码**：修复了 big-M ReLU 编码符号错误并用已知反例校验（6,078 行约束 0 违例）；对 mid/big 采用稀疏约束矩阵（dense 会需 1.15 GB 内存）。即便如此，HiGHS 在 300s 内也无法证明/推翻一个已知可行的查询（small a3_b0），说明这些 100%-coverage 查询对开源 MIP 求解器很困难。
6. **磁盘限制**：运行期间 D 盘剩余空间仅 ~11 MB，分析结果以增量 JSONL 保存；交付物体积很小（< 1 MB），未受影响。
