# TASK: 超新星引力波信号的 EOS 分类 ML 模型评估——关键主张验证（L1）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

## 0. 任务类型与层级

- 层级：**L1（关键主张验证，critical claim）**
- 总分 100（评分规则见私有 `SCORE_RUBRIC.md`：A 核心结果达成度 60 / B 证据真实性 25 / C 方法与报告 15）
- 本 TASK.md 为公开部分；目标论文全文不提供，仅给出主张与出处及必要的方法规格。

## 1. 待验证的关键主张（claim）

论文 **Abylkairov et al. 2025, arXiv:2409.14508**，"Evaluating Machine Learning Models for Supernova Gravitational Wave Signal Classification" 主张：

> （1）在旋转核心坍缩超新星（CCSN）反弹引力波信号上做核物质状态方程（EOS）分类，除朴素贝叶斯外的 7 种 ML 模型（CNN、RNN、RF、SVM、LR、k-NN、XGB）在 GR 数据上准确率均 **>90%**（SVM 最高 **99.5±1.0%**；CNN 97.4、RNN 97.7、RF 96.8、XGB 96.6、LR 95.8、k-NN 93.8、NB 仅 48.9±5.0%）；
> （2）用 GREP（广义相对论有效势）近似波形训练的模型直接用于 GR 波形测试时准确率骤降至 **~30–41%**（SVM 29.9±2.5%），跨域失效；
> （3）按峰值频率 f_peak 对时间归一化后准确率提升，但最高仍仅 **68.0±4.3%**（SVM），**<70%**，说明 GREP 缺乏 EOS 分类所需的精度。

你的任务：在冻结官方数据集（Zenodo 13774509，`GR_vs_GREP.csv`，CC-BY-4.0）上按论文方法规格复现分类实验，量化上述 3 个主张，判断其在冻结数据上是否成立。

## 2. 数据说明

### 2.1 冻结数据（`data/`）

| 文件 | 内容 | 规模 |
|---|---|---|
| `data/GR_vs_GREP.csv` | 864 条 CCSN 反弹 GW 波形（452 GR + 412 GREP；4 种 EOS）+ 元数据列 | 167,797,248 字节 |
| `data/MANIFEST.tsv` | `path | size_bytes | sha256` | — |
| `data/SOURCE.md` | 来源与许可记录 | — |

### 2.2 Schema（CSV：1 行 = 1 波形，10005 列）

- 列 0–9999：波形应变采样，表头为时间网格（单位 ms，步长 0.1 ms = 10 kHz），范围 **−993.0 ~ 6.9 ms**（论文分析用 **−2 ~ 6 ms** 窗口，即 81 个采样点）。
- 列 10000 `T/|W|`：反弹时旋转动能/势能比。
- 列 10001 `GR_or_GREP`：0 = GR（452 条）、1 = GREP（412 条）。
- 列 10002 `EOS`：0=SFHo（116 GR / 105 GREP）、1=LS220（120/105）、2=HSDD2（108/103）、3=GShenFSU2.1（108/99）——与论文 §II.A 完全一致。
- 列 10003 `f_peak`：反弹后峰值频率（Hz）。
- 列 10004 `D Delta h`：振幅（D·Δh，cm）。

### 2.3 来源与许可

- 来源：Zenodo 记录 13774509（论文数据可用性声明 doi:10.5281/zenodo.13774509），文件 `GR_vs_GREP.csv`；下载日期 2026-08-13。
- 许可：**CC-BY-4.0**（Zenodo 记录元数据）。
- 波形由论文团队用 CoCoNuT 代码模拟（GR-CFC 与 Newtonian+GREP case A；s12 前身星模型，T/|W|∈(0.02,0.18)），是论文的原始模拟数据（公开授权）。
- 完整性：SHA-256 固定于 `MANIFEST.tsv`。

### 2.4 与论文口径的对应（必须遵守）

- 论文 §II.A：采样 10 kHz，时间区间 −2~6 ms（零时刻=反弹），CNN 输入层为 (81)；所有波形按振幅 D·Δh 归一化。
- 论文 §II.B：64:16:20 训练/验证/测试切分（经典模型不用验证集）；评估重复 **100 次**随机切分，报告均值±标准差。本任务允许 ≥10 次（须注明与论文 100 次的差异）。
- 论文 Table III 给出经典模型超参搜索空间（GridSearchCV，5 折）；SVM 最优为 **poly 核、degree=4、C=10**（论文正文明确）。CNN/RNN 架构见 §2.4 规格。

### 2.5 方法规格（来自论文，用于复现）

- **CNN**（10 层）：Input(81) → Conv1D(32,k=3,ReLU) → MaxPool(2) → Conv1D(64,k=3) → MaxPool(2) → Conv1D(128,k=3) → MaxPool(2) → Flatten(1024) → Dense(512,ReLU) → Dense(256,ReLU) → Dense(4,Softmax)。
- **RNN**（4 层）：SimpleRNN(64) → SimpleRNN(128) → Dense(64,ReLU) → Dense(4,Softmax)。
- 训练：Adam；early stopping（CNN 20 个 epoch、RNN 40 个 epoch 无改善即停，保留最小验证损失模型）。
- **经典模型**：RF/SVM/NB/LR/k-NN/XGB，超参按论文 Table III 搜索空间做 GridSearchCV（5 折）；SVM 固定 poly/degree=4/C=10。
- 指标：accuracy（式 2）、precision、recall（式 3–4）。

## 3. 实验要求

### 3.1 预处理（必须报告）

- 每行波形裁剪 −2~6 ms 窗口（81 点，10 kHz）；除以 D·Δh 归一化振幅；标签用 EOS 列。
- 报告：波形总数 864、GR 452 / GREP 412、各 EOS 数量（对照论文 §II.A）。

### 3.2 三个实验（每个 ≥10 次随机切分，报告 mean±std）

1. **GR 分类**：用 GR 数据训练并测试 8 个模型（64:16:20；CNN/RNN 用验证集早停）→ 对照论文 Table IV GR 行。
2. **GREP→GR**：用 GREP 数据训练，GR 数据测试 → 对照 Table IV GREP→GR 行。
3. **时间归一化（GREP*→GR*）**：按 f_peak 对时间归一化（如论文 [96] 口径：时间 × f_peak）后，GREP 训练、GR 测试 → 对照 Table IV GREP*→GR* 行。

### 3.3 必报指标（`results/metrics.json`）

- 8 模型 × 3 实验的 accuracy（mean±std，%），及 GR 实验的 precision/recall；
- 与论文 Table IV 对比表（含绝对差）；
- 主张判定结论（每项成立/不成立 + 依据）：
  1. GR 上除 NB 外全部 >90%；SVM 最高；
  2. GREP→GR 全部模型准确率显著低于 GR 同模型（论文 ~30–41%，SVM 29.9±2.5%）；
  3. 时间归一化后最高准确率 <70%（论文 SVM 68.0±4.3%）且明显高于未归一化 GREP→GR。

### 3.4 提交物（对齐 v3 规范）

`submission/run.sh`、`analysis_plan.md`、`results/{metrics,evidence_table,critical_checks,uncertainty}.json`、`figures/`、`report.md`、`provenance/`。

## 4. 数据铁律（必须遵守）

- 只用 `data/` 冻结数据；**禁止模拟/合成波形**（本任务数据本身就是论文公开的模拟波形，不得再自行生成或替换）。
- 不得修改冻结文件；以 `MANIFEST.tsv` 的 SHA-256 为准核验。
- 不得引入外部 CCSN 波形库冒充冻结数据（如需补充分析，须显式声明为附加实验且不参与主张判定）。
