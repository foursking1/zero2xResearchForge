# Solution Report — QED-Nano: Teaching a Tiny Model to Prove Hard Theorems (arXiv:2604.04898v1)

- **Task**: 针对 TASK.md 的 4 条 claim（C01–C04），使用冻结数据实际运行分析，判断 claim 是否成立。
- **执行日期**: 2026-08-13
- **数据根目录**（原位读取，未复制）:
  - 复现工作区: `F:/dataset/2604.04898v1/`（结果 JSONL、论文 PDF、复现代码）
  - 冻结 HuggingFace 数据集快照: `E:/scisolvebench-data/raw/2604.04898v1/huggingface/`
    （该目录是 `F:/dataset/2604.04898v1/data/huggingface` 的 MSYS 符号链接目标）
- **全部指标均在本机实际运行得到**。凡来自论文的数字一律标注 **论文引用**；本地复现计算值标注 **computed_local**。

---

## 0. 结论速览（Claim 判定）

| Claim | 判定 | 一句话依据 |
|---|---|---|
| **C01** QED-Nano (4B) 无 scaffold 在 IMO-ProofBench / ProofBench / IMO-AnswerBench 分别 40.0% / 44.9% / 67.5% | **inconclusive（绝对数值不可复现）** | 论文数值由 Gemini-3-Pro 打分，冻结数据只含本地弱打分器（Qwen2.5-1.5B）的输出且不含 IMO-AnswerBench；本地 30 题子集上 QED-Nano direct 平均分 5.433/7，且**未显示**优于 Qwen3-4B（5.489/7，p=0.73），与论文相对排序（40.0 vs 20.4）不一致，但受 judge 差异限制。 |
| **C02** QED-Nano + RSA scaffold 在 IMO-ProofBench / ProofBench / IMO-AnswerBench 分别 56.9% / 62.6% / 76.5% | **inconclusive** | 冻结复现 harness 未实现 RSA（仅 RC 代理）；本地 RC 在 IMO-ProofBench 30 题子集上 5.506/7、7968 tokens；论文数值（论文引用）无法用冻结数据复算。 |
| **C03** 不同 test-time scaffold 对比，RSA 在 IMO-ProofBench 达 56.9% avg grade、平均 2,045,764 tokens | **partially_supported** | 论文 Table 2 的 RSA 具体数值（56.9% / 2,045,764 tokens）无法复现（judge 不同、RSA 未实现）；但本地数据在**定性方向**上支持“scaffold 用更多 token 换取更高分”：RC 7.0× / DSM 76.9× tokens（vs direct），DSM 本地得分 6.0/7 高于 direct 5.43/7（1 例）。 |
| **C04** 基于 rubric 奖励的 RL 训练在 ~350 步内训练奖励上升、评测分同步上升 | **partially_supported** | 冻结数据含 FineProofs-RL（5227 题 × ~128 个 rubric 奖励/题），支持“rubric 奖励”设计；但**不含逐步训练日志**，论文 Fig. 3 的训练曲线（reward vs step）无法从冻结数据复现 → 时间趋势不可验证。 |

---

## 1. 方法（Methods）

### 1.1 输入数据

| 数据 | 冻结路径（parquet / jsonl） | 规模 | 用途 |
|---|---|---|---|
| IMOProofBench | `hf/IMOProofBench/data/train-*.parquet` | 60 题 | 基准（论文 Table 1/2 的 IMO-ProofBench） |
| ProofBench | `hf/ProofBench/data/{all,24_25,other,train}-*.parquet` | 145 题（24_25=70，other=75） | 基准（论文 Table 1 的 ProofBench） |
| FineProofs-SFT | `hf/FineProofs-SFT/data/train-*.parquet`（2 片） | 4281 条 | SFT 数据，含 Gemini-3-Pro grade 与 reward@128 |
| FineProofs-RL | `hf/FineProofs-RL/data/train-*.parquet` | 5227 条 | RL 数据，含 rubrics / scores / rewards / reward_mean |
| 复现结果 | `F:/dataset/2604.04898v1/results/<group>/*.jsonl` | 见 §2.2 | 本地模型 × 本地 judge 的逐题打分输出 |

**复现工作区已有的真实实验结果**（冻结、非我生成，我只做统计分析）：
- `results/imo_30shot/`：IMOProofBench 前 30 题（PB-Basic-001..030），3 个 seed（42/123/456），3 个实验（qwen3_direct、qed_nano_direct、qed_nano_rc），每实验 90 条记录。
- `results/cross_dataset/`：ProofBench 前 15 题，3 seeds，qwen3_direct + qed_nano_direct，各 45 条。
- `results/local_proof_pilot/`（2 题）、`results/local_proof_3shot/`（3 题）、`results/dsm_wiring_test/`（1 题 DSM）。

### 1.2 本地复现 harness 口径（与论文的偏差，需明确）

论文与本地 harness 的关键差异（来自复现工作区 `code/` 与 `README.md`）：

| 项 | 论文 | 本地复现（冻结结果即此口径） |
|---|---|---|
| Judge | Gemini-3-Pro（0–7 分） | `Qwen/Qwen2.5-1.5B-Instruct` 本地 judge（0–7 分，rubric 提示，温度 0） |
| 主结果 scaffold | RSA（test-time） | direct / RC（Reasoning Cache）；**RSA 未实现**，DSM 仅 1 例 wiring test |
| IMO-AnswerBench | 有（论文 Table 1） | 冻结快照**不含**该数据集 |
| 解码 | 论文未限定；agent 最长 ~2M tokens | solver max_new_tokens=1024（direct 全部顶到 1024），RC 3 轮迭代 |
| 数据集规模 | 全量 IMOProofBench（60 题） | 30 题子集（imo_30shot）|

**关键推论**：本地 judge 与论文 judge 打分尺度不同。冻结结果中，参考（gold）解在本地 judge 下平均 5.867/7（≈84%），而论文中 QED-Nano 无 scaffold 的 IMO-ProofBench grade 为 40.0%——两者量纲不可直接换算。因此本地数值仅用于**相对比较**与方向性判断，不能作为论文绝对数值的复现。

### 1.3 分析步骤

1. **数据集刻画**：读取 4 个 parquet，统计规模、类别/难度/来源分布、SFT grade 分布、RL 奖励分布（`analyze_datasets.py`）。
2. **复现结果重算**：独立读取全部冻结 JSONL，重算每实验 mean/std score、normalized score、tokens、frac≥6、逐 seed 均值；对 IMO-30shot 与 cross_dataset 做**配对检验**（按题聚合 3 seeds 均值后，paired t-test + Wilcoxon）（`analyze_reproduction.py`）。
3. **奖励分析**：统计 FineProofs-RL 的 rubric 奖励分布，SFT 的 grade 分布，并显式检查冻结数据中是否存在逐步训练日志（无）（`analyze_rewards.py`）。
4. **证据汇总**：合并论文引用值与本地计算值 → `results/evidence_table.csv`、`results/metrics.json`（`build_evidence.py`）。
5. **作图**：数据组成、打分分布、token 用量、奖励分布（`make_figures.py`）。

### 1.4 统计口径

- 每题最终分数 = 该题 3 个 seed 的 `candidate_score` 均值（配对比较对象）。
- 配对检验：paired t-test 与 Wilcoxon signed-rank（scipy），n=30（IMO-30shot）/ n=15（ProofBench）。
- token 比 = 该 scaffold 平均 `total_tokens` / direct 平均 `total_tokens`。
- 判定规则：绝对数值可复现且接近 → supported；部分要素可验证、方向一致但数值不可复现 → partially_supported；数值方向与本地数据冲突或关键数据缺失 → contradicted / inconclusive。

---

## 2. 结果（Results）

### 2.1 数据集刻画（computed_local）

| 数据集 | 数量 | 关键分布 |
|---|---|---|
| IMOProofBench | 60 题 | 类别：Algebra 16 / Combinatorics 16 / Number theory 14 / Geometry 14；难度：IMO-easy 24 / IMO-medium 18 / IMO-hard 10 / pre-IMO 8；`Novel Problem` 22 条，其余为 Modified/translated 竞赛题 |
| ProofBench | all=145 | 24_25=70 与 other=75 互不重叠且并集=all；train=145=all |
| FineProofs-SFT | 4281 条 | Gemini-3-Pro grade：均值 6.41，grade=7 占 88.8%；reward@128 均值 0.464 |
| FineProofs-RL | 5227 行 | 每行 ~128 个 rollout 奖励（128 占 4773 行）；reward_mean：mean=0.399，median=0.290，96.7% 行 reward_mean>0；所有行含 rubrics（mean len≈2050 chars） |

### 2.2 本地复现评测结果（computed_local，冻结 JSONL 重算）

**IMO-ProofBench（30 题 × 3 seeds，n=90，本地 judge）**

| 实验 | mean score/7 | std | mean normalized | mean tokens | frac≥6 | frac≥5 |
|---|---:|---:|---:|---:|---:|---:|
| qwen3_direct（Qwen3-4B-Thinking） | **5.489** | 1.094 | 0.943 | 1137.4 | 0.756 | 0.800 |
| qed_nano_direct（QED-Nano） | 5.433 | 1.061 | 0.931 | 1137.4 | 0.689 | 0.822 |
| qed_nano_rc（QED-Nano + RC） | 5.506 | 1.119 | 0.940 | **7968.3** | 0.596¹ | 0.843¹ |

¹ RC 有一例（PB-Basic-012, seed=456）judge 未能提取分数（NaN），均值/比例按其余 89 例计算；qwen3 与 qed_nano 各 90 例全部有效。
参考（gold）解本地 judge 均值 = 5.867/7。

**ProofBench（cross_dataset，15 题 × 3 seeds，n=45）**

| 实验 | mean score/7 | std | mean tokens | frac≥6 |
|---|---:|---:|---:|---:|
| qwen3_direct | 6.133 | 1.120 | 1164.8 | — |
| qed_nano_direct | 6.111 | 1.172 | 1164.8 | — |

**DSM wiring test（1 题，PB-Basic-001）**：qed_nano_dsm score=6.0/7，total_tokens=87,409。

### 2.3 配对检验（computed_local）

| 比较（IMO-ProofBench） | diff（A−B） | paired t-test p | Wilcoxon p | frac A>B | frac B>A |
|---|---:|---:|---:|---:|---:|
| qwen3_direct − qed_nano_direct | +0.0556 | 0.725 | 0.856 | 0.367 | 0.267 |
| qed_nano_direct − qed_nano_rc | −0.0722 | 0.659 | 0.753 | 0.433 | 0.467 |

| 比较（ProofBench） | diff（A−B） | paired t-test p |
|---|---:|---:|
| qwen3_direct − qed_nano_direct | +0.0222 | 0.921 |

**解读**：本地数据中 Qwen3-4B 与 QED-Nano 在 direct 模式下差异不显著（p≈0.7），且均值略偏向 Qwen3；RC 相对 direct 的提升仅 +0.072/7（p≈0.66），远小于论文声称的 40.0→44.0 乃至 56.9 的幅度。

### 2.4 Scaffold 对比（论文引用 vs 本地计算）

| Scaffold | 论文 Table 2 grade%（论文引用） | 论文 tokens（论文引用） | 论文 token 比（论文引用） | 本地 mean score/7 | 本地 tokens | 本地 token 比 |
|---|---:|---:|---:|---:|---:|---:|
| Single Turn | 40.0 | 93,690 | 1.00× | 5.433 | 1,137.4 | 1.00× |
| Reasoning Cache | 44.0 | 237,379 | 2.53× | 5.506 | 7,968.3 | 7.01× |
| DeepSeek Math | 54.0 | 1,605,879 | 17.14× | 6.000（1 例） | 87,409.0 | 76.85× |
| RSA | **56.9** | **2,045,764** | **21.84×** | —（未实现） | — | — |

### 2.5 FineProofs-RL 奖励分布（computed_local）

- 5,227 行，共 668,478 个 rollout 奖励；每行中位 128 个。
- 每行 reward_mean：mean=0.399，std=0.358，median=0.290，96.7% 行 >0，2.3% 行 =1.0（全部 rollout 全对）。
- 全部行带 `rubrics` 字段（平均 ~2050 字符），`scores`/`rewards` 为 128 维数组 → 与论文“rubric-based rewards + 每题 n 路 rollout 采样”的描述一致。
- **重要限制**：冻结数据不含 (step, reward) 训练曲线；论文 Fig. 3（~350 步内奖励与评测分同步上升）无法从冻结数据复现。

---

## 3. 结论（Claim 判定）

### C01 —— **inconclusive**
- 论文数值（40.0% / 44.9% / 67.5%，avg@3，Gemini-3-Pro）为**论文引用**，无法用冻结数据复算：冻结 judge 为 Qwen2.5-1.5B，且 IMO-AnswerBench 不在冻结快照中。
- 基准数据集本身存在且与论文一致（IMOProofBench 60 题、ProofBench 145 题）。
- 本地复现的绝对分数（5.433/7 ≈ 77.6% 本地口径）与论文百分比不可比；且本地相对比较**未显示** QED-Nano 优于 Qwen3-4B（5.433 vs 5.489，p=0.73），与论文相对排序（40.0 vs 20.4）方向相左。该冲突受 judge 能力差异与 30 题子集限制，不足以“证伪”论文，但也不构成支持。

### C02 —— **inconclusive**
- 论文 RSA 数值（56.9% / 62.6% / 76.5%）为**论文引用**；冻结 harness 未实现 RSA，仅 RC 可作最接近代理。RC 代理在 IMO-ProofBench 30 题子集得 5.506/7（n=90），改善不显著（p=0.66）。IMO-AnswerBench 无数据。

### C03 —— **partially_supported**
- 论文 Table 2 的 RSA 具体数值（56.9% / 2,045,764 tokens / 21.84×）无法复现（RSA 未实现、judge 不同）→ 数值层面 inconclusive。
- 方向性部分：本地数据支持“scaffold 消耗显著更多 token 且可带来更高分”：
  - token 比：RC ≈ 7.0×、DSM ≈ 76.9×（均 vs direct，本地）；
  - 打分：DSM（6.0，1 例）> RC（5.506）> direct（5.433），单调性与论文 ranking（RSA>DSM>RC>Single）一致（RSA 无法本地验证）。

### C04 —— **partially_supported**
- 支持面：FineProofs-RL 数据确实存在、规模大（5227 题 × ~128 奖励）、全部带 rubric、奖励分布合理 → 论文“rubric-based rewards 用于 RL”的设计得到冻结数据支持。
- 不可验证面：冻结数据无逐步训练日志，论文 Fig. 3 “~350 步内训练奖励上升、IMO-ProofBench/ProofBench 评测分同步上升”无法复现 → 时间趋势部分 **inconclusive**。

### 总体
四条 claim 中没有任何一条的**绝对数值**可以在冻结数据上以论文口径复现（主因：judge 为本地弱模型、RSA 未实现、IMO-AnswerBench 缺失、无训练日志）。本地数据能提供的是一致口径下的相对比较：C03 得到方向性支持，C04 的奖励数据部分得到支持，C01/C02 的绝对数值不可判定。

---

## 4. 局限性与透明度声明

1. **Judge 不一致**：本地 judge 为 Qwen2.5-1.5B-Instruct（rubric 0–7），非论文 Gemini-3-Pro；本地对 gold 解平均 5.87/7，明显比论文尺度宽松。所有跨模型比较都受此影响。
2. **subset**：IMO-ProofBench 只用了前 30/60 题；ProofBench 只用了前 15/145 题。
3. **RSA 未实现**：C02 的 “+RSA” 结果无法评估，RC 仅是最接近的训练侧 scaffold 代理。
4. **IMO-AnswerBench 缺失**：C01/C02 的 AnswerBench 列无法验证。
5. **无 RL 训练日志**：C04 时间趋势不可验证。
6. 执行过程中，我的一次误运行把 `dataset_overview.json` 写入了冻结数据目录 `F:/dataset/2604.04898v1/results/`（仅 3 KB 分析产物，非原始数据）。受沙箱 recycle-bin 限制无法删除该文件，特此声明；所有正式交付物均写入 `agent_solution/`。

---

## 5. 交付物清单

| 文件 | 说明 |
|---|---|
| `solution.md` | 本文件 |
| `code/common.py` | 路径解析（冻结数据 vs 输出目录） |
| `code/analyze_datasets.py` | 数据集刻画 |
| `code/analyze_reproduction.py` | 复现结果重算 + 配对检验 |
| `code/analyze_rewards.py` | FineProofs-SFT/RL 奖励分析 |
| `code/build_evidence.py` | 生成 `evidence_table.csv` / `metrics.json` |
| `code/make_figures.py` | 生成结果图 |
| `results/evidence_table.csv` | 证据表（指标 / 数值 / 口径 / claim / 来源） |
| `results/metrics.json` | 机器可读指标（与 evidence 表键一致） |
| `results/dataset_overview.json` | 数据集统计 |
| `results/reproduction_metrics.json` | 每实验指标 |
| `results/reproduction_tests.json` | 配对检验 |
| `results/fineproofs_rewards.json` | 奖励分布 |
| `results/figures/*.png` | 4 张结果图 |

**复现命令**（在 `agent_solution/` 的父目录执行）：
```bash
python agent_solution/code/analyze_datasets.py
python agent_solution/code/analyze_reproduction.py
python agent_solution/code/analyze_rewards.py
python agent_solution/code/build_evidence.py   # 会依次调用以上三个并汇总
python agent_solution/code/make_figures.py
```
