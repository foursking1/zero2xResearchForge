# Solution — arXiv 2604.04895v1 "Agentic Federated Learning"

**Paper**: Agentic Federated Learning: The Future of Distributed Training Orchestration
(Jarczewski et al., ICLR 2026 Workshop on AI for Mechanism Design and Strategic Decision Making)

**Task scope (RCBench L2, claims C01–C04)**: re-derive, from the frozen data, whether the
paper's four target claims hold.

---

## 0. 数据与出处（Data & provenance）

所有分析只使用冻结数据，原位只读引用，未复制大文件：

| 数据 | 路径 | 用途 | 可独立分析? |
|---|---|---|---|
| K-Agent 官方结果 CSV（CIFAR-10，论文 Table 1 的 CIFAR-10 半） | `F:\dataset\2604.04895v1\data\official_artifacts\k_agent.csv`（30 配置 × 3 次运行均值） | C01, C02 | ✅ 是 |
| MNIST smoke 基线（5 clients, 3 rounds, alpha=0.1） | `F:\dataset\2604.04895v1\results\local_baseline_comparison.csv` 及 `results\local_runs\*\raw\*.json` | C01（基线语境） | ✅ 是 |
| 论文 PDF（Table 1 MNIST 半、Table 2、Figure 3/4） | `F:\dataset\2604.04895v1\2604.04895v1.pdf` | C01(MNIST), C03, C04 | ⚠️ 仅论文引用（见 3.3/3.4） |

K-Agent CSV 与论文 Table 1 CIFAR-10 半逐值核对一致（例：`chain-of-thought-oort-qwen3:8b`
acc=0.3925/k=9.71/ST=2.54s 对论文 CIFAR-10 `9±4, 39±13, 2.53`），确认 CSV 就是论文 CIFAR-10
实验的机器可读版本。`download_mb/k_medio ≈ 11.76 MB`（每客户端模型传输量，全表一致）。

gpt-4o-mini 对比实验（raw-LLM / ToolAgent / FedAvg，C03/C04）在冻结数据集中**没有机器可读
文件**（`artifacts/collect_report.json` 的规则 R08–R15 全部标记 `no_evidence`；目录全量检索无
token/cost 数据文件）。因此 C03/C04 只能用论文 PDF 中 Table 2 / 正文的数值（下文明确标注
`PAPER-CITED`），不能当作独立复现。

---

## 1. 方法（Method）

所有数字均由 `code/` 下的 Python 脚本实际运行产生（系统 Python 3.13 + numpy/pandas/scipy，
无网络访问）：

1. **C01（CIFAR-10，可计算）**：解析 `k_agent.csv`（30 配置），按 selection method / prompt
   / LLM model 分组统计 accuracy；做单因素 ANOVA（`scipy.stats.f_oneway`）与两两 Welch t 检验
   （`ttest_ind(equal_var=False)`）；给出总体 accuracy 范围、方法间均值差、距均值 ±2pp 内的
   配置占比。C01 的 MNIST 腿用论文 Table 1 MNIST 半（27 配置，`PAPER-CITED`）与本地 smoke
   基线（5 clients/3 rounds）作语境。
2. **C02（可计算）**：CSV 的 `k_std` 列 = 各配置 K 跨轮次取值的标准差，直接度量"K 是否随
   round 动态变化"。统计 k_std>0 / =0 的配置数、k_medio 范围、k_std 均值/中位数/最大。另从
   MNIST smoke raw JSON 提取每轮 `selected_clients` 数量验证管线内每轮参与客户端数可变。
3. **C03 / C04（仅论文引用）**：把论文 Table 2（5/10/25/50 clients × raw-LLM/Tool-Agent 的
   completion/prompt tokens、总 token、总 cost、accuracy）从冻结 PDF 转录为结构化表格，计算
   token/cost 从 5→50 clients 的增长倍数、50 clients 处 LLM vs Tool 的 cost/token 关系，
   以及 10 clients 处两法 accuracy 对比。所有数值均带 `provenance=PAPER-CITED` 标签，不当作
   独立复现结果。

脚本入口：`code/run_all.py`（依次调用三个分析脚本并汇总 `evidence_table.csv`、
`metrics.json`）；`code/make_figures.py` 生成 `results/figures/` 下三张辅助图。

---

## 2. 结果（Results，关键数值）

### 2.1 C01 — K-Agent 在不同 LLM/提示技术下 accuracy 的可比性

**CIFAR-10（来自冻结 CSV，可独立计算）**：

| 指标 | 数值 |
|---|---|
| 30 个配置 accuracy 均值 ± std | 0.3782 ± 0.0137 |
| accuracy 范围（min–max, pp） | 0.3464 – 0.3925（**4.61 pp**） |
| 距均值 ±2pp 内的配置占比 | **90%** |
| 按 selection method 均值 | oort 0.3891 / random 0.3772 / poc 0.3734 / round_robin 0.3633 |
| method 间均值极差（pp） | **2.57 pp** |
| 按 prompt 均值 | chain-of-thought 0.3748 / description-only 0.3811 / few-shot 0.3799 |
| 按 LLM 均值 | qwen3:8b 0.3855 / llama3.1:8b 0.3830 / llama3.2:3b 0.3662 |
| ANOVA：method / prompt / model 的 p | 0.0086 / **0.5475** / 0.0009 |
| 两两 t 检验 | oort vs poc p=0.0123（+1.57pp）；oort vs random p=0.0204（+1.18pp）；poc vs random p=0.5523 |

解读：不同 **prompt** 间 accuracy 无统计差异（p=0.55）；不同 **LLM** 与 **method** 间存在统计
显著但**量级很小**的差异（最大均值差 ≤2.6pp），90% 配置落在均值 ±2pp 内。就"使用不同 LLM 与
提示技术可获得**可比** accuracy"而言，CIFAR-10 数据支持该说法。

**MNIST（仅论文引用 Table 1 MNIST 半）**：27 配置 accuracy 均值 96.46%，范围 95.0%–97.2%
（2.2pp），同样高度聚集。但冻结集中无 MNIST 的机器可读 K-Agent 数据，无法独立复核。

**固定 K 基线语境（本地 smoke，5 clients/3 rounds）**：oort=0.6260、poc=0.6260、
rrobin=0.5997、random=0.4805（由 raw JSON 重新推导，与冻结 `local_baseline_comparison.csv`
完全一致）。注意这是 MNIST 小规模基线，非论文规模（25 clients/50 rounds），且非 K-Agent。

### 2.2 C02 — K-Agent 是否跨轮次动态调整 K

| 指标 | 数值 |
|---|---|
| k_std>0（K 跨轮次有变化）的配置数 | **26 / 30（86.7%）** |
| k_std=0（K 恒定）的配置数 | 4 |
| k_medio 范围 | 4.93 – 12.67 |
| k_std 均值 / 中位数 / 最大 | 3.17 / 2.45 / 7.29 |
| 静态 K 配置列表 | description-only-poc-llama3.1:8b、description-only-poc-llama3.2:3b、description-only-random-llama3.1:8b、few-shot-poc-llama3.2:3b |
| smoke 管线每轮选中客户端数（oort） | [5, 3, 3]（avg 3.67，说明管线内每轮参与数可变） |

解读：绝大多数（87%）K-Agent 配置的 K 随轮次变化，k_std 中位数 2.45（相对 k_medio~8.6，
变异系数可观），且 4 个静态 K 配置恰与论文正文所述"description-only 下 PoC/Random 出现
静态 K"一致。数据直接支持"K 跨轮次动态调整"。注意冻结 CSV 只有聚合 std 而无逐轮 K 轨迹，
"上下文推理"层面（Figure 3 的 K 从 5 跳到 10 及推理日志）仅能靠论文引用佐证。

### 2.3 C03 — raw LLM vs ToolAgent vs FedAvg（MNIST, 10 clients, 25 rounds）

冻结数据集中**无此实验的机器可读数据**。可用的只有：
- 论文正文（Figure 4 说明）："the best-performing method was LLM"。
- 论文 Table 2（`PAPER-CITED`）：10 clients 处 raw-LLM acc=0.6937±0.0664，ToolAgent
  acc=0.7856±0.0857 → **ToolAgent 反而高 9.2pp**（`acc_10_llm_beats_tool=False`）。
- FedAvg random 在 10 clients/25 rounds 的 accuracy 在 Table 2 与冻结文件中均未提供。

即：论文自身的数值表（Table 2）与正文（Figure 4 叙述）方向不一致，且 Table 2 与 Figure 4
实验口径是否完全相同无法从冻结数据确认。结论：**无法验证（inconclusive）**。

### 2.4 C04 — ToolAgent 的 token 可扩展性与 50 clients 处成本交叉

全部来自论文 Table 2（`PAPER-CITED`）：

| 指标（5→50 clients） | raw-LLM | ToolAgent |
|---|---|---|
| 总 token 增长倍数 | **×6.53**（1515→9894） | **×1.16**（6358→7404） |
| 总成本增长倍数 | **×5.17** | **×1.20** |
| 50 clients 总成本（$） | **0.001593** | 0.000961 |
| 5 clients 总成本（$） | 0.000308 | 0.000804 |

- 50 clients 处 LLM cost > ToolAgent cost：**True**（0.001593 > 0.000961）；5 clients 处相反
  （LLM 0.000308 < Tool 0.000804）→ 成本交叉发生在 5 与 50 之间，与论文叙述一致。
- 每客户端 token：50 clients 时 LLM 197.9、Tool 148.1；Tool 随规模增长明显更平缓。

结论：**支持（supported）**——但注意该结论完全建立在作者公布于冻结 PDF 的 Table 2 数值上，
无法从原始数据独立重算（无 token 明细数据）。

---

## 3. Claim 判定（Verdicts）

| Claim | 判定 | 置信度 | 依据 |
|---|---|---|---|
| **C01** K-Agent（不同 LLM/提示）在 CIFAR-10 与 MNIST（25 clients/50 rounds, alpha=0.1）达到与基线 (PoC/Random/Oort) 可比 accuracy | **partially_supported** | medium | CIFAR-10 腿：冻结 CSV 显示 30 配置 accuracy 全在 4.6pp 带内、90% 在均值 ±2pp，prompt 间无差异（p=0.55）、LLM/method 差异 ≤2.6pp → "不同 LLM/提示可获得可比 accuracy"成立。但"与无 LLM 的固定 K 基线持平"无法从冻结数据独立验证（无 CIFAR-10 非 LLM 基线）；MNIST 腿仅有论文引用值（96.5±1pp），不可独立复核 |
| **C02** K-Agent 跨通信轮次动态调整 K，展现上下文适应性 | **supported** | medium-high | 87% 配置 k_std>0，k_std 中位数 2.45，k_medio 范围 4.9–12.7；4 个静态 K 配置与论文叙述吻合。注：逐轮轨迹/推理日志在冻结数据中缺失，"上下文性"仅靠论文 Figure 3 佐证 |
| **C03** raw LLM (gpt-4o-mini) 在 MNIST 10 clients/25 rounds 优于 ReAct ToolAgent 与 FedAvg random | **inconclusive** | low | 冻结数据无此实验文件；论文 Table 2 在 10 clients 处显示 ToolAgent(0.786) > LLM(0.694)，与正文 Figure 4 叙述（LLM 最好）方向矛盾；FedAvg random 数值缺失 |
| **C04** ToolAgent 的 token 可扩展性优于 raw LLM，50 clients 处 LLM 成本超过 ToolAgent | **supported** | medium | 论文 Table 2（PAPER-CITED）：token 增长 LLM ×6.53 vs Tool ×1.16；50 clients 处 LLM cost $0.001593 > Tool $0.000961；5 clients 处相反，交叉点位于 5–50 之间。无独立原始数据可重算 |

### 3.1 C01 判定的细化说明
C01 实际包含三层含义，分开看更准确：
- (a) 不同 **prompt** → accuracy 可比：✅ 支持（ANOVA p=0.55）。
- (b) 不同 **LLM** → accuracy 可比：✅ 大体支持（最大均值差 1.9pp，llama3.2:3b 略低），
  统计显著但效应微小。
- (c) K-Agent（LLM 驱动动态 K）→ 与 **固定 K 基线** accuracy 持平：⚠️ 无法从冻结数据验证
  （CIFAR-10 无非 LLM 基线；本地 MNIST smoke 是 5 clients/3 rounds，且非 K-Agent）。
因此整体 **partially_supported**。

### 3.2 C02 判定的细化说明
"动态调整 K"被冻结数据直接证实（k_std>0 的配置占 87%，且与论文静态 K 叙述一致）；
"上下文适应性"（依据联邦状态推理调整）需要逐轮 K 与推理日志，冻结数据只含聚合 std，故置信度
取 medium-high 而非 full。

---

## 4. 局限（Limitations）

1. **CIFAR-10 K-Agent 数据是官方 artifact，非本地重跑**。它是作者公布在
   `data/official_artifacts/k_agent.csv` 的 3 次运行聚合；本次仅做统计分析，未重训 FL 模型
   （冻结集中无 CIFAR-10 数据、无 Ollama/LLM 运行环境）。
2. **MNIST K-Agent 与 gpt-4o-mini 实验无机器可读数据**。C01-MNIST、C03、C04 全部依赖冻结
   PDF 的表格数值（已明确标注 `PAPER-CITED`）。C03 甚至出现论文内部（Table 2 vs Figure 4
   叙述）方向矛盾，故判 inconclusive。
3. **局部 smoke 与论文规模不可比**。smoke（5 clients/3 rounds, qwen3:0.6b，实际未调用 LLM，
   `messages=[]`）只用于展示管线可运行与基线方向（informed > random），不用于验证论文数值。
4. **CIFAR-10 无逐轮 K 轨迹**：C02 无法从冻结数据给出论文 Figure 3 那样的逐轮 K 曲线，只能
   用 k_std 佐证。
5. **论文 Table 1 MNIST 半为 PDF 排版提取**：列（K/Acc/ST）存在错位风险，其中 accuracy
   （95–97%）清晰可信，ST 列有排版歧义；MNIST 半的 ST 值未用于任何判定。

## 5. 复现/执行说明

```bash
cd agent_solution/code
python run_all.py        # 运行三个分析并产出 evidence_table.csv / metrics.json
python make_figures.py   # 生成 results/figures/*.png（辅助图）
```

产物：`results/evidence_table.csv`（40 项指标，含指标名/数值/口径/claim/出处）、
`results/metrics.json`（同指标机器可读）、`results/figures/`、以及各中间表
（`k_agent_cifar10_configs.csv`、`paper_table2_llm_vs_tool.csv`、
`paper_table1_mnist.csv`、`smoke_per_round.csv` 等）。

**铁律合规声明**：未从互联网下载或补充任何数据；所有"计算得到"的数字均由脚本在本机冻结数据
上实跑获得；所有"论文引用"数值均在结果表中以 `PAPER-CITED` 标注出处。
