# TASK: 太阳耀斑 ML 算法对比与降维敏感性（L2 端到端科研再发现）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- 任务 ID：`2505.03385_solar_flare_ml_compare`
- 层级：L2（RCBench 对齐：input/output/scientific goal 三段式；目标论文隐藏，仅给数据与协议）
- 领域：astro（太阳耀斑预测 / SHARP 磁参数 / 分类）
- 裁判：LLM judge（方向一致性锚 + 证据抽查），判分标准见 `SCORE_RUBRIC.md`（私有）

## 任务描述（三段式）

### Input（给定）

`data/flare_dataset.csv`：**真实太阳活动区耀斑数据集**（Liu et al. 2017 官方数据，NJIT Solar Flaring AR Database，2010-05 ~ 2016-12，共 **845 条**活动区-耀斑记录；来源/许可/checksum 见 `data/SOURCE.md`）。

每行一条记录，列：

| 列 | 含义 |
|---|---|
| `class` | GOES 耀斑级别（如 `X22` 表示 X2.2；首字母 = 主类 B/C/M/X） |
| `retrieval_time` | 13 个 HMI 参数齐备的首个时刻（ISO UTC） |
| `flare_start` | GOES 1-8 Å 耀斑开始时刻 |
| `noaa_ar` | NOAA 活动区编号 |
| `TOTUSJH` … `SHRGT45` | 13 个 SHARP/HMI 磁参数（Liu et al. 2017 Table 1 顺序；单位见论文） |
| `main_class` / `sub_class` | 由 `class` 派生：主类字母 / 数值子类 |

样本分布（与 Liu et al. 2017 一致）：B=128、C=552、M=142、X=23。

### Protocol（必须按此执行）

1. **特征工程**：13 参数 → `StandardScaler` 标准化 → 交互特征 `PolynomialFeatures(degree=2, include_bias=False)`（13 原始 + 13 平方 + 78 两两乘积 = 104 维）→ `PCA(n_components=8)` 与 `PCA(n_components=100)` 两个特征集（记作 8PC 与 100PC）。PCA 在全量 845 条上拟合（一次，固定 random_state=42）。
2. **任务与平衡**：
   - **多分类**：目标 = 主类 B/C/M/X。从 552 条 C 中**无放回**随机抽 142 条，与全部 128 B + 142 M + 23 X 组成 435 条平衡集；重复 R 次（R ≥ 10，论文用 100，报告中声明所用 R）。
   - **二分类**：目标 = B/C（0）vs M/X（1）。无放回抽 165 条 B/C + 165 条 M/X 组成 330 条平衡集；重复 R 次。
   - 每次重复用 `random_state=repeat` 的 `resample`（替换=False）。
3. **评测**：每个平衡集上做 `StratifiedKFold(n_splits=10, shuffle=True, random_state=42)` 外层 CV；每折在训练折内做 `GridSearchCV(cv=3, scoring='accuracy')` 选超参，再在测试折上评估。指标：**accuracy、ROC AUC、F1、PR AUC**（二分类：ROC/PR 用正类概率；多分类：ROC 用 `multi_class='ovr'` 且类别二值化，F1 用 `average='weighted'`，PR AUC 用二值化展平）。每折指标取均值 → 每重复一个数 → 最终对 R 次重复取均值。
4. **超参网格**：
   - Random Forest：`min_samples_split ∈ {8, 10}`，`max_features ∈ {8,9,10,11,12,13}`，`random_state=42`
   - KNN：`n_neighbors ∈ {3,5,7,9}`，`weights ∈ {uniform, distance}`，`metric ∈ {euclidean, manhattan}`
   - XGBoost：`learning_rate ∈ {0.1, 0.9}`，`subsample ∈ {0.01, 1.0}`，`random_state=42`
5. **数据事实核查**（必须先做并报告）：总行数、各类计数、13 参数无缺失；`PolynomialFeatures(degree=2)` 后维度应为 104。

### Output（必须产出）

1. **`method/`**：可运行代码，实现上述协议（特征工程 → 平衡 → 10 折 CV + GridSearch → 指标聚合），3 个算法 × 2 任务 × 2 个降维档全跑。
2. **`results/evidence_table.csv`**：每行 = (algorithm, task, pc_level, metric, value, n_repeats)，全部 3×2×2×4 = 48 个数值；另附 PCA 方差事实（见 Scientific Goal Q0）。
3. **`results/metrics.json`**：上述数值 + 数据事实核查结果 + 结论标签。
4. **`results/figure.svg`/png**：至少一张关键图（如 3 算法 × 2 降维档的指标对比条图，或累计解释方差曲线）。
5. **`report.md`**（≤2 页）：方法、结果、四个科学问题的回答、结论与边界。
6. **`claim.md`**：对每个科学问题的结论标签（`supported` / `partially_supported` / `contradicted` / `inconclusive`）。

### Scientific Goal（要回答的科学问题）

针对「13 个 SHARP 磁参数 + 主成分降维量（8 vs 100 PC）如何影响 RF/KNN/XGBoost 在 B/C/M/X 耀斑分类上的表现」这一主题：

1. **Q0 PCA 方差事实**：在你的特征管道下，累计解释方差达到 95% 需要多少个主成分？97.5% 呢？8 个与 100 个主成分各捕获多少方差？与「8 PC ≈ 95%、100 PC ≈ 97.5%」的说法对照并如实报告差异。
2. **Q1 算法排名**：多分类与二分类下，RF / KNN / XGB 的 accuracy / ROC AUC / PR AUC / F1 排名如何？谁最好、谁最差？
3. **Q2 降维敏感性**：每个算法 × 任务下，8PC → 100PC 性能是提升、下降还是持平？是否存在某个算法在某个任务上因维度过高而**显著退化**？
4. **Q3 你的发现**：基于证据，你支持还是反对「RF 与 XGB 随维度增加而获益、KNN 在高维二分类下显著退化」这类结论？给出四档结论标签并说明证据。

## 数据铁律提醒

- 只用 `data/` 内冻结的真实数据（`flare_dataset.csv` 由官方 `flaringAR_dataset.txt` 确定性派生，SHA-256 固定）；禁止合成/模拟数据；禁止把论文表格数字当作本实验实测。
- 所有数字必须由你的代码从冻结数据重算；裁判会抽查 1–2 个关键数并运行你的代码复核。
- 平衡采样、CV 切分、GridSearch 的随机种子必须记录并可从代码复现；不得让测试折参与任何调参。
- 数据许可见 `data/SOURCE.md`（学术使用 + 引用 Liu et al. 2017）。
