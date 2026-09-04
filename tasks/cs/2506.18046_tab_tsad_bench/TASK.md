# 科研任务（L2 端到端科研再发现）：多元时间序列异常检测的多数据集统一评测

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2506.18046_tab_tsad_bench`
- 层级：L2（RCBench 对齐：input/output/scientific goal 三段式；目标论文隐藏，仅给数据与协议）
- 领域：CS / 时间序列异常检测（TSAD）/ 评测方法学

## 任务描述（三段式）

### Input（给定）

- 6 个**真实多变量时间序列异常检测数据集**（含逐点标签），来自公开 TSAD 基准合集 TAB/OpenTS 的官方预处理（详见 `data/SOURCE.md`）：
  - `CalIt2`（加利福尼亚交通流，2 通道）
  - `Daphnet`（帕金森穿戴者冻结步态事件传感器数据，7 个 subject-run 文件）
  - `MSL`（NASA 火星科学实验室遥测，55 通道）
  - `PSM`（eBay 服务器指标池，25 通道）
  - `SKAB`（SKAB 基准，机器人系统，34 个场景文件）
  - `SMAP`（NASA 土壤水分主动被动卫星遥测，25 通道）
- 格式：长表 CSV，列 `date, data, cols`；`cols` 为通道名（`feature_*` 或原始编号），其中含一个 `label` 通道（逐点 0/1，1 = 异常）。解析：按 `cols` 分组还原为 宽表（每通道一列）+ label 列。
- 划分：每个数据文件的前 `train_lens` 行为 train，其余为 test；`train_lens`/`test_lens` 见 `data/DETECT_META.csv`（SMAP 135,183/427,617；MSL 58,317/73,729；PSM 132,481/87,841；CalIt2 2,520/2,520；SKAB 9,405/N；Daphnet N/2N）。val 从 train 末段自行切分（如最后 20%，报告声明）。

### Output（必须产出）

1. **`method/`**：实现并训练 **≥3 个 TSAD 方法**，覆盖 **≥2 个方法家族**（自选，报告中声明家族归属）：
   - 深度学习方法：重建类（自编码器/Transformer 重建）、预测类、对比类、或基于注意力/关联度的方法；
   - 机器学习方法：如孤立森林、LOF、OCSVM、聚类类；
   - 简单/非学习方法：如统计阈值、线性回归/线性单层基线。
2. **`protocols/`**：实现**统一评测协议**：
   - 划分：使用冻结数据的 train/val/test（禁止自行重划）；val 仅用于模型选择/早停；
   - 阈值：在百分比阈值网格 {0.1, 0.5, 1, 2, 3, 5, 10, 15, 20, 25} 上逐方法取最佳（报告所选阈值）；
   - 后处理：对窗口化方法实现**两种后处理**——窗口重叠（overlapping）与窗口不重叠（non-overlapping）——并分别报告指标；
   - 指标：AUC-ROC（主）；可补充 F1 / Aff-F1 / VUS-PR。
3. **`results/`**：`evidence_table.csv`（dataset × method × post-processing × 指标）+ `metrics.json`；报告每数据集每方法的 AUC-ROC（两种后处理）。
4. **`report.md`**：完整科研报告（见 Scientific Goal 的四个问题）。

### Scientific Goal（要回答的科学问题）

针对「多元时间序列异常检测（TSAD）方法对比是否受评测协议（划分方式、阈值选择、后处理窗口）影响，以及统一协议下方法相对表现如何」这一主题，回答：

1. **Q1 统一协议下的方法排名**：在固定划分 + 阈值网格 + 统一后处理下，你实现的各方法家族在 6 个数据集上的 AUC-ROC 排名如何？深度学习方法是否在所有数据集上普遍优于简单/线性方法？是否存在「某些数据集上简单/线性方法反而占优」的反例？
2. **Q2 后处理敏感性**：窗口重叠 vs 不重叠对每个（数据集 × 方法）的 AUC-ROC 影响多大？是否呈现「大多数情况影响很小、少数情况有明显影响」的模式？两种后处理下方法排名的稳定性如何？
3. **Q3 评测设置敏感性**：若改用固定阈值（如 1% 或 5%）而非逐方法最优阈值，方法排名是否改变？划分方式（如 50/50 vs 原始划分）是否会改变结论？
4. **Q4 你的发现**：基于上述证据，你支持还是反对「TSAD 方法对比需要统一评测协议（划分/阈值/后处理），否则结论不可靠」这一论断？给出四档结论标签：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 冻结真实数据（来源/许可/checksum 见 `data/SOURCE.md` 与 `data/source_manifest.json`）。
- 数据来自公开 TSAD 基准合集（TAB/OpenTS 官方预处理），上游为 NASA SMAP/MSL、eBay PSM、SKAB、Caltrans CalIt2、Daphnet 等公开数据；本包仅用于学术研究评测。
- train/test 边界以 `DETECT_META.csv` 为准；禁止从网络下载其他版本数据或重新划分；test 段禁止参与训练、验证、阈值选择与后处理参数选择。

## 数据铁律提醒

- 只用本包冻结数据；禁止合成/模拟数据替代。
- 时间顺序不得打乱；test 段禁止参与训练、验证、阈值选择或任何校准。
- 所有方法必须在**同一测试协议**下比较（同一 test 段、同一阈值网格口径、同一 AUC-ROC 计算）。
- 禁止把任何论文数字当作"本实验实测"；所有指标必须由你的代码从本包数据算出。