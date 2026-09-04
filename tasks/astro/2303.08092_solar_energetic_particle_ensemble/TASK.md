# TASK: 太阳高能粒子（SEP）集成深度学习预测——关键主张验证（L1）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

## 0. 任务类型与层级

- 层级：**L1（关键主张验证，critical claim）**
- 总分 100（评分规则见私有 `SCORE_RUBRIC.md`：A 核心结果达成度 60 / B 证据真实性 25 / C 方法与报告 15）
- 本 TASK.md 为公开部分；目标论文全文不提供，仅给出主张与出处。

## 1. 待验证的关键主张（claim）

论文 **O'Keefe et al. 2024, Advances in Space Research, arXiv:2303.08092（v2）**，"The Random Hivemind: An Ensemble Deep Learner Application to Solar Energetic Particle Prediction Problem" 主张：

> 随机集成深度学习方法（Random Hivemind，RH）在太阳高能粒子（SEP）事件预测上，与单模型常规神经网络（CoNN）和同特征委员会集成（Committee）相比，**性能相当或更好且得分离散度（std/MAD）显著更低**（对随机切分更稳健）；其中 **RH v2 平均优于 CoNN、Committee 与 RH v1**。关键数值（Table 2 中位数±MAD）：TSS 从 CoNN 0.906±0.042 提升至 Committee 0.926±0.023、RH v1 0.915±0.010、RH v2 0.944±0.005；HSS 0.163±0.026 → 0.168±0.005 / 0.163±0.010 / 0.168±0.008。

你的任务：在冻结官方数据集（SEP³ 门户发布的 TEBBS 耀斑属性与 SEP 关联标签，`SEPTEBBS.json`）上，按论文方法规格复现 4 种分类器（CoNN / Committee / RH v1 / RH v2），用多次随机 70/30 切分评估，判断上述主张在冻结数据上是否成立，并与论文锚数值（Table 1/Table 2）对比。

## 2. 数据说明

### 2.1 冻结数据（`data/`）

| 文件 | 内容 | 规模 |
|---|---|---|
| `data/SEPTEBBS.json` | GOES 软 X 射线耀斑（2002–2018）TEBBS 算法属性 + SEP 关联标签 | 24,797 行，7,499,398 字节 |
| `data/MANIFEST.tsv` | `path | size_bytes | sha256` | — |
| `data/SOURCE.md` | 来源与许可记录 | — |

### 2.2 Schema（`SEPTEBBS.json`，JSON 数组，每元素一个耀斑，15 字段）

| 字段 | 含义（论文 12 特征映射） |
|---|---|
| `Start_time` / `End_time` | 耀斑起止时间（UTC；注意是耀斑时间，非 SEP 时间） |
| `MinDur` | 耀斑持续时间（分钟） |
| `Tmax` | 等离子体温度峰值（MK）→ 特征 Tmax |
| `EMmax` | 发射度量峰值 → 特征 EMmax |
| `PrecisePeak` | 背景扣除后 1–8 Å 峰值流量 → 特征 SXRmax |
| `StartToTmax` / `TmaxToEnd` | Tmax 峰值相对起/止时间 → 特征 |
| `StartToEMmax` / `EMmaxToEnd` | EMmax 峰值相对起/止时间 → 特征 |
| `StartToPeak` / `PeakToEnd` | SXRmax 峰值相对起/止时间 → 特征 |
| `XCtr` / `YCtr` | 宿主耀斑日面 X/Y 坐标 → 特征 |
| `CausedSPE` | 标签：该耀斑是否关联 SEP 事件（True/False，>10 MeV 质子峰值 ≥10 pfu，NOAA SEP 清单） |

（`MinDur` + `Tmax` + `EMmax` + `PrecisePeak` + 6 个时间偏移 + `XCtr`/`YCtr` = 论文 12 特征。）

### 2.3 来源与许可

- 来源：SEP Prediction Portal（SEP³，https://sun.njit.edu/SEP3/datasets.html，第 5 节 "Data set of TEBBS properties of soft X-ray solar flares and associated SEPs"），作者团队（Sadykov 等）公开数据集；下载日期 2026-08-13。
- 底层数据：GOES 卫星 SXR（0.5–4 Å、1–8 Å）经 TEBBS 算法（Ryan et al. 2012；Sadykov et al. 2017）处理；SEP 标签来自 NOAA Space Environment Services Center 太阳质子事件清单（>10 MeV，>10 pfu）。
- 许可：门户公开下载，页面未附明确许可证；学术开放数据，使用时注明出处（O'Keefe et al. 2024；Sadykov et al. 2017；SEP³ 门户）。
- 完整性：SHA-256 固定于 `MANIFEST.tsv`（2026-08-13）。

### 2.4 冻结数据与论文使用版本的差异（必须说明）

- 论文 §2：使用 2002–2017 耀斑 **18,311 条**、SEP **64 条**（12 特征），排除 TEBBS 失败样本（Tmax≥100 MK 或负时间差）与无宿主坐标的 SEP 关联。
- 冻结 `SEPTEBBS.json`：**24,797 行**（2002-01-01 ~ 2018-02-26），**76 个 CausedSPE=True**；应用论文排除准则（Tmax<100 且时间偏移非负）后为 **24,570 行 / 74 SEP** —— 门户数据集较论文版本已扩充（新增耀斑与 SEP 记录）。
- 因此：**相对对比（RH v2 ≥ CoNN、集成离散度更低）为主锚；绝对 TSS/HSS 值与论文对比时须说明数据版本差异**（预期偏差 ≤ ±0.05 视为口径一致）。

## 3. 实验要求

### 3.1 数据清洗（必须报告）

- 应用论文排除准则：`Tmax < 100`（MK）且 6 个时间偏移字段与 `MinDur` 均为非负；报告清洗后行数与 SEP 数（对照论文 18,311 / 64 与冻结全量 24,797 / 76）。
- 特征：按 §2.2 映射构建 12 特征矩阵 + 标签列；数值型处理（论文未明确标准化，可自行选择并说明）。

### 3.2 模型复现（论文 §3 规格）

- 网络：输入层=特征数（CoNN/Committee=12；RH v1=ceil(sqrt(12))=4；RH v2=6）；dense 层 10 神经元；dropout 0.2；输出层=二分类。实现建议用 skorch（论文所用），或等价 PyTorch 实现。
- 训练：nepochs=500、α=0.001（CoNN 与 Committee）；RH 按 Eq.1–4 计算特征权重（χ²+互信息增益归一化）并据此做特征降采样与 epoch/学习率提升。
- 集成：Committee/RH 各 10 个估计器；投票/加权方式按论文 §3（RH 按特征权重贡献加权；Committee 等权）。
- 评估：随机 70/30 切分，**≥10 次**（论文 §2 口径）；若采用 50 次（§4/表注口径）亦合规，须注明。报告每次切分的混淆矩阵（TP/TN/FP/FN）与 TSS/HSS/precision/recall/accuracy/ROC AUC，汇总均值±std 与中位数±MAD。

### 3.3 必报指标（`results/metrics.json`）

- 4 种方法的 TSS/HSS 均值±std、中位数±MAD（对齐 Table 1/Table 2 格式）；
- 与论文 Table 2 中位数对比表（含绝对差）；
- 主张判定结论：「成立 / 部分成立 / 不成立」+ 依据：
  1. RH v2 中位 TSS ≥ CoNN 中位 TSS（论文 0.944 vs 0.906）；
  2. 集成（Committee/RH）TSS 离散度（std 或 MAD）< CoNN；
  3. RH v2 平均 ≥ Committee 与 RH v1（TSS 与 HSS）；
  4. HSS 无系统性下降（RH v2 HSS ≥ CoNN HSS，论文 0.168 vs 0.163）。

### 3.4 提交物（对齐 v3 规范）

`submission/run.sh`、`analysis_plan.md`、`results/{metrics,evidence_table,critical_checks,uncertainty}.json`、`figures/`、`report.md`、`provenance/`。

## 4. 数据铁律（必须遵守）

- 只用 `data/` 冻结数据；**禁止模拟/合成耀斑或 SEP 样本**。
- 不得修改冻结文件；以 `MANIFEST.tsv` 的 SHA-256 为准核验。
- 不得引入外部 SEP/耀斑数据集冒充冻结数据（如需补充分析，须显式声明为附加实验且不参与主张判定）。
