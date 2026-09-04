# 科研任务：TSI-Bench 简单插补基线关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2406.12747_tsibench`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：TSI-Bench: Benchmarking Time Series Imputation（arXiv:2406.12747v2）
- 领域：CS / 时间序列 / 缺失值插补

## 问题（可证伪）

TSI-Bench 在 ETT_h1 数据集、10% 单点缺失（point missingness）设定下报告了 28 种插补算法的 MAE（论文 Table 2）。本任务验证其中关于**简单基线**的关键论断：

1. **论断 C1（简单插补法排序）**：在 ETT_h1 测试集上，简单线性插补（Linear）的 MAE ≈ 0.197（标准化单位），明显优于 LOCF（0.315）、Median（0.71）、Mean（0.737），即排序 Linear < LOCF < Median ≈ Mean。
2. **论断 C2（线性插补的竞争力）**：Linear 插补不仅优于传统基线，还与深度学习方法同量级：论文报告中 SAITS=0.144（最优）、iTransformer=0.263、DLinear=0.227、FiLM=0.583、MRNN=0.789——即"在该数据上深度方法并不全面碾压简单基线"。

请基于冻结数据回答：
- (a) 按你重建的协议（见方向提示）实测 4 种简单基线的测试 MAE，C1 的排序与数值量级是否成立？
- (b) 若把实测 Linear MAE 与论文深度方法数值比较（SAITS/iTransformer 等），C2 是否成立？（注意：深度方法数值来自论文，本任务只实测简单基线；比较时说明口径差异）
- 结论标签（四档之一）：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结，来源见 `data/SOURCE.md`）
  - `ETT-h1.csv`：ETT_h1 原始数据（17,420 行小时记录，7 列：`date, HUFL, HULL, MUFL, MULL, LUFL, LULL, OT`；时间 2016-07-01 → 2018-06-26，无缺失值）
  - `source_manifest.json`：源 URL、许可、SHA-256（固定不可变）
- 来源：ETDataset 官方仓库（Zhou et al. 2021, Informer 论文配套数据），TSI-Bench 论文 Table 4 使用的同一原始数据
- 许可：MIT（ETDataset 仓库）

## 方向提示（非强制步骤，但按此口径才能与论文锚对齐）

1. **时间划分**：train = 2016-07-01 00:00 ≤ t < 2017-09-01；val = 2017-09-01 ≤ t < 2018-02-01；test = t ≥ 2018-02-01（小时级，按论文附录 A.2 的 14/5/5 个月划分）。
2. **标准化**：按特征 z-score，统计量**只用 train 划分**拟合（每个特征一个均值/标准差）。
3. **滑窗**：窗口长度 48（非重叠，尾部不足 48 的丢弃）→ 样本数约为 train 213 / val 76 / test 72（论文 Table 4 报 212/75/71，为已知轻微差异，报告中说明即可）。
4. **缺失模拟（种子协议，你负责确定并报告）**：单点缺失率 10%；掩码在标准化后的窗口上逐窗口生成（如 `rng.random((48,7)) < 0.1`）。
   - **必须包含 seed=42 的掩码运行**（便于与冻结参考协议核对）；另外**至少再选 2 个你自定的种子**（如 43、44），各自独立生成掩码并重复整个流程。
   - 掩码只作用于评估时的"被遮蔽位置"；掩码不参与任何统计量估计。
5. **基线实现**（在标准化后的窗口上）：
   - Mean：缺失位填 train 特征均值；Median：填 train 特征中位数；
   - LOCF：逐特征沿时间前向填充（窗口开头的缺失用后向填充兜底）；
   - Linear：逐特征沿时间线性插值（两端用最近邻/前后值外推）。
6. **指标**：MAE（主）与 MSE，只在**测试集被遮蔽位置**上计算（标准化单位）。对每个基线报告多种子均值±标准差。所有数字必须由你的代码从 `data/ETT-h1.csv` 重算。

## 输出要求（提交物）

1. **`claim.md`**：你检验的论断（C1/C2）、失败条件、四档结论标签、数据支持强度说明（含跨种子稳健性）。
2. **`code/`**：完整可复现脚本（固定种子集合，从 `data/ETT-h1.csv` 读取并重算全部指标）。
3. **`results/evidence_table.csv`**：至少含列 `imputer,seed,mae,mse`（每基线×每种子一行），并可含聚合行（`seed=mean±std`）。
4. **`results/metrics.json`**：各基线每种子 MAE/MSE、多种子均值±标准差、test 窗口数与掩码点总数、train 标准化统计量、结论标签。
5. **`report.md`**：方法（划分/标准化/掩码种子协议/基线定义）、结果、结论、局限（与论文口径差异：掩码种子、窗口数 213 vs 212、Mean/Median 定义差异等；若实测偏离论文数值请解释可能原因）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成/模拟数据替代。
- 标准化统计量只能由 train 拟合；test 不得参与任何统计量估计。
- 掩码种子集合必须固定并写入代码与报告；seed=42 的运行必须包含。若你偏离上述协议，必须显式说明并评估对结论的影响。
- 禁止手工抄写论文数字作为"实测结果"；所有指标必须运行代码得到。深度方法数值（SAITS 0.144 等）为论文引用，只能用于比较讨论，不得标注为你的实测结果。
