# solution.md — 方法说明与结果

**任务**：`2308.13068_mvts_flawed_eval`（L2 科研再发现：多变量时序异常检测的评估协议问题）
**目标论文（隐藏）**：arXiv:2308.13068《Multivariate Time Series Anomaly Detection:
Fancy Algorithms and Flawed Evaluation Methodology》
**本文件**：方法说明 + 核心结果；完整分析见 `report.md`。

---

## 1. 数据与冻结事实（实测）

| 数据集 | train | test | 通道 | 异常点数 | 异常比例 | 异常事件段数 |
|---|---|---|---|---|---|---|
| SWaT | 473,399 | 449,919 | 51 | 54,621 | **12.14 %** | 35 |
| PSM | 132,481 | 87,841 | 25（drop `timestamp_(min)`） | 24,381 | **27.76 %** | 72 |

- 冻结参考值校验：PSM 24,381/87,841 = **27.76 %** ✓；SWaT 12.14 % ✓。
- PSM 训练段 4,195 个 NaN（12 通道）：逐通道非 NaN 均值填充（仅使用训练段统计）。
- 时间序列顺序保持，训练/测试按给定顺序使用，未混洗。

## 2. 检测器（`method/`）

| 方法 | 类别 | 说明 |
|---|---|---|
| **PCA**（主） | simple | z-score 标准化 → PCA（95% 方差）重建 → **逐通道残差标准化**（除以训练段逐通道重建 RMSE）合并 → 5 点滑动平均后处理 |
| **PCA-uniform** | simple | 同上但不做逐通道残差标准化（普通 MSE 重建误差，敏感性对照） |
| **Mahalanobis** | simple | z-score 后到训练质心的平方马氏距离 + 平滑 |
| **GRU-AE**（主） | deep | 窗口 100、GRU 自编码器（encoder 取末隐藏态 → decoder 补零重建，hidden=32），逐窗重建 MSE → 逐点聚合 → 平滑；训练 6 epoch（CPU，全离线）；另报逐通道标准化变体 `GRU-AE-cholstd` 作稳健性 |

- 全部 **只使用训练段**拟合；测试段仅用于最终评估。种子固定（seed=42），全流程可复现。

## 3. 评估协议（`protocols/eval_protocols.py`）

1. **逐点（point-wise）F1**：逐点比较预测/标签。
2. **point-adjust F1**：任意一个真异常事件段内检出 ≥1 点，该段整段计为检出（TP 扩展）。
3. **事件级 F1E（含 FAR 惩罚，辅助）**：`R`=被≥1个预测事件命中的真事件比例；`FAR`=与任何真事件无交集的预测事件数/真事件数；`F1E = 2R(1-FAR)/(R+(1-FAR))`。

**阈值口径（明确声明）**：主口径为 `oracle`（测试段上按最优逐点 F1 选阈值——随目标论文 Table 1 口径）；另报 `train_mean+3std` 与 `train_q99` 两种**只用训练段分数**的固定阈值结果。oracle 是上界口径，已在文中声明。

## 4. 随机猜测基线（`baselines/random_guess.py`）

- 在测试段随机抽 α=1000 点标为异常（另做 α=1% 变体），两种协议下算 F1；**50 次重复**取均值±std，真随机（按 seed 调度可复现）。

## 5. 核心结果（oracle 阈值口径）

### 5.1 Q1 — 随机猜测的可操纵性

| 数据集 | F1pw（mean±std） | F1pa（mean±std） | F1pa − F1pw |
|---|---|---|---|
| SWaT | 0.0044 ± 0.0004 | **0.9472** ± 0.0116 | +0.9428 |
| PSM | 0.0217 ± 0.0011 | **0.9742** ± 0.0036 | +0.9525 |

→ 与论文锚值量级一致（论文 SWaT≈0.95 / PSM≈0.98）。**随机猜测的 F1pa 高于 GRU-AE 自己的 F1pa**（SWaT 0.947>0.848；PSM 0.974>0.592）——不学习任何东西，只用 point-adjust 就能“击败”训练好的深度模型。

### 5.2 Q2 — 简单 vs 复杂（逐点 F1，oracle 阈值）

| 方法（family） | SWaT | PSM |
|---|---|---|
| **PCA**（simple） | **0.7964** | **0.6131** |
| PCA-uniform（simple） | 0.7563 | 0.6255 |
| Mahalanobis（simple） | 0.7563 | 0.6158 |
| **GRU-AE**（deep） | 0.7889 | 0.5257 |
| GRU-AE-cholstd（deep） | 0.7931 | 0.5430 |

→ **简单 PCA ≥ 深度 GRU-AE 在两个数据集上均成立**（SWaT +0.0075；PSM +0.0874）。
注意：我们复现的深度方法（GRU-AE）明显强于论文中的 AT/NCAD（SWaT 0.21 / PSM 0.43 量级），因此差距比论文小，但方向一致。

### 5.3 Q3 — 跨协议

- 同方法点 F1pa − F1pw：PCA SWaT +0.057、PSM +0.027；GRU-AE SWaT +0.059、PSM +0.066（oracle 下温和上浮）。
- 任意固定阈值下上浮更大（PSM PCA-uniform q99：0.468→0.777，+0.31）。
- **真正的协议失真在“对比用于比较方法时”**：逐点协议下随机猜测垫底（0.004 / 0.022），而 point-adjust 协议下随机猜测**超过所有训练方法**（0.947 / 0.974）——只用 point-adjust 排序会得到与事实相反的结论。

### 5.4 Q4 — 结论标签

**`supported`**（支持「评估协议是异常检测领域结论混乱的主要来源」）。
证据：(i) 随机猜测 F1pa≈0.95-0.97，比逐点 F1 高 0.94+，且高于训练好的深度模型在同协议下的 F1；(ii) 逐点口径下简单 PCA 在两数据集都 ≥ 深度方法。局限性：SWaT 上差距小、固定阈值口径下方向反转（见 report.md §6），提示“简单 vs 复杂”的排序对阈值敏感，但“协议可操纵”这一主论断证据充分。

## 6. 复现

```bash
cd agent_solution
python scripts/run_pipeline.py          # 全流程：方法+协议+随机猜测 → results/
python scripts/make_figures.py          # 图表 → figures/
python scripts/verify_frozen_facts.py   # 冻结事实/随机猜测 F1pw 独立复核（B 抽查项）
```

- 运行环境：Python 3.13 / numpy / pandas / scipy / scikit-learn / torch（CPU，~2 分钟总运行，见 `evidence/run_pipeline.log`）。
- 数据位于冻结目录 `data/`（本机解析为 `/mnt/f/dataset/cs/2308.13068_mvts_flawed_eval/`，见 `data/DATA_LOCATION.md`）；若路径不同，修改 `scripts/common.py` 中 `DATA_ROOT`。
- 全部键值存在于 `results/evidence_table.csv` 与 `results/metrics.json`。

## 7. 交付物索引

| 路径 | 内容 |
|---|---|
| `method/` | PCA/Mahalanobis 基线 + GRU 自编码器深度方法 |
| `protocols/` | 逐点 / point-adjust / 事件级 F1E 三种协议 |
| `baselines/` | 随机猜测（α、重复次数、种子可复现） |
| `results/evidence_table.csv` | 数据集 × 方法 × 阈值 × 协议 F1 全表 |
| `results/metrics.json` | 关键指标（含随机猜测 mean±std、冻结事实） |
| `results/predictions/*.npz` | 各方法分数/标签（供复核） |
| `figures/` | 4 张分析图 |
| `evidence/` | data_facts.json、run_pipeline.log |
| `scripts/` | common / run_pipeline / make_figures / verify_frozen_facts |